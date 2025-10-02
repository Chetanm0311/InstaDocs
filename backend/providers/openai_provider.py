import json
from typing import Dict, Optional
from .base_provider import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider implementation"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        self.model = model
        self.client = None
        super().__init__(api_key=api_key)
    
    def _initialize(self, **kwargs) -> None:
        """Initialize OpenAI client"""
        if not self.api_key or not self.api_key.startswith("sk-"):
            print("⚠️ Invalid or missing OpenAI API key")
            return
        
        try:
            from openai import OpenAI
            
            self.client = OpenAI(api_key=self.api_key)
            
            # Test connection
            if self.test_connection():
                self.is_initialized = True
                print(f"✅ OpenAI initialized with model: {self.model}")
            else:
                print("❌ OpenAI connection test failed")
                
        except ImportError:
            print("❌ OpenAI library not installed: pip install openai")
        except Exception as e:
            print(f"❌ OpenAI initialization failed: {e}")
    
    def generate_completion(self, system_prompt: str, user_message: str, **kwargs) -> Dict:
        """Generate completion using OpenAI"""
        if not self.is_initialized or not self.client:
            raise RuntimeError("OpenAI provider not initialized")
        
        try:
            response = self.client.chat.completions.create(
                model=kwargs.get("model", self.model),
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=kwargs.get("temperature", 0.3),
                max_tokens=kwargs.get("max_tokens", 1500)
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"❌ OpenAI API error: {e}")
            raise
    
    def get_provider_name(self) -> str:
        return f"OpenAI ({self.model})"
