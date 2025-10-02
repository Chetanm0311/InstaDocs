from typing import Dict
from .base_provider import BaseLLMProvider


class FallbackProvider(BaseLLMProvider):
    """Rule-based fallback provider when no LLM is available"""
    
    def __init__(self):
        super().__init__(api_key=None)
    
    def _initialize(self, **kwargs) -> None:
        """Fallback is always available"""
        self.is_initialized = True
        print("ℹ️ Using rule-based fallback (no LLM configured)")
    
    def generate_completion(self, system_prompt: str, user_message: str, **kwargs) -> Dict:
        """Generate rule-based response"""
        context_text = user_message.split("Context:\n")[-1].split("\n\nQuestion:")[0]
        query = user_message.split("Question: ")[-1]
        
        # Check if no context
        if "No relevant context found" in context_text:
            return {
                "answer": f"I couldn't find relevant information in the knowledge base to answer: '{query}'. Please upload documents related to this topic.",
                "confidence": 0.1,
                "sources_used": [],
                "is_complete": False,
                "missing_information": [f"Information about: {query}"],
                "enrichment_suggestions": [
                    {
                        "missing_topic": query,
                        "suggested_action": f"Upload documents containing information about {query}",
                        "priority": "high"
                    }
                ],
                "reasoning": "No relevant documents found in the knowledge base."
            }
        
        # Extract sources and relevance
        sources = []
        avg_relevance = 0.0
        relevance_count = 0
        
        lines = context_text.split('\n')
        for line in lines:
            if line.startswith('[Source'):
                try:
                    source = line.split(': ')[1].split(' - ')[0]
                    if source not in sources:
                        sources.append(source)
                    
                    if 'Relevance:' in line:
                        rel_str = line.split('Relevance: ')[1].split(')')[0]
                        avg_relevance += float(rel_str)
                        relevance_count += 1
                except:
                    pass
        
        if relevance_count > 0:
            avg_relevance /= relevance_count
        
        # Determine confidence and completeness
        confidence = min(avg_relevance, 0.65)  # Cap at 0.65 for rule-based
        is_complete = confidence > 0.5
        
        # Build answer
        if confidence > 0.4:
            answer = f"Based on the available documents:\n\n{context_text[:800]}"
            if len(context_text) > 800:
                answer += "...\n\n(More information available in source documents)"
        else:
            answer = f"I found some information, but it may not be highly relevant to: '{query}'"
        
        # Generate suggestions if incomplete
        missing_info = []
        suggestions = []
        
        if not is_complete:
            missing_info = ["More comprehensive information on this topic"]
            suggestions = [{
                "missing_topic": query,
                "suggested_action": "Upload more detailed documents about this specific topic",
                "priority": "medium"
            }]
        
        return {
            "answer": answer,
            "confidence": confidence,
            "sources_used": sources,
            "is_complete": is_complete,
            "missing_information": missing_info if missing_info else None,
            "enrichment_suggestions": suggestions if suggestions else None,
            "reasoning": f"Rule-based response (relevance: {avg_relevance:.2f}). Configure an LLM provider for better results."
        }
    
    def get_provider_name(self) -> str:
        return "Rule-Based Fallback"
