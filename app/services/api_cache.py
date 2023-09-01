import inspect
import json
from functools import wraps
from hashlib import sha256

from cachetools import LRUCache
from fastapi.encoders import jsonable_encoder

from app.utils.singleton_meta import SingletonMeta


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
        if kwargs.get("parameters").request:
            path = kwargs.get("parameters").request.url.path
        else:
            path = ""

        # Set request as None as it is not needed anymore
        kwargs.get("parameters").request = None

        # Create a jsonable dict from kwargs
        kwargs_jsonable = jsonable_encoder(kwargs)

        # Remove request
        kwargs_jsonable.get("parameters").pop("request")

        # Add path to jsonable kwargs
        kwargs_jsonable["path"] = path

        # Create hash value
        kwargs_json = json.dumps(kwargs_jsonable, sort_keys=True)
        hash_value = sha256(kwargs_json.encode()).hexdigest()

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
