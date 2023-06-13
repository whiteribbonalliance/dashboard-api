import json
import os
from typing import Any

from app import constants


class TranslationsCache:
    """This class is responsible for caching translations"""

    __instance = None

    @staticmethod
    def get_instance() -> "TranslationsCache":
        """
        Only use this function to get the instance e.g. 'TranslationsCache.get_instance()'
        """

        if TranslationsCache.__instance is None:
            TranslationsCache()

        return TranslationsCache.__instance

    def __init__(self):
        TranslationsCache.__instance = self

        self.__cache = {}

        self.__load()

    def __load(self):
        """Load content of translations.json into cache"""

        if os.path.isfile(constants.TRANSLATIONS_JSON_FILE_NAME):
            with open(constants.TRANSLATIONS_JSON_FILE_NAME, "r") as file:
                self.__cache = json.loads(file.read())

    def set(self, key: str, value: Any):
        """Set key value pair"""

        self.__cache[key] = value

    def get(self, key: str) -> str:
        """Get value by key"""

        return self.__cache.get(key)

    def has(self, key: str) -> bool:
        """Check if key is in cache"""

        return key in self.__cache

    def get_all(self) -> dict:
        """Get the whole cache"""

        return self.__cache
