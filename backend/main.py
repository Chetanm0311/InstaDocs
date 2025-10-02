from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os
from dotenv import load_dotenv

from backend.services.document_service import DocumentService
from backend.services.embedding_service import EmbeddingService
from backend.services.llm_service import LLMService
from backend.services.feedback_service import FeedbackService
from backend.models.schemas import AnswerResponse, FeedbackRequest, DocumentMetadata, SearchRequest

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="InstaDocs Knowledge Base API",
    description="RAG-based knowledge base with completeness detection",
    version="1.0.0"
)

# CORS middleware for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
document_service = DocumentService(
    upload_dir=os.getenv("UPLOAD_DIR", "./storage/documents")
)
embedding_service = EmbeddingService(
    db_path=os.getenv("VECTOR_DB_DIR", "./storage/vector_db")
)
llm_service = LLMService()
feedback_service = FeedbackService()


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "message": "AI Knowledge Base API is running",
        "version": "1.0.0"
    }


@app.post("/api/documents/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    """
    Upload and process multiple documents
    
    Supported formats: PDF, TXT, MD, DOCX
    """
    results = []
    errors = []
    
    for file in files:
        try:
            # Read file content
            content = await file.read()
            
            # Save and process document
            doc_id, chunks = await document_service.save_and_process(content, file.filename)
            
            # Generate embeddings and store in vector DB
            embedding_service.embed_and_store(chunks, doc_id)
            
            results.append({
                "document_id": doc_id,
                "filename": file.filename,
                "chunks": len(chunks),
                "status": "success"
            })
            
        except Exception as e:
            errors.append({
                "filename": file.filename,
                "error": str(e)
            })
    
    return {
        "uploaded": results,
        "errors": errors,
        "total_success": len(results),
        "total_failed": len(errors)
    }


@app.post("/api/search", response_model=AnswerResponse)
async def search_knowledge_base(request: SearchRequest):
    """
    Search knowledge base and get AI-generated answer with completeness check
    
    Args:
        query: Natural language question
        top_k: Number of relevant chunks to retrieve (default: 5)
    """
    if not request.query or len(request.query.strip()) == 0:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        # Retrieve relevant context
        context = embedding_service.search(request.query, request.top_k)
        
        # Generate answer with completeness assessment
        answer = llm_service.generate_answer(request.query, context)
        print(f"✅ Search completed - Query ID: {answer.query_id}")
        return answer
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@app.post("/api/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """
    Submit feedback on answer quality
    
    Used to improve the system over time
    """
    try:
        print(f"📥 Received feedback request: {feedback.dict()}")
        request = feedback_service.store_feedback(
            query_id=feedback.query_id,
            rating=feedback.rating,
            feedback_text=feedback.feedback_text,
            query=feedback.query,
            answer=feedback.answer,
            confidence=feedback.confidence
        )
        return {"status": "success", "feedback": feedback,"message": "Feedback recorded successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error storing feedback: {str(e)}")

@app.get("/api/feedback/stats")
async def get_feedback_stats():
    """Get feedback statistics"""
    try:
        stats = feedback_service.get_feedback_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/feedback/recent")
async def get_recent_feedback(limit: int = 10):
    """Get recent feedback entries"""
    try:
        feedback = feedback_service.get_recent_feedback(limit)
        return {"feedback": feedback}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents")
async def list_documents():
    """List all uploaded documents with metadata"""
    try:
        documents = document_service.get_all_documents()
        return {"documents": documents, "total": len(documents)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving documents: {str(e)}")


@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and its embeddings"""
    try:
        # Delete from vector store
        embedding_service.delete_document_chunks(document_id)
        
        # Delete from document storage
        success = document_service.delete_document(document_id)
        
        if success:
            return {"status": "success", "message": f"Document {document_id} deleted"}
        else:
            raise HTTPException(status_code=404, detail="Document not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")


@app.get("/api/stats")
async def get_stats():
    """Get system statistics"""
    try:
        vector_stats = embedding_service.get_collection_stats()
        documents = document_service.get_all_documents()
        feedback_stats = feedback_service.get_feedback_stats()
        llm_provider = llm_service.get_provider_info()
        
        return {
            "vector_store": vector_stats,
            "documents": {
                "total_documents": len(documents),
                "documents": documents
            },
            "feedback": feedback_stats,
            "llm_provider": llm_provider
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving stats: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("BACKEND_HOST", "localhost")
    port = int(os.getenv("BACKEND_PORT", 8000))
    
    print(f"Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
