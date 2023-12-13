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

import inspect
import json
from functools import wraps
from typing import Any

from cachetools import LRUCache
from fastapi import Request
from fastapi.encoders import jsonable_encoder

from app import utils
from app.helpers.singleton_meta import SingletonMeta


class ApiCache(metaclass=SingletonMeta):
    """
    Cache API responses (Singleton class)
    """

    def __init__(self):
        self.__cache = LRUCache(maxsize=1000)

    def cache_response(self, func):
        """Decorator for caching API responses"""

        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def wrapper(*args: tuple, **kwargs: dict):
                hash_value = self.__get_hash_value(**kwargs)
                if self.__hash_exists(hash_value):
                    # Return cached result
                    return self.__cache.get(hash_value)
                else:
                    # Create result, cache result, return result
                    result = await func(*args, **kwargs)
                    self.__cache[hash_value] = result

                    return result

        else:

            @wraps(func)
            def wrapper(*args: tuple, **kwargs: dict):
                hash_value = self.__get_hash_value(**kwargs)
                if self.__hash_exists(hash_value):
                    # Return cached result
                    return self.__cache.get(hash_value)
                else:
                    # Create result, cache result, return result
                    result = func(*args, **kwargs)
                    self.__cache[hash_value] = result

                    return result

        return wrapper

    def __get_hash_value(self, **kwargs: dict) -> str:
        """Get hash value"""

        # Get path from request
        request: Request | Any = kwargs.get("_request")
        if kwargs.get("_request"):
            path = request.url.path
        else:
            path = ""

        # Remove request
        kwargs.pop("_request")

        # Create a jsonable dict from kwargs
        kwargs_jsonable = jsonable_encoder(kwargs)

        # Add path to jsonable kwargs
        kwargs_jsonable["path"] = path

        # Create hash value
        kwargs_json = json.dumps(kwargs_jsonable, sort_keys=True)
        hash_value = utils.get_string_hash_value(kwargs_json)

        return hash_value

    def __hash_exists(self, hash_value: str) -> bool:
        """Check if hash exists"""

        return hash_value in self.__cache.keys()

    def get_cache(self):
        """Get cache"""

        return self.__cache

    def clear_cache(self):
        """Clear cache"""

        if len(self.__cache) > 0:
            self.__cache.clear()
