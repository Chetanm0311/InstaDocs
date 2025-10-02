import os
from typing import List, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from langchain.schema import Document

# from dotenv import load_dotenv
class EmbeddingService:
    """Service for generating embeddings and managing vector store"""
    
    def __init__(self, db_path: str = "./storage/vector_db", collection_name: str = "documents"):
        # load_dotenv(".env.normal",override=True)
        self.db_path = db_path
        self.collection_name = collection_name
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            print(f"Loaded existing collection: {collection_name}")
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            print(f"Created new collection: {collection_name}")
        
        # Initialize embedding model
        self.use_openai = False
        self.openai_client = None
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if openai_key and openai_key.startswith("skt-"):
            try:
                from openai import OpenAI
                # Initialize OpenAI client (newer version doesn't use proxies parameter)
                self.openai_client = OpenAI(api_key=openai_key)
                
                # Test the connection with a simple embedding
                test_response = self.openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input="test"
                )
                
                self.use_openai = True
                print("✅ Using OpenAI embeddings (text-embedding-3-small)")
            except ImportError:
                print("⚠️ OpenAI library not installed. Installing sentence-transformers...")
                self._init_sentence_transformers()
            except Exception as e:
                print(f"⚠️ OpenAI init failed: {e}")
                print("Falling back to sentence-transformers (local)")
                self._init_sentence_transformers()
        else:
            print("ℹ️ No valid OpenAI API key found")
            self._init_sentence_transformers()
    
    def _init_sentence_transformers(self):
        """Initialize local sentence-transformers model"""
        try:
            
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            print("✅ Using sentence-transformers embeddings (all-MiniLM-L6-v2) - Works offline!")
        except Exception as e:
            print(f"❌ Failed to initialize sentence-transformers: {e}")
            raise
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        if self.use_openai and self.openai_client:
            try:
                response = self.openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input=text
                )
                return response.data[0].embedding
            except Exception as e:
                print(f"OpenAI embedding failed: {e}. Falling back to local model.")
                # Fall back to sentence-transformers if OpenAI fails
                if not hasattr(self, 'embedding_model'):
                    self._init_sentence_transformers()
                self.use_openai = False
                embedding = self.embedding_model.encode(text, convert_to_numpy=True)
                return embedding.tolist()
        else:
            # load_dotenv(".env.normal",override=True)
            # Use sentence-transformers
            embedding = self.embedding_model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
    
    def embed_and_store(self, chunks: List[Document], document_id: str):
        """Generate embeddings and store chunks in vector database"""
        embeddings = []
        documents = []
        metadatas = []
        ids = []
        
        print(f"📊 Processing {len(chunks)} chunks for document {document_id}...")
        
        for idx, chunk in enumerate(chunks):
            # Generate embedding
            embedding = self._generate_embedding(chunk.page_content)
            embeddings.append(embedding)
            
            # Prepare data
            documents.append(chunk.page_content)
            metadatas.append({
                "doc_id": document_id,
                "chunk_id": str(idx),
                "source": chunk.metadata.get("source", document_id),
                "page": str(chunk.metadata.get("page", "unknown"))
            })
            ids.append(f"{document_id}_{idx}")
            
            # Progress indicator
            if (idx + 1) % 10 == 0:
                print(f"  Processed {idx + 1}/{len(chunks)} chunks...")
        
        # Add to collection
        self.collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"✅ Stored {len(chunks)} chunks for document {document_id}")
    
    def search(self, query: str, top_k: int = 5) -> List[dict]:
        """Search for relevant chunks using vector similarity
        
        Steps:
        1. Convert query text to embedding vector
        2. Compare query vector with all stored document vectors
        3. Find top_k most similar chunks using cosine similarity
        4. Convert distance to similarity score (0-1, where 1 is best)
        5. Return formatted results with metadata
        """
        # Generate query embedding
        query_embedding = self._generate_embedding(query)
        
        # Query collection using vector similarity search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        context = []
        if results["documents"] and len(results["documents"][0]) > 0:
            for doc, metadata, distance in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            ):
                # Convert distance to similarity score
                # Cosine distance: 0 = identical, 2 = opposite
                # Similarity: 1 = perfect match, 0 = no match
                similarity = 1 - (distance / 2)
                
                context.append({
                    "content": doc,
                    "source": metadata.get("source", "unknown"),
                    "relevance_score": similarity,
                    "chunk_id": metadata.get("chunk_id", "unknown"),
                    "doc_id": metadata.get("doc_id", "unknown"),
                    "page": metadata.get("page", "unknown")
                })
        
        return context
    
    def delete_document_chunks(self, document_id: str):
        """Delete all chunks associated with a document"""
        # Get all IDs for this document
        results = self.collection.get(
            where={"doc_id": document_id}
        )
        
        if results["ids"]:
            self.collection.delete(ids=results["ids"])
            print(f"🗑️ Deleted {len(results['ids'])} chunks for document {document_id}")
        else:
            print(f"⚠️ No chunks found for document {document_id}")
    
    def get_collection_stats(self) -> dict:
        """Get statistics about the vector database"""
        count = self.collection.count()
        return {
            "total_chunks": count,
            "collection_name": self.collection_name,
            "embedding_model": "OpenAI (text-embedding-3-small)" if self.use_openai else "sentence-transformers (all-MiniLM-L6-v2)"
        }
