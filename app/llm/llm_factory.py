"""
llm_factory.py - Provider-agnostic LLM initialization.

Creates and returns an LLM instance based on the configured provider.
Switching between Google Gemini and Ollama requires only a .env change:
    LLM_PROVIDER=gemini   →  Google Gemini (free tier, cloud)
    LLM_PROVIDER=ollama   →  Ollama (local, requires Ollama server)

Both return a LangChain BaseChatModel so the rest of the code is
completely provider-agnostic.
"""

from langchain_core.language_models import BaseChatModel

from app.config import (
    LLM_PROVIDER,
    GOOGLE_API_KEY,
    GEMINI_MODEL,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Module-level cache for the LLM instance.
_llm_instance = None


def get_llm(provider: str = None) -> BaseChatModel:
    """Get the configured LLM instance (singleton pattern).

    The LLM is initialized once and reused across the application.
    This avoids repeated API key validation and connection setup.

    Args:
        provider: LLM provider name ("gemini" or "ollama").
                  Default from config.

    Returns:
        A LangChain BaseChatModel instance.

    Raises:
        ValueError: If the provider is not supported or misconfigured.
    """
    global _llm_instance

    if provider is None:
        provider = LLM_PROVIDER

    if _llm_instance is None:
        logger.info(f"Initializing LLM with provider: {provider}")

        if provider == "gemini":
            _llm_instance = _create_gemini_llm()
        elif provider == "ollama":
            _llm_instance = _create_ollama_llm()
        else:
            raise ValueError(
                f"Unsupported LLM provider: '{provider}'. "
                f"Supported: 'gemini', 'ollama'"
            )

        logger.info(f"LLM initialized successfully ({provider})")
    else:
        logger.debug("Using cached LLM instance")

    return _llm_instance


def _create_gemini_llm() -> BaseChatModel:
    """Create a Google Gemini LLM instance.

    Requires GOOGLE_API_KEY in .env. Uses the free tier by default.

    Returns:
        ChatGoogleGenerativeAI instance.

    Raises:
        ValueError: If the API key is not set.
    """
    api_key = os.getenv("GOOGLE_API_KEY") or GOOGLE_API_KEY
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY not found. Please enter it in the sidebar or set it in .env file. "
            "Get a free key at: https://aistudio.google.com/app/apikey"
        )

    from langchain_google_genai import ChatGoogleGenerativeAI

    llm = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=api_key,
        temperature=0.1,  # Low temperature for factual, consistent answers.
        max_output_tokens=2048,
    )

    logger.info(f"Gemini LLM created with model: {GEMINI_MODEL}")
    return llm


def _create_ollama_llm() -> BaseChatModel:
    """Create an Ollama LLM instance (local).

    Requires Ollama server running locally. Install from https://ollama.ai

    Returns:
        ChatOllama instance.
    """
    from langchain_community.chat_models import ChatOllama

    llm = ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0.1,
    )

    logger.info(f"Ollama LLM created with model: {OLLAMA_MODEL}")
    return llm


def reset_llm() -> None:
    """Reset the cached LLM instance.

    Useful when switching providers at runtime (e.g., in tests).
    """
    global _llm_instance
    _llm_instance = None
    logger.info("LLM instance reset")
