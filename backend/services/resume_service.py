import os
import logging
from typing import Dict, Any
from backend.document.pdf_loader import load_resume
from backend.document.chunker import chunk_text
from backend.ai.embeddings import get_embeddings_batch
from backend.ai.vector_store import ResumeVectorStore
from backend.ai.vector_store_manager import (
    get_shared_vector_store,
    set_shared_vector_store
)
logger = logging.getLogger(__name__)

# This Handles ingestion, processing and Vectorization of resume
class ResumeService:
    def __init__(self):
        self.vector_store = get_shared_vector_store()
    # End to End Processing of Document Pipeline
    def process_resume(self, file_path: str) -> Dict[str, Any]:
        logger.info("Resume Servie Started Processing: %s", file_path)
        if not file_path or not os.path.exists(file_path):
            logger.error("File Not Found, Verify the file path: %s", file_path)
            return {
                "status": "error",
                "message": "File not Found.."
            }
        
        try:
            # Extract
            logger.debug("Extracting Text from Pdf...")
            cleaned_text = load_resume(file_path)
            if not cleaned_text or not cleaned_text.strip():
                return{
                    "error": "Uploaded Resume is appears to be Empty.."
                }

            # Chunks
            logger.debug("Chunking the Text")
            chunks = chunk_text(
                cleaned_text,
                chunk_size=5,
                overlap=1
            )
            # Embedding the text)
            if not chunks:
                return {
                    "status": "error",
                    "message": "No meaningful chunks were generated from the resume."
                }
            logger.info("Generated %d resume chunks", len(chunks))

            # Embeddings
            logger.debug("Generate Embeddings..")
            embeddings = get_embeddings_batch(chunks)
            if not embeddings:
                raise ValueError("Failed to Generate Resume Embeddings..")
            if len(embeddings) != len(chunks):
                raise ValueError(
                    "Number of embeddings does not match number of chunks."
                )
            logger.info("Generated %d Embeddings", len(embeddings))

            # Create a fresh Vector Store for the new resume
            logger.debug("Creating fresh FAISS Vector Store...")
            self.vector_store = ResumeVectorStore()
            self.vector_store.add_chunks(
                chunks,
                embeddings
            )
            logger.info(
                "Added %d chunks to FAISS.",
                len(chunks)
            )

            # Save
            logger.debug("Saving FAISS Vector Store..")
            self.vector_store.save_index()

            # Update shared Vector Store
            set_shared_vector_store(self.vector_store)
            logger.info("Shared Vector Store updated successfully.")
            logger.info(
                "Process Success and total %d chunks Stored", 
                len(chunks)
            )
            return {
                "status": "success",
                "message": "resume parsed Successfully..",
                "chunks_processed": len(chunks)
            }
        except Exception as e:
            logger.exception("A Error Occurred while processing Document...")
            return {
                "status": "error",
                "message": "Error Occurred Dusring Resume Processing..",
                "details": str(e)
            }