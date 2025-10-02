from abc import ABC, abstractmethod
from typing import Dict, Optional


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        self.api_key = api_key
        self.is_initialized = False
        self._initialize(**kwargs)
    
    @abstractmethod
    def _initialize(self, **kwargs) -> None:
        """Initialize the provider (setup client, validate credentials, etc.)"""
        pass
    
    @abstractmethod
    def generate_completion(self, system_prompt: str, user_message: str, **kwargs) -> Dict:
        """
        Generate a completion from the LLM
        
        Args:
            system_prompt: System instructions
            user_message: User query with context
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Dict with structured response matching AnswerResponse schema
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the provider name for logging"""
        pass
    
    def is_available(self) -> bool:
        """Check if provider is available and initialized"""
        return self.is_initialized
    
    def test_connection(self) -> bool:
        """Test if the provider connection works"""
        try:
            test_response = self.generate_completion(
                system_prompt="You are a helpful assistant.",
                user_message="Say 'test' in one word.",
                max_tokens=5
            )
            return test_response is not None
        except Exception as e:
            print(f"⚠️ Connection test failed for {self.get_provider_name()}: {e}")
            return False
