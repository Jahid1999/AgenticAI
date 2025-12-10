"""
Client factory for multiple AI providers using OpenAI Agents SDK.
Supports OpenAI, DeepSeek, and Gemini providers.
"""

import os
from typing import Literal
from openai import AsyncOpenAI


ClientName = Literal["openai", "deepseek", "gemini"]


def get_client(client_name: ClientName) -> AsyncOpenAI | None:
    """
    Get an AsyncOpenAI client for the specified provider.

    Args:
        client_name: The name of the client to get ("openai", "deepseek", "gemini").

    Returns:
        The AsyncOpenAI client configured for the specified provider.
    """
    # ====> For OpenAI models <====
    if client_name == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set in the environment variables.")
        return AsyncOpenAI(api_key=api_key)

    # ====> For DeepSeek models <====
    elif client_name == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY is not set in the environment variables.")
        return AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
        )

    # ====> For Google Gemini models <====
    elif client_name == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set in the environment variables.")
        return AsyncOpenAI(
            api_key=api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )

    else:
        print(f"Unsupported client: {client_name}")
        return None


def get_model_for_client(client_name: ClientName) -> str:
    """
    Get the default model name for the specified client.

    Args:
        client_name: The name of the client.

    Returns:
        The default model name for the client.
    """
    models = {
        "openai": "gpt-4o-mini",
        "deepseek": "deepseek-chat",
        "gemini": "gemini-2.5-flash",
    }
    return models.get(client_name, "gpt-4o-mini")
