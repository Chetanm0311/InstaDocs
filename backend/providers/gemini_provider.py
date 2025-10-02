from typing import Dict, Optional
from .base_provider import BaseLLMProvider


class GeminiProvider(BaseLLMProvider):
    """Google Gemini provider implementation"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = None
        super().__init__(api_key=api_key)
    
    def _initialize(self, **kwargs) -> None:
        """Initialize Gemini client"""
        if not self.api_key:
            print("⚠️ Missing Google API key")
            return
        
        try:
            from backend.services.chat_service.gemini_service import Gemini
            
            self.client = Gemini()
            self.is_initialized = True
            print("✅ Gemini initialized")
            
        except ImportError:
            print("❌ Gemini service not available")
        except Exception as e:
            print(f"❌ Gemini initialization failed: {e}")
    
    def generate_completion(self, system_prompt: str, user_message: str, **kwargs) -> Dict:
        """Generate completion using Gemini"""
        if not self.is_initialized or not self.client:
            raise RuntimeError("Gemini provider not initialized")
        
        try:
            response = self.client.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
            )
            
            return response
            
        except Exception as e:
            print(f"❌ Gemini API error: {e}")
            raise
    
    def get_provider_name(self) -> str:
        return "Google Gemini"
