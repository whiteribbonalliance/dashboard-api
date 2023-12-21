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

import json
import os
from typing import Any

from app import constants
from app.helpers.singleton_meta import SingletonMeta


class TranslationsCache(metaclass=SingletonMeta):
    """
    This class is responsible for caching translations (Singleton class).
    """

    def __init__(self):
        self.__cache = {}

        self.__is_loaded = False

    def load(self):
        """Load content of translations.json into cache"""

        if not self.__cache:
            if os.path.isfile(constants.TRANSLATIONS_JSON):
                with open(constants.TRANSLATIONS_JSON, "r") as file:
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
