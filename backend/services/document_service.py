import os
import uuid
from pathlib import Path
from typing import List
from datetime import datetime
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredWordDocumentLoader
from langchain.schema import Document
import json


class DocumentService:
    """Service for document upload, processing, and management"""
    
    def __init__(self, upload_dir: str = "./storage/documents"):
        self.upload_dir = Path(upload_dir).resolve()  # Convert to absolute path
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.upload_dir / "metadata.json"
        self.metadata = self._load_metadata()
        
        # Text splitter configuration
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )
    
    def _load_metadata(self) -> dict:
        """Load document metadata from file"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print("Corrupted metadata file, starting fresh")
                return {}
        return {}
    
    def _save_metadata(self):
        """Save document metadata to file"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, default=str, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving metadata: {e}")

    def _get_loader(self, file_path: Path):
        """Get appropriate document loader based on file extension"""
        extension = file_path.suffix.lower()
        
        # Ensure absolute path
        absolute_path = file_path.resolve()

        print(f"Loading file: {absolute_path}")

        if extension == '.pdf':
            return PyPDFLoader(str(absolute_path))
        elif extension in ['.txt', '.md']:
            return TextLoader(str(absolute_path), encoding='utf-8')
        elif extension == '.docx':
            return UnstructuredWordDocumentLoader(str(absolute_path))
        else:
            raise ValueError(f"Unsupported file type: {extension}")
    
    async def save_file(self, file_content: bytes, filename: str) -> tuple[str, Path]:
        """Save uploaded file to storage"""
        # Generate unique document ID
        try:
            # Generate unique document ID
            doc_id = str(uuid.uuid4())
            
            # Create document directory
            doc_dir = self.upload_dir / doc_id
            doc_dir.mkdir(exist_ok=True)
            
            # Save file with proper encoding handling
            file_path = doc_dir / filename

            print(f"Saving file: {file_path}")

            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Verify file was saved
            if not file_path.exists():
                raise IOError(f"File not saved properly: {file_path}")
            
            print(f"File saved: {file_path.stat().st_size} bytes")
            
            return doc_id, file_path
            
        except Exception as e:
            print(f"Error saving file: {e}")
            raise
    
    
    def process_document(self, file_path: Path) -> List[Document]:
        """Load and split document into chunks"""
        try:
            # Ensure we have absolute path
            absolute_path = file_path.resolve()
            
            # Verify file exists
            if not absolute_path.exists():
                raise FileNotFoundError(f"File not found: {absolute_path}")
            
            print(f"Processing document: {absolute_path.name}")
            
            # Load document
            loader = self._get_loader(absolute_path)
            documents = loader.load()
            
            if not documents:
                raise ValueError(f"No content loaded from {absolute_path.name}")
            
            print(f"Loaded {len(documents)} page(s)")
            
            # Split into chunks
            chunks = self.text_splitter.split_documents(documents)
            
            print(f"Split into {len(chunks)} chunks")
            
            return chunks
            
        except Exception as e:
            print(f"Error processing document {file_path.name}: {e}")
            raise
    
    
    async def save_and_process(self, file_content: bytes, filename: str) -> tuple[str, List[Document]]:
        """Save file and process it into chunks"""
        try:
            # Save file
            doc_id, file_path = await self.save_file(file_content, filename)
            
            # Process document
            chunks = self.process_document(file_path)
            
            # Store metadata
            self.metadata[doc_id] = {
                "document_id": doc_id,
                "filename": filename,
                "upload_date": datetime.now().isoformat(),
                "num_chunks": len(chunks),
                "file_size": file_path.stat().st_size,
                "file_path": str(file_path.resolve())  # Store absolute path
            }
            self._save_metadata()

            print(f"Document processed: {filename} → {len(chunks)} chunks")

            return doc_id, chunks
            
        except Exception as e:
            print(f"Error in save_and_process: {e}")
            # Clean up on error
            if 'doc_id' in locals():
                try:
                    self.delete_document(doc_id)
                except:
                    pass
            raise
    
    def get_all_documents(self) -> List[dict]:
        """Get list of all uploaded documents"""
        return list(self.metadata.values())
    
    def get_document_by_id(self, doc_id: str) -> dict:
        """Get document metadata by ID"""
        return self.metadata.get(doc_id)
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete document and its metadata"""
        if doc_id in self.metadata:
            try:
                # Delete files
                doc_dir = self.upload_dir / doc_id
                if doc_dir.exists():
                    import shutil
                    shutil.rmtree(doc_dir)
                    print(f"🗑️ Deleted document directory: {doc_dir}")
                
                # Remove metadata
                del self.metadata[doc_id]
                self._save_metadata()
                
                print(f"✅ Document {doc_id} deleted successfully")
                return True
                
            except Exception as e:
                print(f"❌ Error deleting document: {e}")
                return False
        else:
            print(f"⚠️ Document {doc_id} not found in metadata")
            return False
    
    def get_stats(self) -> dict:
        """Get document storage statistics"""
        total_size = sum(doc.get('file_size', 0) for doc in self.metadata.values())
        total_chunks = sum(doc.get('num_chunks', 0) for doc in self.metadata.values())
        
        return {
            "total_documents": len(self.metadata),
            "total_size_bytes": total_size,
            "total_chunks": total_chunks,
            "storage_path": str(self.upload_dir)
        }
