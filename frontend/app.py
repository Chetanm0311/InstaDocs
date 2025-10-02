import streamlit as st
import requests
from typing import List
import os
from pathlib import Path

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Page config
st.set_page_config(
    page_title="AI Knowledge Base",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .confidence-high {
        color: #28a745;
        font-weight: bold;
    }
    .confidence-medium {
        color: #ffc107;
        font-weight: bold;
    }
    .confidence-low {
        color: #dc3545;
        font-weight: bold;
    }
    .source-box {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
        border-left: 3px solid #1f77b4;
    }
    .enrichment-box {
        background-color: #fff3cd;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
        border-left: 3px solid #ffc107;
    }
</style>
""", unsafe_allow_html=True)


def check_backend_health():
    """Check if backend is running"""
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=2)
        return response.status_code == 200
    except:
        return False


def upload_documents(files):
    """Upload documents to backend"""
    files_data = [("files", (file.name, file, file.type)) for file in files]
    response = requests.post(f"{BACKEND_URL}/api/documents/upload", files=files_data)
    return response.json()


def search_knowledge_base(query: str, top_k: int = 5):
    """Search knowledge base and get answer"""
    response = requests.post(
        f"{BACKEND_URL}/api/search",
        json={"query": query, "top_k": top_k}
    )
    result = response.json()
    
    # Debug: Print what we received
    print(f"📥 Search result keys: {result.keys()}")
    print(f"📥 Query ID: {result.get('query_id', 'MISSING!')}")
    
    return result


def submit_feedback(query_id: str, rating: int, feedback_text: str = "", query: str = "", answer: str = "", confidence: float = 0.0):
    """Submit user feedback"""
    try:
        payload = {
            "query_id": query_id,
            "rating": int(rating),
            "feedback_text": feedback_text if feedback_text else None,
            "query": query if query else None,
            "answer": answer if answer else None,
            "confidence": float(confidence) if confidence else None
        }
        
        print(f"📤 Sending feedback to {BACKEND_URL}/api/feedback")
        print(f"   Payload: {payload}")
        
        response = requests.post(
            f"{BACKEND_URL}/api/feedback",
            json=payload,
            timeout=5
        )
        
        print(f"📥 Response status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        response.raise_for_status()  # Raise error for bad status codes
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        raise Exception(f"Failed to submit feedback: {str(e)}")
    except Exception as e:
        print(f"❌ General error: {e}")
        raise


def get_documents():
    """Get list of uploaded documents"""
    response = requests.get(f"{BACKEND_URL}/api/documents")
    return response.json()


def get_stats():
    """Get system statistics"""
    response = requests.get(f"{BACKEND_URL}/api/stats")
    return response.json()


def delete_document(doc_id: str):
    """Delete a document"""
    response = requests.delete(f"{BACKEND_URL}/api/documents/{doc_id}")
    return response.json()


# Main app
def main():
    # Header
    st.markdown('<p class="main-header">🔍 InstaDocs (Internal Knowledge Based Agent)</p>', unsafe_allow_html=True)
    st.markdown("Search & Enrichment System with Completeness Detection")
    
    # Check backend health
    if not check_backend_health():
        st.error("⚠️ Backend server is not running! Please start the backend first.")
        st.code(".\\run_backend.ps1", language="bash")
        return
    
    # Sidebar
    with st.sidebar:
        st.header("📚 Knowledge Base Manager")
        
        # Upload section
        st.subheader("Upload Documents")
        uploaded_files = st.file_uploader(
            "Choose files",
            accept_multiple_files=True,
            type=['pdf', 'txt', 'md', 'docx'],
            help="Upload PDF, TXT, MD, or DOCX files"
        )
        
        if uploaded_files and st.button("📤 Process Documents", use_container_width=True):
            with st.spinner("Processing documents..."):
                try:
                    result = upload_documents(uploaded_files)
                    
                    if result.get("uploaded"):
                        success_count = sum(1 for doc in result["uploaded"] if doc["status"] == "success")
                        st.success(f"✅ Successfully processed {success_count} document(s)")
                        
                        for doc in result["uploaded"]:
                            if doc["status"] == "success":
                                st.info(f"📄 {doc['filename']}: {doc['chunks']} chunks created")
                            else:
                                st.error(f"❌ {doc['filename']}: {doc.get('error', 'Unknown error')}")
                            
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        st.divider()
        
        # Document list
        st.subheader("📑 Uploaded Documents")
        try:
            docs_data = get_documents()
            documents = docs_data.get("documents", [])
            
            if documents:
                st.metric("Total Documents", len(documents))
                
                for doc in documents:
                    with st.expander(f"📄 {doc['filename']}"):
                        st.text(f"Chunks: {doc['num_chunks']}")
                        st.text(f"Size: {doc['file_size']} bytes")
                        st.text(f"Uploaded: {doc['upload_date'][:10]}")
                        
                        if st.button(f"🗑️ Delete", key=f"del_{doc['document_id']}"):
                            try:
                                delete_document(doc['document_id'])
                                st.success("Document deleted!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
            else:
                st.info("No documents uploaded yet")
                
        except Exception as e:
            st.error(f"Error loading documents: {str(e)}")
        
        st.divider()
        
        # # Statistics
        # if st.button("📊 View Statistics", use_container_width=True):
        #     st.session_state.show_stats = True
    
    # Main content area
    tab1, tab2 = st.tabs(["🔍 Search", "📊 Statistics"])
    
    with tab1:
        # Search interface
        st.header("Ask a Question")
        
        col1, col2 = st.columns([4, 1])
        with col1:
            query = st.text_input(
                "Enter your question",
                placeholder="e.g., What is the RAG pipeline?",
                label_visibility="collapsed"
            )
        with col2:
            top_k = st.number_input("Top Results", min_value=1, max_value=10, value=5)
        
        if st.button("🔍 Search", use_container_width=True, type="primary") and query:
            with st.spinner("Searching knowledge base..."):
                try:
                    query_clean = query.strip()
                    top_k_int = int(top_k)
                    
                    print(f"🔍 Searching with query: '{query_clean}', top_k: {top_k_int}")
                    
                    result = search_knowledge_base(query_clean, top_k_int)
                    
                    # Validate that result has query_id
                    if "query_id" not in result:
                        st.error("⚠️ Backend response missing query_id. Please check backend logs.")
                        st.json(result)  # Show what we got
                        return
                    
                    # Store result in session state for feedback
                    st.session_state.last_result = result
                    st.session_state.last_query = query
                    
                    # Display answer
                    st.markdown("### 💡 Answer")
                    st.markdown(result["answer"])
                    
                    # Confidence indicator
                    confidence = result["confidence"]
                    if confidence > 0.7:
                        conf_class = "confidence-high"
                        conf_emoji = "🟢"
                    elif confidence > 0.4:
                        conf_class = "confidence-medium"
                        conf_emoji = "🟡"
                    else:
                        conf_class = "confidence-low"
                        conf_emoji = "🔴"
                    
                    st.markdown(f"""
                    <div style='background-color: #f0f2f6; padding: 15px; border-radius: 5px; margin: 10px 0;'>
                        <p><strong>Query ID:</strong> {result['query_id']}</p>
                        <p><strong>Confidence:</strong> <span class='{conf_class}'>{conf_emoji} {confidence:.0%}</span></p>
                        <p><strong>Status:</strong> {'✅ Complete' if result['is_complete'] else '⚠️ Incomplete'}</p>
                        <p><strong>Reasoning:</strong> {result['reasoning']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Sources used
                    if result["sources_used"]:
                        st.markdown("### 📚 Sources Used")
                        for source in result["sources_used"]:
                            st.markdown(f'<div class="source-box">📄 {source}</div>', unsafe_allow_html=True)
                    
                    # Missing information
                    if not result["is_complete"] and result.get("missing_information"):
                        st.markdown("### ⚠️ Missing Information")
                        for item in result["missing_information"]:
                            st.warning(f"• {item}")
                    
                    # Enrichment suggestions
                    if result.get("enrichment_suggestions"):
                        st.markdown("### 💡 Enrichment Suggestions")
                        for suggestion in result["enrichment_suggestions"]:
                            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
                            emoji = priority_emoji.get(suggestion["priority"], "⚪")
                            
                            st.markdown(f"""
                            <div class="enrichment-box">
                                <p><strong>{emoji} {suggestion['missing_topic']}</strong> (Priority: {suggestion['priority']})</p>
                                <p>→ {suggestion['suggested_action']}</p>
                            </div>
                            """, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    st.info("Make sure you have uploaded documents first!")
        
        # Feedback section (outside the search button condition)
        if "last_result" in st.session_state:
            st.divider()
            st.markdown("### 📝 Rate This Answer")
            
            result = st.session_state.last_result
            query_text = st.session_state.get("last_query", "")
            
            # Debug display
            with st.expander("🔍 Debug Info"):
                st.json({
                    "query_id": result.get("query_id", "MISSING"),
                    "has_answer": "answer" in result,
                    "has_confidence": "confidence" in result
                })
            
            col1, col2 = st.columns([1, 3])
            
            with col1:
                rating = st.slider("Rating", 1, 5, 3, key="rating_slider")
            
            with col2:
                feedback_text = st.text_input("Optional feedback", key="feedback_text_input", placeholder="Tell us what you think...")
            
            if st.button("📤 Submit Feedback", key="submit_feedback_btn", use_container_width=True):
                try:
                    # Validate query_id exists
                    if "query_id" not in result:
                        st.error("❌ Cannot submit feedback: query_id is missing from the search result")
                        st.info("This is a backend issue. Check that llm_service.py is returning query_id properly.")
                        return
                    
                    with st.spinner("Submitting feedback..."):
                        feedback_response = submit_feedback(
                            query_id=result["query_id"],
                            rating=rating,
                            feedback_text=feedback_text,
                            query=query_text,
                            answer=result.get("answer", ""),
                            confidence=result.get("confidence", 0.0)
                        )
                        
                        st.success("✅ Thank you for your feedback! 🙏")
                        st.balloons()
                        
                        # Clear the form
                        del st.session_state.last_result
                        del st.session_state.last_query
                        st.rerun()
                        
                except KeyError as e:
                    st.error(f"❌ Missing field: {str(e)}")
                    st.info("💡 The search result is missing required data. This is a backend issue.")
                    st.json(result)  # Show what we have
                except Exception as e:
                    st.error(f"❌ Error submitting feedback: {str(e)}")
                    st.info("💡 Tip: Check that the backend server is running and check browser console (F12)")
    
    with tab2:
        # Statistics view
        st.header("System Statistics")
        
        try:
            stats = get_stats()
            
            # Overview metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Documents", stats["documents"]["total_documents"])
            
            with col2:
                st.metric("Total Chunks", stats["vector_store"]["total_chunks"])
            
            with col3:
                st.metric("Total Feedback", stats["feedback"]["total_feedback"])
            
            with col4:
                avg_rating = stats["feedback"].get("average_rating", 0)
                st.metric("Avg Rating", f"{avg_rating:.1f}/5.0")
            
            st.divider()
            
            # LLM Provider info
            st.subheader("🤖 LLM Provider")
            st.info(f"**Provider:** {stats['llm_provider']['provider_name']}")
            st.info(f"**Status:** {'✅ Available' if stats['llm_provider']['is_available'] else '❌ Not Available'}")
            
            st.divider()
            
            # Embedding model info
            st.subheader("🧠 Embedding Configuration")
            st.info(f"**Model:** {stats['vector_store']['embedding_model']}")
            st.info(f"**Collection:** {stats['vector_store']['collection_name']}")
            
            # Feedback distribution
            if stats["feedback"]["total_feedback"] > 0:
                st.divider()
                st.subheader("📊 Feedback Distribution")
                rating_dist = stats["feedback"]["rating_distribution"]
                
                # Create bar chart data
                import pandas as pd
                df = pd.DataFrame({
                    "Rating": [f"{i} ⭐" for i in range(1, 6)],
                    "Count": [rating_dist.get(str(i), 0) for i in range(1, 6)]
                })
                st.bar_chart(df.set_index("Rating"))
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Low Rated (1-2⭐)", stats["feedback"]["low_rated_count"])
                with col2:
                    st.metric("High Rated (4-5⭐)", stats["feedback"]["high_rated_count"])
                
                # Suggestions
                if stats["feedback"].get("suggestions"):
                    st.subheader("💡 Improvement Suggestions")
                    for suggestion in stats["feedback"]["suggestions"]:
                        st.warning(f"• {suggestion}")
            else:
                st.info("📭 No feedback received yet. Start searching and rate the answers!")
            
        except Exception as e:
            st.error(f"Error loading statistics: {str(e)}")


if __name__ == "__main__":
    main()
