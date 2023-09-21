import json
import logging
from html import unescape
from typing import Callable

from deep_replacer import DeepReplacer, key_depth_rules
from google.cloud import translate_v2
from google.oauth2 import service_account

from app import constants, helpers
from app.enums.campaign_code import CampaignCode
from app.logginglib import init_custom_logger
from app.schemas.option import Option
from app.services.translations_cache import TranslationsCache
from app.utils.singleton_meta import SingletonMeta

logger = logging.getLogger(__name__)
init_custom_logger(logger)

CLOUD_TRANSLATION_API_MAX_MESSAGES_PER_REQUEST = 128


class Translator(metaclass=SingletonMeta):
    """
    Singleton class
    This class is responsible for applying translations
    """

    def __init__(self):
        self.__target_language = "en"
        self.__translations_cache = TranslationsCache()

        # Keep the latest generated keys per language from extracted texts that have been translated
        self.__latest_generated_keys_per_language = {}

        # Extracted texts are texts that were determined to be translated
        self.__extracted_texts = set()
        self.__translations_char_count = 0

    def __get_translate_client(self) -> translate_v2.Client:
        """Get Translate client"""

        credentials = service_account.Credentials.from_service_account_file(
            filename="credentials.json",
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )

        return translate_v2.Client(credentials=credentials)

    def __save_translations(self):
        """Save translations to translations.json"""

        with open(constants.TRANSLATIONS_JSON, "w") as file:
            file.write(json.dumps(self.__translations_cache.get_all()))

    def __translate_text_delimiter_separated(self, text: str, delimiter: str) -> str:
        """
        Split string into a list of words e.g. "hello, world" -> ["hello", "world"]
        Translate each word
        Merge words back together
        """

        # Conditions
        if not text or self.__target_language == "en":
            return text
        if not isinstance(text, str):
            return text
        if not helpers.contains_letters(text):
            return text

        translated_text = ""

        split_text = text.split(delimiter)

        for index, word in enumerate(split_text):
            word = word.strip()
            translated_text += f"{self.translate_text(word)}"
            if index < len(split_text) - 1:
                if delimiter == " ":
                    translated_text += f"{delimiter}"
                else:
                    translated_text += f"{delimiter} "

        return translated_text

    def __translate_text(self, text: str) -> str:
        """
        Get translation of text from cache.
        If not in cache, translate the text with Cloud Translate and add it to cache.
        This function will only be used to translate texts on the fly.
        """

        # Conditions
        if not text or self.__target_language == "en":
            return text
        if not isinstance(text, str):
            return text
        if not helpers.contains_letters(text):
            return text

        key = f"{self.__target_language}.{text}"

        if self.__translations_cache.has(key):
            # If translated text already exists, return it
            return self.__translations_cache.get(key)
        else:
            # If translated text does not exist, translate it and add it to cache
            try:
                translate_client = self.__get_translate_client()
                output = translate_client.translate(
                    values=text,
                    source_language="en",
                    target_language=self.__target_language,
                )
                translated_text = unescape(output["translatedText"])
            except (Exception,):
                logger.error(f"Error translating: {text} to {self.__target_language}")
                return text

            # Add translation to cache
            self.__translations_cache.set(key, translated_text)

            return translated_text

    def translate_text(self, text: str, delimiter: str | None = None) -> str:
        """
        Translate text

        :param text: Text to translate
        :param delimiter: If a delimiter is given, then the text will be split using the delimiter and each word
        translated separately and returned as a whole string
        """

        # Conditions
        if not text or self.__target_language == "en":
            return text
        if not isinstance(text, str):
            return text
        if not helpers.contains_letters(text):
            return text

        if delimiter:
            return self.__translate_text_delimiter_separated(
                text=text, delimiter=delimiter
            )
        else:
            return self.__translate_text(text=text)

    def extract_text(self, text: str, delimiter: str | None = None) -> str:
        """
        Extract text.

        :param text: Text to extract
        :param delimiter: Separate text by delimiter and add to texts to extract set
        """

        # Conditions
        if not text or self.__target_language == "en":
            return text
        if not isinstance(text, str):
            return text
        if not helpers.contains_letters(text):
            return text

        extracted_texts = set()

        if delimiter:
            split_text = text.split(delimiter)
            for index, word in enumerate(split_text):
                word = word.strip()
                extracted_texts.add(word)
        else:
            extracted_texts.add(text)

        # If text is not in translations.json, add it to extracted texts set
        for extracted_text in extracted_texts:
            key = f"{self.__target_language}.{extracted_text}"
            if not self.__translations_cache.has(key):
                self.__extracted_texts.add(extracted_text)
            else:
                # Text has already been translated
                self.__add_key_to_latest_generated_keys(key)

        return text

    def __clear_extracted_texts(self):
        """Clear extracted texts"""

        self.__extracted_texts.clear()

    def __add_key_to_latest_generated_keys(self, key: str):
        """Add key to latest generated keys"""

        if not self.__latest_generated_keys_per_language.get(self.__target_language):
            self.__latest_generated_keys_per_language[self.__target_language] = []
        self.__latest_generated_keys_per_language[self.__target_language].append(key)

    def translate_extracted_texts(
        self, count_chars_only: bool = False, skip_saving_to_json: bool = False
    ):
        """Translate extracted texts and save them to translations.json"""

        if self.__target_language == "en":
            self.__clear_extracted_texts()
            return

        if len(self.__extracted_texts) < 1:
            return

        # Divide extracted_texts into chunks
        extracted_texts_chunks = helpers.divide_list_into_chunks(
            my_list=list(self.__extracted_texts),
            n=CLOUD_TRANSLATION_API_MAX_MESSAGES_PER_REQUEST,
        )

        # Skip translation, count characters instead
        # 1. Add the key to the TranslationsCache with the value as the text not translated
        # 2. Increase count of translations_char_count
        #    This is to be able to count the total amount of chars from texts that can be translated
        if count_chars_only:
            for extracted_texts_chunk in extracted_texts_chunks:
                for text in extracted_texts_chunk:
                    key = f"{self.__target_language}.{text}"
                    self.__translations_cache.set(key=key, value=text)
                    self.__translations_char_count += len(text)

        # Apply translation
        else:
            for extracted_texts_chunk in extracted_texts_chunks:
                try:
                    translate_client = self.__get_translate_client()
                    output = translate_client.translate(
                        values=extracted_texts_chunk,
                        source_language="en",
                        target_language=self.__target_language,
                    )
                except (Exception,):
                    logger.error(
                        f"Error translating: extracted_texts_chunk to {self.__target_language}"
                    )
                    continue

                for data in output:
                    input_text = data["input"]
                    translated_text = unescape(data["translatedText"])
                    key = f"{self.__target_language}.{input_text}"
                    self.__translations_cache.set(key=key, value=translated_text)
                    self.__translations_char_count += len(input_text)
                    self.__add_key_to_latest_generated_keys(key)

            if not skip_saving_to_json:
                self.__save_translations()

        self.__clear_extracted_texts()

    def get_translations_char_count(self) -> int:
        """Get translations char count"""

        return self.__translations_char_count

    def set_target_language(self, target_language: str):
        """Set target language"""

        self.__target_language = target_language

    def get_latest_generated_keys_per_language(self) -> dict:
        """Get latest generated keys per language"""

        return self.__latest_generated_keys_per_language

    def apply_t_function_campaign(
        self,
        t: Callable,
        campaign_code: CampaignCode,
        language: str,
        responses_sample: dict,
        responses_breakdown: list,
        living_settings_breakdown: list,
        top_words_and_phrases: dict,
        histogram: dict,
        genders_breakdown: list,
        world_bubble_maps_coordinates: dict,
        filter_1_average_age: str,
        filter_2_average_age: str,
        filter_1_description: str,
        filter_2_description: str,
    ):
        """Apply extract/translate"""

        # Create deep replacer instance
        deep_replacer = DeepReplacer()

        # Responses sample
        # economic_empowerment_mexico: Do not translate 'raw_response' if the language is 'es'
        # economic_empowerment_mexico: For other languages, only translate text between parenthesis
        if campaign_code == CampaignCode.economic_empowerment_mexico:
            if language != "es":
                responses_sample = deep_replacer.replace(
                    data=responses_sample,
                    replace_func=t,
                    pydantic_to_dict=True,
                    key_depth_rules={
                        "columns:id": [key_depth_rules.IGNORE],
                        "columns:type": [key_depth_rules.IGNORE],
                        "data:raw_response": [
                            key_depth_rules.APPLY_ON_TEXT_BETWEEN_PARENTHESIS
                        ],
                    },
                )
        else:
            responses_sample = deep_replacer.replace(
                data=responses_sample,
                replace_func=t,
                pydantic_to_dict=True,
                key_depth_rules={
                    "columns:id": [key_depth_rules.IGNORE],
                    "columns:type": [key_depth_rules.IGNORE],
                },
            )

        # Responses breakdown
        responses_breakdown = deep_replacer.replace(
            data=responses_breakdown,
            replace_func=t,
            pydantic_to_dict=True,
            key_depth_rules={"code": ["ignore"]},
        )

        # Living settings
        living_settings_breakdown = deep_replacer.replace(
            data=living_settings_breakdown,
            replace_func=t,
            pydantic_to_dict=True,
        )

        # Top words and phrases
        top_words_and_phrases = deep_replacer.replace(
            data=top_words_and_phrases,
            replace_func=t,
            pydantic_to_dict=True,
        )

        # Histogram
        histogram = deep_replacer.replace(
            data=histogram,
            replace_func=t,
            pydantic_to_dict=True,
            key_depth_rules={
                "ages": [key_depth_rules.IGNORE_STR_WITHOUT_LETTERS],
                "age_ranges": [key_depth_rules.IGNORE_STR_WITHOUT_LETTERS],
            },
        )

        # Genders breakdown
        genders_breakdown = deep_replacer.replace(
            data=genders_breakdown,
            replace_func=t,
            pydantic_to_dict=True,
        )

        # World bubble maps coordinates
        world_bubble_maps_coordinates = deep_replacer.replace(
            data=world_bubble_maps_coordinates,
            replace_func=t,
            pydantic_to_dict=True,
            key_depth_rules={
                "coordinates_1:location_code": [key_depth_rules.IGNORE],
                "coordinates_2:location_code": [key_depth_rules.IGNORE],
            },
        )

        filter_1_average_age = t(text=filter_1_average_age)
        filter_2_average_age = t(text=filter_2_average_age)
        filter_1_description = t(text=filter_1_description)
        filter_2_description = t(text=filter_2_description)

        return (
            responses_sample,
            responses_breakdown,
            living_settings_breakdown,
            top_words_and_phrases,
            histogram,
            genders_breakdown,
            world_bubble_maps_coordinates,
            filter_1_average_age,
            filter_2_average_age,
            filter_1_description,
            filter_2_description,
        )

    def apply_t_who_the_people_are_options(self, t: Callable, options: list[Option]):
        """Apply extract/translate"""

        # Create deep replacer instance
        deep_replacer = DeepReplacer()

        # Options
        options = deep_replacer.replace(
            data=options,
            replace_func=t,
            pydantic_to_dict=True,
            key_depth_rules={
                "value": [key_depth_rules.IGNORE],
                "metadata": [key_depth_rules.IGNORE],
            },
        )

        return options

    def apply_t_filter_options(
        self,
        t: Callable,
        country_options: list[dict],
        country_regions_options: list[dict[str, str | list[dict]]],
        response_topic_options: list[dict],
        age_options: list[dict],
        gender_options: list[dict],
        profession_options: list[dict],
        only_responses_from_categories_options: list[dict],
        only_multi_word_phrases_containing_filter_term_options: list[dict],
    ):
        """Apply extract/translate"""

        # Create deep replacer instance
        deep_replacer = DeepReplacer()

        # Country options
        country_options = deep_replacer.replace(
            data=country_options,
            replace_func=t,
            pydantic_to_dict=True,
            key_depth_rules={
                "value": [key_depth_rules.IGNORE],
                "metadata": [key_depth_rules.IGNORE],
            },
        )

        # Country regions options
        country_regions_options = deep_replacer.replace(
            data=country_regions_options,
            replace_func=t,
            pydantic_to_dict=True,
            key_depth_rules={
                "country_alpha2_code": [key_depth_rules.IGNORE],
                "options:value": [key_depth_rules.IGNORE],
                "options:metadata": [key_depth_rules.IGNORE],
            },
        )

        # Response topic options
        response_topic_options = deep_replacer.replace(
            data=response_topic_options,
            replace_func=t,
            pydantic_to_dict=True,
            key_depth_rules={
                "value": [key_depth_rules.IGNORE],
                "metadata": [key_depth_rules.IGNORE],
            },
        )

        # Age options
        age_options = deep_replacer.replace(
            data=age_options,
            replace_func=t,
            pydantic_to_dict=True,
            key_depth_rules={
                "value": [key_depth_rules.IGNORE],
                "metadata": [key_depth_rules.IGNORE],
            },
        )

        # Gender options
        gender_options = deep_replacer.replace(
            data=gender_options,
            replace_func=t,
            pydantic_to_dict=True,
            key_depth_rules={
                "value": [key_depth_rules.IGNORE],
                "metadata": [key_depth_rules.IGNORE],
            },
        )

        # Profession options
        profession_options = deep_replacer.replace(
            data=profession_options,
            replace_func=t,
            pydantic_to_dict=True,
            key_depth_rules={
                "value": [key_depth_rules.IGNORE],
                "metadata": [key_depth_rules.IGNORE],
            },
        )

        # Only responses from categories options
        only_responses_from_categories_options = deep_replacer.replace(
            data=only_responses_from_categories_options,
            replace_func=t,
            pydantic_to_dict=True,
            key_depth_rules={
                "value": [key_depth_rules.IGNORE],
                "metadata": [key_depth_rules.IGNORE],
            },
        )

        # Only multi-word phrases containing filter term options
        only_multi_word_phrases_containing_filter_term_options = deep_replacer.replace(
            data=only_multi_word_phrases_containing_filter_term_options,
            replace_func=t,
            pydantic_to_dict=True,
            key_depth_rules={
                "value": [key_depth_rules.IGNORE],
                "metadata": [key_depth_rules.IGNORE],
            },
        )

        return (
            country_options,
            country_regions_options,
            response_topic_options,
            age_options,
            gender_options,
            profession_options,
            only_responses_from_categories_options,
            only_multi_word_phrases_containing_filter_term_options,
        )
