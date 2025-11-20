"""
PDF Processing Module
Handles PDF upload, text extraction, and chunking for large documents
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from queue import Queue

from .config import (
    GOOGLE_API_KEY,
    MAX_PDF_PAGES,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    UPLOAD_DIR,
    VECTOR_STORE_PATH,
)

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Handles PDF processing operations with multithreading support."""

    def __init__(self, max_workers: int = 4):
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=GOOGLE_API_KEY
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
        )
        self.metadata_file = UPLOAD_DIR / "metadata.json"
        self._load_metadata()
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.processing_status = {}
        self.status_lock = threading.Lock()

    def _load_metadata(self):
        """Load document metadata from file."""
        if self.metadata_file.exists():
            with open(self.metadata_file, "r") as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {}

    def _save_metadata(self):
        """Save document metadata to file."""
        with open(self.metadata_file, "w") as f:
            json.dump(self.metadata, f, indent=2)

    def validate_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Validate PDF file and return metadata.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary with validation results and metadata
        """
        try:
            if not os.path.exists(file_path):
                return {"valid": False, "error": "File not found"}

            if not file_path.lower().endswith(".pdf"):
                return {"valid": False, "error": "File is not a PDF"}

            reader = PdfReader(file_path)
            num_pages = len(reader.pages)

            if num_pages > MAX_PDF_PAGES:
                return {
                    "valid": False,
                    "error": f"PDF has {num_pages} pages, exceeds maximum of {MAX_PDF_PAGES}",
                }

            # Calculate file hash
            with open(file_path, "rb") as f:
                file_hash = hashlib.md5(f.read()).hexdigest()

            return {
                "valid": True,
                "num_pages": num_pages,
                "file_size": os.path.getsize(file_path),
                "file_hash": file_hash,
            }
        except Exception as e:
            logger.error(f"Error validating PDF: {str(e)}")
            return {"valid": False, "error": str(e)}

    def _extract_page_text(self, page_data: tuple) -> tuple:
        """Extract text from a single page (thread-safe)."""
        page_num, page = page_data
        try:
            text = page.extract_text()
            return (page_num, text.strip() if text else "")
        except Exception as e:
            logger.error(f"Error extracting text from page {page_num + 1}: {str(e)}")
            return (page_num, "")

    def extract_text(self, file_path: str, document_id: str = None) -> List[str]:
        """
        Extract text from PDF file using multithreading.
        
        Args:
            file_path: Path to the PDF file
            document_id: Optional document ID for progress tracking
            
        Returns:
            List of text strings, one per page
        """
        try:
            reader = PdfReader(file_path)
            num_pages = len(reader.pages)
            pages_text = [""] * num_pages

            # Update status
            if document_id:
                with self.status_lock:
                    self.processing_status[document_id] = {
                        "stage": "extracting",
                        "progress": 0,
                        "total": num_pages
                    }

            # Process pages in parallel
            page_data = [(i, page) for i, page in enumerate(reader.pages)]
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_page = {executor.submit(self._extract_page_text, data): data[0] 
                                for data in page_data}
                
                completed = 0
                for future in as_completed(future_to_page):
                    page_num, text = future.result()
                    pages_text[page_num] = text
                    completed += 1
                    
                    # Update progress
                    if document_id:
                        with self.status_lock:
                            if document_id in self.processing_status:
                                self.processing_status[document_id]["progress"] = completed

            return pages_text
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise

    def chunk_documents(self, pages_text: List[str], document_id: str) -> List[Document]:
        """
        Split text into chunks and create Document objects.
        
        Args:
            pages_text: List of text from each page
            document_id: Unique identifier for the document
            
        Returns:
            List of Document objects
        """
        documents = []
        
        for page_num, page_text in enumerate(pages_text):
            if page_text.strip():
                doc = Document(
                    page_content=page_text,
                    metadata={
                        "document_id": document_id,
                        "page_number": page_num + 1,
                        "source": "pdf",
                    }
                )
                documents.append(doc)

        # Split documents into chunks
        chunked_docs = self.text_splitter.split_documents(documents)
        
        logger.info(f"Created {len(chunked_docs)} chunks from {len(pages_text)} pages")
        return chunked_docs

    def create_vector_store(self, documents: List[Document], document_id: str) -> Chroma:
        """
        Create vector store from documents.
        
        Args:
            documents: List of Document objects
            document_id: Unique identifier for the document
            
        Returns:
            Chroma vector store
        """
        try:
            collection_name = f"pdf_{document_id}"
            vector_store = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                collection_name=collection_name,
                persist_directory=VECTOR_STORE_PATH,
            )
            
            logger.info(f"Created vector store for document {document_id}")
            return vector_store
        except Exception as e:
            logger.error(f"Error creating vector store: {str(e)}")
            raise

    def get_vector_store(self, document_id: str) -> Optional[Chroma]:
        """
        Retrieve existing vector store for a document.
        
        Args:
            document_id: Unique identifier for the document
            
        Returns:
            Chroma vector store or None if not found
        """
        try:
            collection_name = f"pdf_{document_id}"
            vector_store = Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                persist_directory=VECTOR_STORE_PATH,
            )
            return vector_store
        except Exception as e:
            logger.error(f"Error retrieving vector store: {str(e)}")
            return None

    def upload_pdf(self, file_path: str, document_id: str) -> Dict[str, Any]:
        """
        Upload and validate a PDF file.
        
        Args:
            file_path: Path to the PDF file
            document_id: Unique identifier for the document
            
        Returns:
            Dictionary with upload results
        """
        # Validate PDF
        validation = self.validate_pdf(file_path)
        if not validation["valid"]:
            return validation

        # Copy file to upload directory
        dest_path = UPLOAD_DIR / f"{document_id}.pdf"
        
        if file_path != str(dest_path):
            import shutil
            shutil.copy2(file_path, dest_path)

        # Store metadata
        self.metadata[document_id] = {
            "file_path": str(dest_path),
            "num_pages": validation["num_pages"],
            "file_size": validation["file_size"],
            "file_hash": validation["file_hash"],
            "status": "uploaded",
            "processed": False,
        }
        self._save_metadata()

        return {
            "success": True,
            "document_id": document_id,
            "num_pages": validation["num_pages"],
            "message": "PDF uploaded successfully",
        }

    def process_pdf(self, document_id: str) -> Dict[str, Any]:
        """
        Process a PDF: extract text, chunk, and create vector store with multithreading.
        
        Args:
            document_id: Unique identifier for the document
            
        Returns:
            Dictionary with processing results
        """
        if document_id not in self.metadata:
            return {"success": False, "error": "Document not found"}

        doc_meta = self.metadata[document_id]
        file_path = doc_meta["file_path"]

        try:
            # Initialize status
            with self.status_lock:
                self.processing_status[document_id] = {
                    "stage": "starting",
                    "progress": 0,
                    "total": 100
                }

            # Extract text with progress tracking
            logger.info(f"Extracting text from {document_id}")
            pages_text = self.extract_text(file_path, document_id)

            # Update status
            with self.status_lock:
                self.processing_status[document_id] = {
                    "stage": "chunking",
                    "progress": 0,
                    "total": 100
                }

            # Chunk documents
            logger.info(f"Chunking documents for {document_id}")
            chunked_docs = self.chunk_documents(pages_text, document_id)

            # Update status
            with self.status_lock:
                self.processing_status[document_id] = {
                    "stage": "vectorizing",
                    "progress": 0,
                    "total": 100
                }

            # Create vector store
            logger.info(f"Creating vector store for {document_id}")
            vector_store = self.create_vector_store(chunked_docs, document_id)

            # Update metadata
            self.metadata[document_id]["status"] = "processed"
            self.metadata[document_id]["processed"] = True
            self.metadata[document_id]["num_chunks"] = len(chunked_docs)
            self._save_metadata()

            # Clear status
            with self.status_lock:
                if document_id in self.processing_status:
                    del self.processing_status[document_id]

            return {
                "success": True,
                "document_id": document_id,
                "num_pages": doc_meta["num_pages"],
                "num_chunks": len(chunked_docs),
                "message": "PDF processed successfully",
            }
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            self.metadata[document_id]["status"] = "error"
            self.metadata[document_id]["error"] = str(e)
            self._save_metadata()
            
            # Clear status
            with self.status_lock:
                if document_id in self.processing_status:
                    del self.processing_status[document_id]
            
            return {"success": False, "error": str(e)}

    def get_processing_status(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get current processing status for a document."""
        with self.status_lock:
            return self.processing_status.get(document_id)

    def list_documents(self) -> List[Dict[str, Any]]:
        """
        List all uploaded documents.
        
        Returns:
            List of document metadata
        """
        return [
            {
                "document_id": doc_id,
                **meta
            }
            for doc_id, meta in self.metadata.items()
        ]


# Global processor instance
pdf_processor = PDFProcessor()
