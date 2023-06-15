import json
from collections import OrderedDict
from functools import wraps
from hashlib import sha256

from fastapi.encoders import jsonable_encoder

from app.utils.singleton_meta import SingletonMeta


class ApiCache(metaclass=SingletonMeta):
    """
    Singleton class
    Cache API responses
    """

    def __init__(self):
        self.__cache = OrderedDict()
        self.__is_checking_cache_size = False

    def cache_response(self, func):
        """Decorator for caching API responses"""

        @wraps(func)
        async def wrapper(*args: tuple, **kwargs: dict):
            kwargs_jsonable = jsonable_encoder(kwargs)
            kwargs_jsonable["function_name"] = func.__name__
            kwargs_json = json.dumps(kwargs_jsonable, sort_keys=True)
            hash_value = sha256(kwargs_json.encode()).hexdigest()

            if hash_value in self.__cache:
                # Return cached result
                result = self.__cache.get(hash_value)

                return result
            else:
                self.__check_cache_size()

                # Create result, cache result, return result
                result = await func(*args, **kwargs)
                self.__cache[hash_value] = result

                return result

        return wrapper

    def __check_cache_size(self):
        """Clear cache when cached items are over 1000"""

        if len(self.__cache) > 1000:
            if self.__is_checking_cache_size:
                return

            self.__is_checking_cache_size = True

            self.clear_cache()

            self.__is_checking_cache_size = False

    def get_cache(self):
        """Get cache"""

        return self.__cache

    def clear_cache(self):
        """Clear cache"""

        if len(self.__cache) > 0:
            self.__cache.clear()


api_cache = ApiCache()
