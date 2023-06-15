import json
import os
from typing import Any

from app import constants
from app.utils.singleton_meta import SingletonMeta


class TranslationsCache(metaclass=SingletonMeta):
    """
    Singleton class
    This class is responsible for caching translations
    """

    def __init__(self):
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
