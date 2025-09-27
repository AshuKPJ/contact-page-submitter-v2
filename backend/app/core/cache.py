# backend/app/core/cache.py
import json
import redis
from typing import Optional, Dict, Any, List, Literal, Union
from datetime import timedelta

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
)


def cache_get(key: str) -> Optional[Any]:
    """Get value from cache."""
    try:
        value = redis_client.get(key)
        return json.loads(value) if value else None
    except (redis.RedisError, json.JSONDecodeError):
        return None


def cache_set(key: str, value: Any, expire: int = 5):
    """Set value in cache with expiration in seconds."""
    try:
        redis_client.setex(key, timedelta(seconds=expire), json.dumps(value))
    except (redis.RedisError, json.JSONEncodeError):
        pass
