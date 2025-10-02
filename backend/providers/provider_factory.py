import os
from typing import Optional, List
from .base_provider import BaseLLMProvider
from .openai_provider import OpenAIProvider
from .gemini_provider import GeminiProvider
from .geni_provider import GeniProvider
from .fallback_provider import FallbackProvider


class LLMProviderFactory:
    """Factory for creating and managing LLM providers"""
    
    @staticmethod
    def create_provider(provider_type: str, **kwargs) -> Optional[BaseLLMProvider]:
        """
        Create a specific provider instance
        
        Args:
            provider_type: Type of provider ('openai', 'gemini', 'geni', 'fallback')
            **kwargs: Provider-specific configuration
            
        Returns:
            Initialized provider or None if creation fails
        """
        providers_map = {
            'openai': OpenAIProvider,
            'gemini': GeminiProvider,
            'geni': GeniProvider,
            'fallback': FallbackProvider
        }
        
        provider_class = providers_map.get(provider_type.lower())
        if not provider_class:
            print(f"⚠️ Unknown provider type: {provider_type}")
            return None
        
        try:
            provider = provider_class(**kwargs)
            return provider if provider.is_available() else None
        except Exception as e:
            print(f"❌ Failed to create {provider_type} provider: {e}")
            return None
    
    @staticmethod
    def create_from_env() -> BaseLLMProvider:
        """
        Create provider based on environment variables
        Priority: OpenAI > Gemini > Geni > Fallback
        
        Returns:
            First available provider or FallbackProvider
        """
        print("\n🔍 Detecting available LLM providers...")
        
        # Try OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key and openai_key.startswith("sk-"):
            provider = LLMProviderFactory.create_provider(
                'openai',
                api_key=openai_key,
                model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
            )
            if provider:
                return provider
        
        # Try Gemini
        google_key = os.getenv("GOOGLE_API_KEY")
        if google_key:
            provider = LLMProviderFactory.create_provider(
                'gemini',
                api_key=google_key
            )
            if provider:
                return provider
        
        # Try Geni
        geni_key = os.getenv("GENI_API_KEY")
        if geni_key:
            provider = LLMProviderFactory.create_provider(
                'geni',
                api_key=geni_key
            )
            if provider:
                return provider
        
        # Fallback
        print("⚠️ No LLM providers configured, using fallback")
        return FallbackProvider()
    
    @staticmethod
    def get_all_available_providers() -> List[BaseLLMProvider]:
        """
        Get list of all available providers
        
        Returns:
            List of initialized and available providers
        """
        available = []
        
        # Check each provider
        for provider_type in ['openai', 'gemini', 'geni']:
            api_key = os.getenv(f"{provider_type.upper()}_API_KEY")
            if api_key:
                provider = LLMProviderFactory.create_provider(
                    provider_type,
                    api_key=api_key
                )
                if provider:
                    available.append(provider)
        
        # Always add fallback
        available.append(FallbackProvider())
        
        return available
