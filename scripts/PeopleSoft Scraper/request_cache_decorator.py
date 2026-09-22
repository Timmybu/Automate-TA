import json
import os
import time
from functools import wraps

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache")


def cache_request(ttl=None, force=False, cache_dir=CACHE_DIR):
    """Cache a function's return value based on its arguments.

    Builds the cache key by concatenating all positional and keyword
    arguments as text and hashing them. Results are persisted as JSON
    files on disk so the cache survives across runs.

    Args:
        ttl: seconds before a cached entry expires. None = never expires.
        force: if True, skip reading the cache and always call the
            function, overwriting any existing entry.
        cache_dir: directory where cache files are stored.
    """
    os.makedirs(cache_dir, exist_ok=True)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key_parts = [func.__name__]
            key_parts.extend(str(a) for a in args)
            key_parts.extend(f"v" for k, v in sorted(kwargs.items()))
            key_text = "_".join(key_parts)
            cache_path = os.path.join(cache_dir, f"{key_text}.json")

            if not force and os.path.exists(cache_path):
                with open(cache_path, "r") as f:
                    entry = json.load(f)
                if ttl is None or (time.time() - entry["cached_at"]) < ttl:
                    return entry["result"]

            result = func(*args, **kwargs)

            with open(cache_path, "w") as f:
                json.dump({"cached_at": time.time(), "result": result}, f, indent=2)

            return result

        return wrapper

    return decorator
