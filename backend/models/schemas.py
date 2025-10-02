from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class EnrichmentSuggestion(BaseModel):
    """Suggestion for enriching the knowledge base"""
    missing_topic: str
    suggested_action: str
    priority: str = Field(pattern="^(high|medium|low)$")


class AnswerResponse(BaseModel):
    """Structured response from the LLM"""
    query_id: Optional[str] = None
    answer: str
    confidence: float = Field(ge=0, le=1, description="Confidence score between 0 and 1")
    sources_used: List[str]
    is_complete: bool
    missing_information: Optional[List[str]] = None
    enrichment_suggestions: Optional[List[EnrichmentSuggestion]] = None
    reasoning: str


class DocumentMetadata(BaseModel):
    """Metadata for uploaded documents"""
    document_id: str
    filename: str
    upload_date: datetime
    num_chunks: int
    file_size: int


class SearchContext(BaseModel):
    """Context retrieved from vector search"""
    content: str
    source: str
    relevance_score: float
    chunk_id: str

class SearchRequest(BaseModel):
    """Request model for search endpoint"""
    query: str = Field(..., description="The search query", min_length=1)
    top_k: Optional[int] = Field(5, description="Number of results to return", ge=1, le=20)

class FeedbackRequest(BaseModel):
    query_id: str
    rating: int = Field(ge=1, le=5, description="Rating from 1-5")
    feedback_text: Optional[str] = None
    query: Optional[str] = None
    answer: Optional[str] = None
    confidence: Optional[float] = None
