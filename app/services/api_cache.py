import json
from functools import wraps
from hashlib import sha256

from cachetools import LRUCache
from fastapi.encoders import jsonable_encoder

from app.utils.singleton_meta import SingletonMeta


class ApiCache(metaclass=SingletonMeta):
    """
    Singleton class
    Cache API responses
    """

    def __init__(self):
        self.__cache = LRUCache(maxsize=1000)

    def cache_response(self, func):
        """Decorator for caching API responses"""

        @wraps(func)
        async def wrapper(*args: tuple, **kwargs: dict):
            # Get path from request
            path = kwargs.get("common_parameters").request.url.path

            # Set request as None as it is not needed anymore
            kwargs.get("common_parameters").request = None

            # Create a jsonable dict from kwargs
            kwargs_jsonable = jsonable_encoder(kwargs)

            # Remove request
            kwargs_jsonable.get("common_parameters").pop("request")

            # Add path to jsonable kwargs
            kwargs_jsonable["path"] = path

            # Create hash value
            kwargs_json = json.dumps(kwargs_jsonable, sort_keys=True)
            hash_value = sha256(kwargs_json.encode()).hexdigest()

            if hash_value in self.__cache.keys():
                # Return cached result
                result = self.__cache.get(hash_value)

                return result
            else:
                # Create result, cache result, return result
                result = await func(*args, **kwargs)
                self.__cache[hash_value] = result

                return result

        return wrapper

    def get_cache(self):
        """Get cache"""

        return self.__cache

    def clear_cache(self):
        """Clear cache"""

        if len(self.__cache) > 0:
            self.__cache.clear()
