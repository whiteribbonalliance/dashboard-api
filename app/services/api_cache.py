"""
Cache API responses
"""

import json
from collections import OrderedDict
from functools import wraps
from hashlib import sha256

from fastapi.encoders import jsonable_encoder

cache = OrderedDict()
is_checking_cache_size = False


def cache_response(func):
    """Decorator for caching API responses"""

    global cache

    @wraps(func)
    async def wrapper(*args: tuple, **kwargs: dict):
        kwargs_jsonable = jsonable_encoder(kwargs)
        kwargs_json = json.dumps(kwargs_jsonable, sort_keys=True)
        hash_value = sha256(kwargs_json.encode()).hexdigest()

        if hash_value in cache:
            # Return cached result
            result = cache.get(hash_value)

            return result
        else:
            check_cache_size()

            # Create result, cache result, return result
            result = await func(*args, **kwargs)
            cache[hash_value] = result

            return result

    return wrapper


def check_cache_size():
    """Clear cache when cached items is over 1000"""

    if len(cache) > 1000:
        global is_checking_cache_size

        if is_checking_cache_size:
            return

        is_checking_cache_size = True

        clear_cache()

        is_checking_cache_size = False


def get_cache():
    """Get cache"""

    global cache

    return cache


def clear_cache():
    """Clear cache"""

    global cache

    if len(cache) > 0:
        cache.clear()
