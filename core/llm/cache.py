"""Prompt cache management for The Hive."""

import hashlib
import json
from typing import Any, Optional

from ..memory.redis.client import get_redis_client


class PromptCache:
    """Cache for LLM prompts to reduce cost and latency."""

    def __init__(self, ttl: int = 604800):
        """Initialize prompt cache.

        Args:
            ttl: Time to live in seconds (default 7 days)
        """
        self.redis = get_redis_client()
        self.ttl = ttl

    def _hash_prompt(self, prompt: str) -> str:
        """Hash a prompt for cache key.

        Args:
            prompt: Input prompt

        Returns:
            Hash string
        """
        return hashlib.sha256(prompt.encode()).hexdigest()

    def get(self, prompt: str) -> Optional[str]:
        """Get cached response for prompt.

        Args:
            prompt: Input prompt

        Returns:
            Cached response or None
        """
        key = f"prompt_cache:{self._hash_prompt(prompt)}"
        return self.redis.get(key)

    def set(self, prompt: str, response: str) -> None:
        """Cache prompt-response pair.

        Args:
            prompt: Input prompt
            response: Response to cache
        """
        key = f"prompt_cache:{self._hash_prompt(prompt)}"
        self.redis.set(key, response, self.ttl)

    def clear(self, prompt: str) -> None:
        """Clear cached response for prompt.

        Args:
            prompt: Input prompt
        """
        key = f"prompt_cache:{self._hash_prompt(prompt)}"
        self.redis.delete(key)
