import json
import os
from typing import Any

TRANSLATIONS_JSON_FILE_NAME = "translations.json"


class TranslationsCache:
    """This class is responsible for caching translations"""

    __instance = None

    @staticmethod
    def get_instance() -> "TranslationsCache":
        if TranslationsCache.__instance is None:
            TranslationsCache()

        return TranslationsCache.__instance

    def __init__(self):
        self.__cache = {}
        TranslationsCache.__instance = self

        # Load translations from translations.json
        self.load_cache()

        # Start the instance
        self.get_instance()

    def load_cache(self):
        """Load content of translations.json into cache"""

        if os.path.isfile(TRANSLATIONS_JSON_FILE_NAME):
            with open(TRANSLATIONS_JSON_FILE_NAME, "r") as file:
                self.__cache = json.loads(file.read())

    def set(self, key: str, value: Any):
        """Set key value pair"""

        self.__cache[key] = value

    def get(self, key: str):
        """Get value by key"""

        return self.__cache.get(key)

    def has(self, key: str):
        """Check if key is in cache"""

        return key in self.__cache

    def all(self):
        """Get the whole cache"""

        return self.__cache
