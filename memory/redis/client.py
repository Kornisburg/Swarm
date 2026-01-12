"""Redis client wrapper for The Hive."""

import os
import json
from typing import Any, Optional

import redis


class RedisClient:
    """Redis client for session state management."""

    def __init__(self, redis_url: Optional[str] = None):
        """Initialize Redis client.

        Args:
            redis_url: Redis connection URL. If None, builds from env vars.
        """
        if redis_url is None:
            redis_url = self._get_redis_url()

        self.client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )

    def _get_redis_url(self) -> str:
        """Build Redis URL from environment variables."""
        host = os.getenv("REDIS_HOST", "localhost")
        port = os.getenv("REDIS_PORT", "6379")
        return f"redis://{host}:{port}"

    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis.

        Args:
            key: Redis key

        Returns:
            Value if exists, None otherwise
        """
        value = self.client.get(key)
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    def set(self, key: str, value: Any, ttl: int = 86400) -> bool:
        """Set value in Redis.

        Args:
            key: Redis key
            value: Value to store
            ttl: Time to live in seconds (default 24 hours)

        Returns:
            True if successful, False otherwise
        """
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        return self.client.setex(key, ttl, value)

    def delete(self, key: str) -> bool:
        """Delete key from Redis.

        Args:
            key: Redis key

        Returns:
            True if key was deleted, False otherwise
        """
        return self.client.delete(key) > 0

    def lpush(self, key: str, *values: Any) -> int:
        """Push values to left of list.

        Args:
            key: Redis key
            *values: Values to push

        Returns:
            List length after push
        """
        serialized = []
        for value in values:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            serialized.append(value)
        return self.client.lpush(key, *serialized)

    def lrange(self, key: str, start: int = 0, end: int = -1) -> list:
        """Get range of list elements.

        Args:
            key: Redis key
            start: Start index
            end: End index

        Returns:
            List of values
        """
        values = self.client.lrange(key, start, end)
        result = []
        for value in values:
            try:
                result.append(json.loads(value))
            except json.JSONDecodeError:
                result.append(value)
        return result

    def hset(self, key: str, mapping: dict[str, Any]) -> int:
        """Set hash fields.

        Args:
            key: Redis key
            mapping: Dictionary of field-value pairs

        Returns:
            Number of fields set
        """
        serialized = {}
        for k, v in mapping.items():
            if isinstance(v, (dict, list)):
                v = json.dumps(v)
            serialized[k] = v
        return self.client.hset(key, mapping=serialized)

    def hgetall(self, key: str) -> dict[str, Any]:
        """Get all hash fields.

        Args:
            key: Redis key

        Returns:
            Dictionary of field-value pairs
        """
        values = self.client.hgetall(key)
        result = {}
        for k, v in values.items():
            try:
                result[k] = json.loads(v)
            except json.JSONDecodeError:
                result[k] = v
        return result

    def health_check(self) -> bool:
        """Check Redis connection health.

        Returns:
            True if Redis is accessible, False otherwise
        """
        try:
            return self.client.ping()
        except Exception:
            return False


# Global client instance
_client: Optional[RedisClient] = None


def get_redis_client() -> RedisClient:
    """Get global Redis client instance.

    Returns:
        Redis client
    """
    global _client
    if _client is None:
        _client = RedisClient()
    return _client
