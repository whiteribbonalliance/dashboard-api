import json
import os
from typing import Any

from app import constants
from app.utils.singleton_meta import SingletonMeta


class TranslationsCache(metaclass=SingletonMeta):
    """
    This class is responsible for caching translations (Singleton class)
    """

    def __init__(self):
        self.__cache = {}

        self.__is_loaded = False

    def load(self):
        """Load content of translations.json into cache"""

        if not self.__cache:
            if os.path.isfile(constants.TRANSLATIONS_JSON):
                with open(constants.TRANSLATIONS_JSON, "r", encoding="utf-8") as file:
                    self.__cache: dict = json.loads(file.read())
                    self.__is_loaded = True

    def is_loaded(self) -> bool:
        """Is loaded"""

        return self.__is_loaded

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
