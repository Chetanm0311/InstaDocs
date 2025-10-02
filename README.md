# InstaDocs (Knowledge Base Search & Enrichment Agent)

A RAG (Retrieval-Augmented Generation) system that allows users to upload documents, search them in natural language, get AI-generated answers, and detect when information is incomplete with enrichment suggestions.

## 🌟 Features

- **Document Upload & Processing**: Support for PDF, TXT, MD, and DOCX files
- **Natural Language Search**: Ask questions in plain language
- **AI-Generated Answers**: Intelligent responses using RAG pipeline
- **Completeness Detection**: AI detects when information is missing or uncertain
- **Enrichment Suggestions**: System suggests how to fill knowledge gaps
- **Structured JSON Output**: Answer, confidence score, sources, and missing info
- **User Feedback System**: Rate answers to improve the system over time
- **Local-First**: Works with ChromaDB and sentence-transformers (no API key required)
- **OpenAI Integration**: Optional upgrade with OpenAI API for better results

## 🏗️ Architecture

```
User → Streamlit UI → FastAPI Backend → RAG Pipeline → ChromaDB
                                              ↓
                                      LLM (GPT-3.5-Turbo/Gemini/Fallback)
```
## 📊 Trade Off due to 24 hr constrains
### 1. Vector Database
- **Chosen**: Local ChromaDB
- **TradeOff**: chromadb is not as feature-rich or scalable as some commercial vector DBs (Pinecone, Weaviate) but is easy to set up and works well for small to medium datasets.

### 2. File Storage
- **Chosen**: Local filesystem storage
- **TradeOff**: Simple to implement but lacks advanced features like versioning, access control, and scalability of cloud storage solutions.

### 3. Hosting
- **Chosen**: Localhost deployment
- **TradeOff**: Easiest for development and testing but not suitable for production use. Cloud deployment (AWS, GCP, Azure) would be needed for scalability and reliability.

### 4. System Reliability
- **Chosen**: Basic error handling and logging
- **TradeOff**: Sufficient for development but lacks robust monitoring, backups, alerting, and failover mechanisms needed for production systems.

## What can be improved for production?
- switch to pinecone, use index sharing and configure replication
- for file storage, migrate to AWS S3, setup CDN and implement versioning
- for llm providers, switch to reliable OpenAI and implement rate limiting and caching
- for feedback storage, migrate to PostgreSQL or MongoDB
- frontend, use react and add user authentication
- add logging, setup alerting and containerize with docker
  

## 📦 Installation

### 1. Clone or Navigate to Project

```powershell
cd c:\InstaDocs
```

### 2. Create Virtual Environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

**or** 

```python
python setup.py
```

### 4. Configure Environment (Optional)

```powershell
copy .env.example .env
```

Edit `.env` to add your OpenAI API key (optional):
```
OPENAI_API_KEY=sk-your-key-here
GOOGLE_API_KEY="your-google-api-key-here"
BACKEND_HOST=localhost
BACKEND_PORT=8000
UPLOAD_DIR=./storage/documents
VECTOR_DB_DIR=./storage/vector_db
```

**Note**: The system works without OpenAI using sentence-transformers locally!

## 🚀 Running the Application

### Step 1: Start the Backend Server

```powershell
python -m uvicorn backend.main:app --reload --host localhost --port 8000
```

Backend will be available at: `http://localhost:8000`
API docs at: `http://localhost:8000/docs`

### Step 2: Start the Streamlit Frontend (New Terminal)

Open a new PowerShell window:

```powershell
cd c:\InstaDocs
.\venv\Scripts\Activate.ps1
streamlit run frontend/app.py
```

Frontend will open automatically in your browser at: `http://localhost:8501`

## 📖 Usage

### 1. Upload Documents
- Click "Choose files" in the sidebar
- Select PDF, TXT, MD, or DOCX files
- Click "📤 Process Documents"
- Wait for processing (documents will be chunked and embedded)

### 2. Ask Questions
- Enter your question in the search box
- Click "🔍 Search"
- View the AI-generated answer with:
  - Confidence score (🟢 high, 🟡 medium, 🔴 low)
  - Sources used
  - Completeness status
  - Missing information (if incomplete)
  - Enrichment suggestions

