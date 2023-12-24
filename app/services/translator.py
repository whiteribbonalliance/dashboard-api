"""
MIT License

Copyright (c) 2023 White Ribbon Alliance. Maintainers: Thomas Wood, https://fastdatascience.com, Zairon Jacobs, https://zaironjacobs.com.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""

import base64
import json
import logging
from html import unescape
from typing import Callable

import requests
from deep_replacer import DeepReplacer, key_depth_rules
from google.cloud import translate_v2
from google.oauth2 import service_account

from app import constants, utils
from app.core.settings import get_settings
from app.enums.legacy_campaign_code import LegacyCampaignCode
from app.logginglib import init_custom_logger
from app.services.translations_cache import TranslationsCache
from app.types import TCloudService

settings = get_settings()

logger = logging.getLogger(__name__)
init_custom_logger(logger)

GOOGLE_CLOUD_TRANSLATION_API_MAX_TEXTS_PER_REQUEST = 128
AZURE_TEXT_TRANSLATIONS_API_MAX_CHARACTERS_PER_REQUEST = 50000


class Translator:
    """
    This class is responsible for applying translations, mainly from English to another language.
    If English is target language, then no translation is applied.
    To translate from any other language to English, use the quick_translate_text function.
    """

    def __init__(self, cloud_service: TCloudService, target_language: str = "en"):
        self.__target_language = target_language
        self.__translations_cache = TranslationsCache()

        # Keep the latest generated translation keys per language from extracted texts that have been translated
        self.__latest_generated_keys = {}

        # Extracted texts are texts that were determined to be translated
        self.__extracted_texts = set()
        self.__translations_char_count = 0

        # Cloud service to use (google or azure)
        self.__cloud_service = cloud_service

        # Translations enabled
        self.__translations_enabled = settings.TRANSLATIONS_ENABLED

        # Translation function to use
        if self.__cloud_service == "google":
            self.__request_translation = self.__request_translation_with_google
        elif self.__cloud_service == "azure":
            self.__request_translation = self.__request_translation_with_azure
        else:
            self.__request_translation = self.__request_translation_with_google

    def translate_text(self, text: str, delimiter: str | None = None) -> str:
        """
        Translate text.

        :param text: Text to translate.
        :param delimiter: If a delimiter is given, then the text will be split using the delimiter and each word translated separately and returned as a whole string.
        """

        if not text or self.__target_language == "en":
            return text
        if not isinstance(text, str):
            return text
        if not utils.contains_letters(text):
            return text
        if not self.__translations_enabled:
            return text

        if delimiter:
            return self.__translate_text_delimiter_separated(
                text=text, delimiter=delimiter
            )
        else:
            return self.__translate_text(text=text)

    def quick_translate_text(
        self, text: str, source_language: str, target_language: str
    ) -> str:
        """
        Quick translate text.
        Can translate from any other supported language to English.
        Does not cache translations.
        """

        if not self.__translations_enabled:
            return text

        try:
            translated_texts = self.__request_translation(
                values=[text],
                source_language=source_language,
                target_language=target_language,
            )
        except (Exception,) as e:
            logger.error(f"Error translating {text} to {target_language}. {str(e)}")

            return text

        return translated_texts[0]["output"]

    def extract_text(
        self,
        text: str,
        delimiter: str | None = None,
        add_key_to_latest_generated_keys: bool = False,
    ) -> str:
        """
        Extract text.
        Temporarily store the text in memory to translate later.

        :param text: Text to extract.
        :param delimiter: Separate text by delimiter.
        :param add_key_to_latest_generated_keys: Add key to latest generated keys.
        """

        if not text or self.__target_language == "en":
            return text
        if not isinstance(text, str):
            return text
        if not utils.contains_letters(text):
            return text
        if not self.__translations_enabled:
            return text

        extracted_texts = set()

        # Split by delimiter
        if delimiter:
            split_text = text.split(delimiter)
            for index, word in enumerate(split_text):
                word = word.strip()
                extracted_texts.add(word)
        else:
            extracted_texts.add(text)

        for extracted_text in extracted_texts:
            key = f"{self.__target_language}.{extracted_text}"

            # If text is not in cache, add it to extracted texts set
            if not self.__translations_cache.has(key):
                self.__extracted_texts.add(extracted_text)

            # Text has already been translated
            else:
                if add_key_to_latest_generated_keys:
                    self.__add_latest_generated_key(key)

        return text

    def translate_extracted_texts(
        self,
        count_chars_only: bool = False,
        skip_saving_to_json: bool = False,
        add_key_to_latest_generated_keys: bool = False,
    ):
        """
        Translate extracted texts and save them to translations.json.
        """

        if self.__target_language == "en":
            self.__clear_extracted_texts()
            return
        if not self.__translations_enabled:
            self.__clear_extracted_texts()
            return

        if len(self.__extracted_texts) < 1:
            return

        # Divide extracted_texts into chunks
        if self.__cloud_service == "azure":
            extracted_texts_chunks = utils.divide_list_into_chunks_by_char_count(
                my_list=list(self.__extracted_texts),
                n=AZURE_TEXT_TRANSLATIONS_API_MAX_CHARACTERS_PER_REQUEST,
            )
        elif self.__cloud_service == "google":
            extracted_texts_chunks = utils.divide_list_into_chunks_by_text_count(
                my_list=list(self.__extracted_texts),
                n=GOOGLE_CLOUD_TRANSLATION_API_MAX_TEXTS_PER_REQUEST,
            )
        else:
            extracted_texts_chunks = utils.divide_list_into_chunks_by_text_count(
                my_list=list(self.__extracted_texts),
                n=GOOGLE_CLOUD_TRANSLATION_API_MAX_TEXTS_PER_REQUEST,
            )

        # Skip translation, only count characters instead.
        # 1. Add the key to the TranslationsCache with the value as the text not translated.
        # 2. Increase count of translations_char_count.
        #    This is to be able to count the total amount of chars from texts that can be translated.
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
                    translated_texts = self.__request_translation(
                        values=extracted_texts_chunk,
                        source_language="en",
                        target_language=self.__target_language,
                    )
                except (Exception,) as e:
                    logger.error(
                        f"Error translating texts from extracted_texts_chunk to {self.__target_language}. {str(e)}"
                    )
                    continue

                for translated_text in translated_texts:
                    input_text = translated_text["input"]
                    translated_text = translated_text["output"]
                    key = f"{self.__target_language}.{input_text}"
                    self.__translations_cache.set(key=key, value=translated_text)
                    self.__translations_char_count += len(input_text)

                    if add_key_to_latest_generated_keys:
                        self.__add_latest_generated_key(key)

            if not skip_saving_to_json:
                self.__save_translations()

        self.__clear_extracted_texts()

    def __request_translation_with_google(
        self, values: list[str], source_language: str, target_language: str
    ) -> list[dict[str, str]]:
        """Get translation with Google"""

        credentials = service_account.Credentials.from_service_account_info(
            info=json.loads(base64.b64decode(settings.GOOGLE_CREDENTIALS_JSON)),
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )

        client = translate_v2.Client(credentials=credentials)

        output = client.translate(
            values=values,
            source_language=source_language,
            target_language=target_language,
            format_="text",
        )

        translations = []
        for data in output:
            translations.append(
                {"input": data["input"], "output": unescape(data["translatedText"])}
            )

        return translations

    def __request_translation_with_azure(
        self, values: list[str], source_language: str, target_language: str
    ) -> list[dict[str, str]]:
        """Get translation with Azure"""

        url = "https://api.cognitive.microsofttranslator.com/translate"
        params = {"api-version": "3.0", "from": source_language, "to": target_language}
        headers = {
            "Ocp-Apim-Subscription-Key": settings.AZURE_TRANSLATOR_KEY,
            "Ocp-Apim-Subscription-Region": "eastus",
            "Content-type": "application/json",
        }

        body = [{"text": x} for x in values]

        response = requests.post(url, params=params, headers=headers, json=body)

        if not response.ok:
            raise Exception("Error translating with Azure")

        output = response.json()

        translations = []
        for _input, _output in zip(values, output):
            translations.append(
                {"input": _input, "output": _output["translations"][0]["text"]}
            )

        return translations

    def __save_translations(self):
        """Save translations to translations.json"""

        with open(constants.TRANSLATIONS_JSON, "w") as file:
            file.write(json.dumps(self.__translations_cache.get_all()))

    def __translate_text_delimiter_separated(self, text: str, delimiter: str) -> str:
        """
        Split string into a list of words e.g. "hello, world" -> ["hello", "world"] and translate each word then merge words back together
        """

        if not text or self.__target_language == "en":
            return text
        if not isinstance(text, str):
            return text
        if not utils.contains_letters(text):
            return text

        translated_text = ""
        split_text = text.split(delimiter)
        for index, word in enumerate(split_text):
            word = word.strip()
            translated_text += f"{self.__translate_text(word)}"
            if index < len(split_text) - 1:
                if delimiter == " ":
                    translated_text += f"{delimiter}"
                else:
                    translated_text += f"{delimiter} "

        return translated_text

    def __translate_text(self, text: str) -> str:
        """
        Get translation of text from cache.
        If translation is not in cache, translate the text and add it to cache.
        """

        if not text or self.__target_language == "en":
            return text
        if not isinstance(text, str):
            return text
        if not utils.contains_letters(text):
            return text

        # Create key
        key = f"{self.__target_language}.{text}"

        # If translated text already exists, return it
        if self.__translations_cache.has(key):
            return self.__translations_cache.get(key)

        # If translated text does not exist, translate it, add it to cache, and return it
        else:
            try:
                translated_texts = self.__request_translation(
                    values=[text],
                    source_language="en",
                    target_language=self.__target_language,
                )
            except (Exception,) as e:
                logger.error(
                    f"Error translating {text} to {self.__target_language}. {str(e)}"
                )
                return text

            # Add translation to cache
            self.__translations_cache.set(key, translated_texts[0]["output"])

            return translated_texts[0]["output"]

    def __clear_extracted_texts(self):
        """
        Clear extracted texts.
        """

        self.__extracted_texts.clear()

    def __add_latest_generated_key(self, key: str):
        """
        Add latest generated key.
        """

        if not self.__latest_generated_keys.get(self.__target_language):
            self.__latest_generated_keys[self.__target_language] = []
        self.__latest_generated_keys[self.__target_language].append(key)

    def get_translations_char_count(self) -> int:
        """Get translations char count"""

        return self.__translations_char_count

    def set_target_language(self, target_language: str):
        """Set target language"""

        self.__target_language = target_language

    def get_latest_generated_keys(self) -> dict:
        """Get latest generated keys"""

        return self.__latest_generated_keys

    #
    # The following functions are used for translating campaign data.
    #

    def apply_t_function_campaign(
        self,
        t: Callable,
        campaign_code: str,
        language: str,
        current_question: dict,
        all_questions: list,
        responses_sample: dict,
        responses_breakdown: dict,
        living_settings_breakdown: list,
        top_words_and_phrases: dict,
        histogram: dict,
        genders_breakdown: list,
        world_bubble_maps_coordinates: dict,
        filter_1_average_age: str,
        filter_2_average_age: str,
        filter_1_description: str,
        filter_2_description: str,
    ) -> dict:
        """
        Apply extract/translate.

        If the data structure of any argument has changed (except t, campaign_code and language), make sure
        key_depth_rules is updated.
        """

        # Create deep replacer instance
        deep_replacer = DeepReplacer()

        # Responses sample
        # giz: Do not translate response if the language is es
        # giz: For other languages, only translate text between parenthesis
        if campaign_code == LegacyCampaignCode.giz.value:
            if language != "es":
                responses_sample = deep_replacer.replace(
                    data=responses_sample,
                    replace_func=t,
                    pydantic_to_dict=True,
                    key_depth_rules={
                        "columns:id": [key_depth_rules.IGNORE],
                        "columns:type": [key_depth_rules.IGNORE],
                        "data:response": [
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

        # Current question
        current_question = deep_replacer.replace(
            data=current_question,
            replace_func=t,
            pydantic_to_dict=True,
            key_depth_rules={
                "code": [key_depth_rules.IGNORE],
            },
        )

        # question
        all_questions = deep_replacer.replace(
            data=all_questions,
            replace_func=t,
            pydantic_to_dict=True,
            key_depth_rules={
                "code": [key_depth_rules.IGNORE],
            },
        )

        # Responses breakdown
        responses_breakdown = deep_replacer.replace(
            data=responses_breakdown,
            replace_func=t,
            pydantic_to_dict=True,
            key_depth_rules={
                "parent_categories:value": [key_depth_rules.IGNORE],
                "sub_categories:value": [key_depth_rules.IGNORE],
                "parent_or_sub_categories:value": [key_depth_rules.IGNORE],
            },
        )

        # Living settings
        living_settings_breakdown = deep_replacer.replace(
            data=living_settings_breakdown,
            replace_func=t,
            pydantic_to_dict=True,
            key_depth_rules={
                "value": [key_depth_rules.IGNORE],
            },
        )

        # Top words and phrases
        top_words_and_phrases = deep_replacer.replace(
            data=top_words_and_phrases,
            replace_func=t,
            pydantic_to_dict=True,
            key_depth_rules={
                "top_words:value": [key_depth_rules.IGNORE],
                "two_word_phrases:value": [key_depth_rules.IGNORE],
                "three_word_phrases:value": [key_depth_rules.IGNORE],
                "wordcloud_words:value": [key_depth_rules.IGNORE],
            },
        )

        # Top words and phrases (lower)
        for key, value in top_words_and_phrases.items():
            for word in value:
                if word.get("label"):
                    word["label"] = word["label"].lower()
                elif word.get("text"):
                    word["text"] = word["text"].lower()

        # Histogram
        histogram = deep_replacer.replace(
            data=histogram,
            replace_func=t,
            pydantic_to_dict=True,
            key_depth_rules={
                "ages:label": [key_depth_rules.IGNORE_STR_WITHOUT_LETTERS],
                "age_buckets:label": [key_depth_rules.IGNORE_STR_WITHOUT_LETTERS],
                "ages:value": [key_depth_rules.IGNORE],
                "ages_buckets:value": [key_depth_rules.IGNORE],
                "ages_buckets_default:value": [key_depth_rules.IGNORE],
                "genders:value": [key_depth_rules.IGNORE],
                "professions:value": [key_depth_rules.IGNORE],
                "canonical_countries:value": [key_depth_rules.IGNORE],
            },
        )

        # Genders breakdown
        genders_breakdown = deep_replacer.replace(
            data=genders_breakdown,
            replace_func=t,
            pydantic_to_dict=True,
            key_depth_rules={
                "value": [key_depth_rules.IGNORE],
            },
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

        return {
            "current_question": current_question,
            "all_questions": all_questions,
            "responses_sample": responses_sample,
            "responses_breakdown": responses_breakdown,
            "living_settings_breakdown": living_settings_breakdown,
            "top_words_and_phrases": top_words_and_phrases,
            "histogram": histogram,
            "genders_breakdown": genders_breakdown,
            "world_bubble_maps_coordinates": world_bubble_maps_coordinates,
            "filter_1_average_age": filter_1_average_age,
            "filter_2_average_age": filter_2_average_age,
            "filter_1_description": filter_1_description,
            "filter_2_description": filter_2_description,
        }

    def apply_t_histogram_options(self, t: Callable, options: list[dict]) -> dict:
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

        return {"options": options}

    def apply_t_filter_options(
        self,
        t: Callable,
        country_options: list[dict],
        country_region_options: list[dict[str, str | list[dict]]],
        country_province_options: list[dict[str, str | list[dict]]],
        response_topic_options: list[dict],
        age_options: list[dict],
        age_bucket_options: list[dict],
        age_bucket_default_options: list[dict],
        gender_options: list[dict],
        living_setting_options: list[dict],
        profession_options: list[dict],
        only_responses_from_categories_options: list[dict],
        only_multi_word_phrases_containing_filter_term_options: list[dict],
    ) -> dict:
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
        country_region_options = deep_replacer.replace(
            data=country_region_options,
            replace_func=t,
            pydantic_to_dict=True,
            key_depth_rules={
                "country_alpha2_code": [key_depth_rules.IGNORE],
                "options:value": [key_depth_rules.IGNORE],
                "options:metadata": [key_depth_rules.IGNORE],
            },
        )

        # Country provinces options
        country_province_options = deep_replacer.replace(
            data=country_province_options,
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

        # Age bucket options
        age_bucket_options = deep_replacer.replace(
            data=age_bucket_options,
            replace_func=t,
            pydantic_to_dict=True,
            key_depth_rules={
                "value": [key_depth_rules.IGNORE],
                "metadata": [key_depth_rules.IGNORE],
            },
        )

        # Age bucket default options
        age_bucket_default_options = deep_replacer.replace(
            data=age_bucket_default_options,
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

        # Living setting options
        living_setting_options = deep_replacer.replace(
            data=living_setting_options,
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

        return {
            "country_options": country_options,
            "country_region_options": country_region_options,
            "country_province_options": country_province_options,
            "response_topic_options": response_topic_options,
            "age_options": age_options,
            "age_bucket_options": age_bucket_options,
            "age_bucket_default_options": age_bucket_default_options,
            "gender_options": gender_options,
            "living_setting_options": living_setting_options,
            "profession_options": profession_options,
            "only_responses_from_categories_options": only_responses_from_categories_options,
            "only_multi_word_phrases_containing_filter_term_options": only_multi_word_phrases_containing_filter_term_options,
        }
