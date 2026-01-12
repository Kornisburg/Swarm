"""LLM provider abstraction for The Hive."""

import os
from abc import ABC, abstractmethod
from typing import Any, Optional

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from ..config import get_settings
from ..exceptions import AgentException


class LLMProvider(ABC):
    """Abstract base for LLM providers."""

    @abstractmethod
    async def complete(self, prompt: str, **kwargs: Any) -> str:
        """Complete a prompt.

        Args:
            prompt: Input prompt
            **kwargs: Additional arguments

        Returns:
            Completion text
        """
        pass

    @abstractmethod
    def estimate_cost(self, prompt: str, response: str) -> float:
        """Estimate cost in USD.

        Args:
            prompt: Input prompt
            response: Response text

        Returns:
            Estimated cost in USD
        """
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""

    def __init__(self):
        """Initialize OpenAI provider."""
        settings = get_settings()
        if not settings.openai_api_key:
            raise AgentException("OpenAI API key not configured")

        self.client = ChatOpenAI(
            api_key=settings.openai_api_key,
            model="gpt-4",
            temperature=settings.model_temperature,
            max_tokens=settings.max_tokens,
        )
        self.model = "gpt-4"

    async def complete(self, prompt: str, **kwargs: Any) -> str:
        """Complete a prompt with OpenAI.

        Args:
            prompt: Input prompt
            **kwargs: Additional arguments

        Returns:
            Completion text
        """
        response = await self.client.ainvoke(prompt, **kwargs)
        return response.content

    def estimate_cost(self, prompt: str, response: str) -> float:
        """Estimate OpenAI cost.

        Args:
            prompt: Input prompt
            response: Response text

        Returns:
            Estimated cost in USD
        """
        # GPT-4 pricing (as of 2024)
        input_cost_per_1k = 0.03
        output_cost_per_1k = 0.06

        prompt_tokens = len(prompt.split()) * 1.3  # Rough estimate
        response_tokens = len(response.split()) * 1.3

        cost = (
            (prompt_tokens / 1000) * input_cost_per_1k
            + (response_tokens / 1000) * output_cost_per_1k
        )
        return cost


class AnthropicProvider(LLMProvider):
    """Anthropic LLM provider."""

    def __init__(self):
        """Initialize Anthropic provider."""
        settings = get_settings()
        if not settings.anthropic_api_key:
            raise AgentException("Anthropic API key not configured")

        self.client = ChatAnthropic(
            api_key=settings.anthropic_api_key,
            model="claude-3-opus-20240229",
            temperature=settings.model_temperature,
            max_tokens=settings.max_tokens,
        )
        self.model = "claude-3-opus-20240229"

    async def complete(self, prompt: str, **kwargs: Any) -> str:
        """Complete a prompt with Anthropic.

        Args:
            prompt: Input prompt
            **kwargs: Additional arguments

        Returns:
            Completion text
        """
        response = await self.client.ainvoke(prompt, **kwargs)
        return response.content

    def estimate_cost(self, prompt: str, response: str) -> float:
        """Estimate Anthropic cost.

        Args:
            prompt: Input prompt
            response: Response text

        Returns:
            Estimated cost in USD
        """
        # Claude 3 Opus pricing (as of 2024)
        input_cost_per_1k = 0.015
        output_cost_per_1k = 0.075

        prompt_tokens = len(prompt.split()) * 1.3
        response_tokens = len(response.split()) * 1.3

        cost = (
            (prompt_tokens / 1000) * input_cost_per_1k
            + (response_tokens / 1000) * output_cost_per_1k
        )
        return cost


def get_llm_provider() -> LLMProvider:
    """Get LLM provider based on configuration.

    Returns:
        LLM provider instance

    Raises:
        AgentException: If provider not configured
    """
    settings = get_settings()

    if settings.llm_provider.lower() == "openai":
        return OpenAIProvider()
    elif settings.llm_provider.lower() == "anthropic":
        return AnthropicProvider()
    else:
        raise AgentException(f"Unknown LLM provider: {settings.llm_provider}")