### 3. Rate Answers
- Use the rating slider (1-5 stars)
- Optionally provide feedback text
- Click "Submit Feedback"

### 4. View Statistics
- Click "📊 Statistics" tab
- See document count, chunks, feedback ratings
- View improvement suggestions

## 🛠️ Project Structure

```
InstaDocs/
├── backend/
│   ├── models/
│   │   └── schemas.py              # Pydantic models
|   ├── providers
|   |   ├── gemini_provider.py      # gemini api
|   |   ├── base_provider.py        # Abstract Base class for providers
|   |   ├── openai_provider.py      # openai api
|   |   ├── provider_factory.py     # provider factory
|   |   ├── fallback_provider.py    # fallback provider
│   ├── services/
│   │   ├── document_service.py     # Document processing
│   │   ├── embedding_service.py    # Vector embeddings & ChromaDB
│   │   ├── llm_service.py          # LLM answer generation
│   │   └── feedback_service.py     # User feedback collection
│   └── main.py                     # FastAPI application
├── frontend/
│   └── app.py                      # Streamlit UI
├── storage/                        # Auto-created
│   ├── documents/                  # Uploaded files
│   ├── vector_db/                  # ChromaDB storage
│   └── feedback.json               # User feedback
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## 🔧 Configuration

### Environment Variables (.env)

```env
# Optional: OpenAI API Key for better results
OPENAI_API_KEY=your_openai_api_key_here

# Backend settings
BACKEND_HOST=localhost
BACKEND_PORT=8000

# Storage paths
UPLOAD_DIR=./storage/documents
VECTOR_DB_DIR=./storage/vector_db
```

### Default Settings (No API Key Required)

- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2) - Works offline!
- **Vector DB**: ChromaDB (local persistent storage)
- **LLM**: Rule-based fallback (or OpenAI GPT-4 if API key provided)

## 📊 API Endpoints

- `GET /` - Health check
- `POST /api/documents/upload` - Upload documents
- `POST /api/search` - Search and get answer
- `POST /api/feedback` - Submit feedback
- `GET /api/documents` - List all documents
- `DELETE /api/documents/{id}` - Delete document
- `GET /api/stats` - System statistics
- `GET /api/feedback/stats` - Feedback statistics
- `GET /api/feedback/recent` - Recent feedback

Full API docs: `http://localhost:8000/docs`

## 🎯 Key Features Explained

### Completeness Detection

The system analyzes if it has enough information to answer:
- **Confidence > 0.7**: Complete answer with high confidence
- **Confidence 0.4-0.7**: Partial answer, may need more info
- **Confidence < 0.4**: Incomplete, missing critical information

### Enrichment Suggestions

When information is incomplete, the system suggests:
- **Missing Topic**: What specific information is needed
- **Suggested Action**: How to obtain that information
- **Priority**: high/medium/low urgency

### Structured Output

All responses follow a consistent JSON schema:
```json
{
  "answer": "...",
  "confidence": 0.85,
  "sources_used": ["doc1.pdf"],
  "is_complete": true,
  "missing_information": null,
  "enrichment_suggestions": null,
  "reasoning": "..."
}
```

## 🧪 Testing

Example questions to try:
1. Upload a txt about Synthetic IT-Related Knowledge Items(https://www.kaggle.com/datasets/dkhundley/synthetic-it-related-knowledge-items)
2. Ask: "how to setup mobile device for company email"

## 🚀 Performance Tips

1. **Chunk Size**: Default 800 tokens with 200 overlap (adjust in `document_service.py`)
2. **Top-K Results**: Default 5 (increase for broader context)
3. **OpenAI API**: Use for best results with structured outputs
4. **Local Mode**: Works great with sentence-transformers for privacy/offline use

## 🔐 Security Notes

- API keys should be in `.env` (not committed to git)
- Add authentication for production use
- Validate file uploads (size limits, virus scanning)

## 📝 Future Enhancements

- [ ] Auto-enrichment from external sources (Wikipedia, APIs)
- [ ] Multi-modal support (images, tables)
- [ ] Fine-tuning based on feedback
- [ ] Advanced re-ranking algorithms
- [ ] User authentication and multi-tenancy
- [ ] Dockerize for easy deployment
