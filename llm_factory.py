"""
LLM Factory for CrewAI with LiteLLM Proxy Support
Handles JWT token passing and fallback strategies
"""

import os
from typing import Optional, Dict, Any
from crewai import LLM
from ivcap_service import getLogger

logger = getLogger("app.llm")

class LLMFactory:
    """Factory for creating LLM instances with proper authentication."""

    def __init__(self, litellm_proxy_url: Optional[str] = None):
        self.litellm_proxy_url = litellm_proxy_url or os.getenv("LITELLM_PROXY_URL")
        self.default_model = os.getenv("LITELLM_DEFAULT_MODEL", "gpt-5")
        self.fallback_model = os.getenv("LITELLM_FALLBACK_MODEL", "gpt-5-mini")

    def create_llm(
        self,
        jwt_token: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> LLM:
        """
        Create an LLM instance with proper configuration.

        Args:
            jwt_token: JWT token for authentication with LiteLLM proxy
            model: Model name override (defaults to LITELLM_DEFAULT_MODEL)
            **kwargs: Additional LLM configuration parameters

        Returns:
            Configured LLM instance
        """
        model = model or self.default_model

        # Primary configuration: Use LiteLLM proxy with JWT
        if self.litellm_proxy_url and jwt_token:
            logger.info(f"Creating LLM with LiteLLM proxy: {self.litellm_proxy_url}")

            # CrewAI LLM class passes through to LiteLLM
            # LiteLLM will handle the authentication with the Bearer token
            llm_config = {
                "model": model,
                "base_url": self.litellm_proxy_url,
                "api_key": jwt_token,  # JWT token as API key
                "default_headers": {
                    "Authorization": f"Bearer {jwt_token}"
                },
                **kwargs
            }

            try:
                return LLM(**llm_config)
            except Exception as e:
                logger.warning(f"Failed to create LLM with proxy: {e}")
                # Fall through to fallback

        # Fallback 1: Use LiteLLM proxy without JWT (if proxy allows)
        elif self.litellm_proxy_url:
            logger.info("Creating LLM with LiteLLM proxy (no JWT)")

            llm_config = {
                "model": model,
                "base_url": self.litellm_proxy_url,
                **kwargs
            }

            try:
                return LLM(**llm_config)
            except Exception as e:
                logger.warning(f"Failed to create LLM with proxy (no JWT): {e}")

        # Fallback 2: Direct OpenAI API (if API key available)
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            logger.info("Falling back to direct OpenAI API")
            return LLM(
                model=self.fallback_model,
                api_key=openai_key,
                **kwargs
            )

        # Final fallback: Basic configuration (will likely fail but provides clear error)
        logger.error("No valid LLM configuration available")
        raise ValueError(
            "No valid LLM configuration. Please set either:\n"
            "1. LITELLM_PROXY_URL with JWT authentication, or\n"
            "2. OPENAI_API_KEY for direct API access"
        )

# Singleton instance
_llm_factory = None

def get_llm_factory() -> LLMFactory:
    """Get or create the singleton LLM factory instance."""
    global _llm_factory
    if _llm_factory is None:
        _llm_factory = LLMFactory()
    return _llm_factory