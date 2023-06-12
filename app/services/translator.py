from html import unescape

from google.api_core.exceptions import BadRequest
from google.cloud import translate_v2
from google.oauth2 import service_account

from app.services.translations_cache import TranslationsCache


class Translator:
    """
    This class is responsible for applying translations
    """

    def __init__(self, language):
        self.__language = language
        self.__translations_cache = TranslationsCache.get_instance()

    def __get_translate_client(self) -> translate_v2.Client:
        """Get Translate client"""

        credentials = service_account.Credentials.from_service_account_file(
            filename="credentials.json",
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )

        return translate_v2.Client(credentials=credentials)

    def translate(self, text: str, test_mode: bool = False) -> str:
        """
        Get translation of text from cache
        If not in cache, translate the text with Cloud Translate and add it to cache
        """

        if not text:
            return text

        if test_mode:
            return f"t_{text}"

        translate_client = self.__get_translate_client()

        key = f"{self.__language}.{text}"
        if self.__translations_cache.has(key):
            # If translated text already exists, return it
            return self.__translations_cache.get(key)
        else:
            # If translated text does not exist, translate it and add it to cache
            # English will not be translated
            if self.__language == "en":
                translated_text = text
            else:
                try:
                    output = translate_client.translate(
                        values=text,
                        source_language="en",
                        target_language=self.__language,
                    )
                    translated_text = unescape(output["translatedText"])
                except (BadRequest, KeyError):
                    return text

            # Add translation to cache
            self.__translations_cache.set(key, translated_text)

            return translated_text
