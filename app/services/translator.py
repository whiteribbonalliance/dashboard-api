import json
import logging
from html import unescape

from google.cloud import translate_v2
from google.oauth2 import service_account

from app import constants
from app.core.settings import settings
from app.logginglib import init_custom_logger
from app.services.translations_cache import TranslationsCache
from app.utils import helpers
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
        self.__language = "en"
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

    def __translate_text(self, text: str) -> str:
        """
        Get translation of text from cache
        If not in cache, translate the text with Cloud Translate and add it to cache

        This function will only be used to translate texts on the fly
        When OFFLINE_TRANSLATE_MODE = True, texts will be extracted only
        """

        if not text or self.__language == "en":
            return text

        # With OFFLINE_TRANSLATE_MODE = True, save the text to extracted_texts only
        if settings.OFFLINE_TRANSLATE_MODE:
            self.add_text_to_extract(text=text)

            return text

        key = f"{self.__language}.{text}"

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
                    target_language=self.__language,
                )
                translated_text = unescape(output["translatedText"])
            except (Exception,):
                logger.error(f"Error translating: {text} to {self.__language}")
                return text

            # Add translation to cache
            self.__translations_cache.set(key, translated_text)

            return translated_text

    def __translate_text_delimiter_separated(self, text: str, delimiter: str) -> str:
        """
        Split string into a list of words e.g. "hello, world" -> ["hello", "world"]
        Translate each word
        Merge words back together
        """

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

    def translate_text(self, text: str, delimiter: str | None = None) -> str:
        """
        Translate text

        :param text: Text to translate
        :param delimiter: If a delimiter is given, then the text will be split using the delimiter and each word
        translated separately and returned as a whole string
        """

        if delimiter:
            return self.__translate_text_delimiter_separated(
                text=text, delimiter=delimiter
            )
        else:
            return self.__translate_text(text=text)

    def add_text_to_extract(self, text: str):
        """
        Add text to extract

        :param text: Text to extract
        """

        if not text or self.__language == "en":
            return

        # If text is not in translations.json, add it to a set of texts to be translated
        key = f"{self.__language}.{text}"
        if not self.__translations_cache.has(key):
            self.__extracted_texts.add(text)
        else:
            # Texts has already been translated
            self.__add_key_to_latest_generated_keys(key)

    def __clear_extracted_texts(self):
        """Clear extracted texts"""

        self.__extracted_texts.clear()

    def __add_key_to_latest_generated_keys(self, key: str):
        """Add key to latest generated keys"""

        if not self.__latest_generated_keys_per_language.get(self.__language):
            self.__latest_generated_keys_per_language[self.__language] = []
        self.__latest_generated_keys_per_language[self.__language].append(key)

    def translate_extracted_texts(
        self, count_chars_only: bool = False, skip_saving_to_json: bool = False
    ):
        """Translate extracted texts and save them to translations.json"""

        if len(self.__extracted_texts) < 1 or self.__language == "en":
            self.__clear_extracted_texts()
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
                    key = f"{self.__language}.{text}"
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
                        target_language=self.__language,
                    )
                except (Exception,):
                    logger.error(
                        f"Error translating: extracted_texts_chunk to {self.__language}"
                    )
                    continue

                for data in output:
                    input_text = data["input"]
                    translated_text = unescape(data["translatedText"])
                    key = f"{self.__language}.{input_text}"
                    self.__translations_cache.set(key=key, value=translated_text)
                    self.__translations_char_count += len(input_text)
                    self.__add_key_to_latest_generated_keys(key)

            if not skip_saving_to_json:
                self.__save_translations()

        self.__clear_extracted_texts()

    def __save_translations(self):
        """Save translations to translations.json"""

        with open(constants.TRANSLATIONS_JSON_FILE_NAME, "w") as file:
            file.write(json.dumps(self.__translations_cache.get_all()))

    def get_translations_char_count(self) -> int:
        """Get translations char count"""

        return self.__translations_char_count

    def set_language(self, language: str):
        """Set language"""

        self.__language = language

    def get_latest_generated_keys_per_language(self) -> dict:
        """Get latest generated keys per language"""

        return self.__latest_generated_keys_per_language
