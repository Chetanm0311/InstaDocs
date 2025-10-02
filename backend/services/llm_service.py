import uuid
from typing import List
from backend.models.schemas import AnswerResponse, EnrichmentSuggestion
from backend.providers import BaseLLMProvider, LLMProviderFactory


class LLMService:
    """Service for LLM-based answer generation with completeness detection"""
    
    SYSTEM_PROMPT = """You are an intelligent knowledge base assistant. Your responsibilities:

1. Answer questions using ONLY the provided context from the knowledge base
2. Assess whether you have sufficient information (provide confidence score 0-1)
3. Identify specific information gaps when answer is incomplete
4. Suggest concrete enrichment actions to fill those gaps

IMPORTANT RULES:
- If context is relevant and complete: confidence > 0.7, is_complete = true
- If context is partial or vague: confidence 0.4-0.7, is_complete = false
- If context is irrelevant or missing: confidence < 0.4, is_complete = false
- Always cite which sources you used
- Be honest about uncertainties

Respond in valid JSON format with these exact fields:
{
  "answer": "Your detailed answer here",
  "confidence": 0.85,
  "sources_used": ["document1.pdf", "document2.txt"],
  "is_complete": true,
  "missing_information": ["specific gap 1", "specific gap 2"],
  "enrichment_suggestions": [
    {
      "missing_topic": "specific topic name",
      "suggested_action": "concrete action to get this info",
      "priority": "high"
    }
  ],
  "reasoning": "Explain why you're confident or not"
}"""

    def __init__(self, provider: BaseLLMProvider = None):
        """
        Initialize LLM service with a provider
        
        Args:
            provider: Specific provider instance, or None to auto-detect from env
        """
        self.provider = provider or LLMProviderFactory.create_from_env()
        print(f"📡 Active LLM Provider: {self.provider.get_provider_name()}")
    
    def set_provider(self, provider: BaseLLMProvider):
        """Switch to a different provider at runtime"""
        if provider and provider.is_available():
            self.provider = provider
            print(f"🔄 Switched to: {provider.get_provider_name()}")
        else:
            print("⚠️ Provider not available, keeping current provider")
    
    def _format_context(self, context: List[dict]) -> str:
        """Format retrieved context for LLM"""
        if not context:
            return "No relevant context found in the knowledge base."
        
        formatted = []
        for idx, ctx in enumerate(context, 1):
            formatted.append(
                f"[Source {idx}: {ctx['source']} - Page {ctx.get('page', 'N/A')} "
                f"(Relevance: {ctx['relevance_score']:.2f})]\n{ctx['content']}\n"
            )
        return "\n".join(formatted)
    
    def generate_answer(self, query: str, context: List[dict]) -> AnswerResponse:
        """
        Generate answer with completeness assessment
        
        Args:
            query: User's question
            context: List of retrieved document chunks
            
        Returns:
            Structured AnswerResponse with confidence and enrichment suggestions
        """
        # Format context
        context_text = self._format_context(context)
        
        # Build user message
        user_message = f"Context:\n{context_text}\n\nQuestion: {query}"
        
        # Generate response using active provider
        try:
            result = self.provider.generate_completion(
                system_prompt=self.SYSTEM_PROMPT,
                user_message=user_message,
                temperature=0.3,
                max_tokens=1500
            )
        except Exception as e:
            print(f"❌ Provider failed: {e}")
            # Try fallback if current provider fails
            from backend.providers import FallbackProvider
            fallback = FallbackProvider()
            result = fallback.generate_completion(
                system_prompt=self.SYSTEM_PROMPT,
                user_message=user_message
            )
        
        # Parse enrichment suggestions
        enrichment_suggestions = None
        if result.get("enrichment_suggestions"):
            enrichment_suggestions = [
                EnrichmentSuggestion(**suggestion)
                for suggestion in result["enrichment_suggestions"]
            ]
        
        # Create response object
        response = AnswerResponse(
            query_id=str(uuid.uuid4()),
            answer=result["answer"],
            confidence=result["confidence"],
            sources_used=result["sources_used"],
            is_complete=result["is_complete"],
            missing_information=result.get("missing_information"),
            enrichment_suggestions=enrichment_suggestions,
            reasoning=result["reasoning"]
        )
        
        return response
    
    def get_provider_info(self) -> dict:
        """Get information about the current provider"""
        return {
            "provider_name": self.provider.get_provider_name(),
            "is_available": self.provider.is_available()
        }
