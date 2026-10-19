import os
import numpy as np
import faiss
import pickle
import logging
from typing import Dict, Tuple, List

logger = logging.getLogger(__name__)

# BAAI/bge-small-en-v1.5 outputs embeddings with exactly 384 dimensions
EMBEDDING_DIMENSION = 384

# File Paths
INDEX_FILE = "data/vector_index/faiss_index.bin"
DOC_STORE_FILE = "data/vector_index/doc_store.pkl"

# Initializes the FAISS index and document store.
# Uses Inner Product (IndexFlatIP) which equals Cosine Similarity 
# because i normalized the embeddings in embeddings.py.
class ResumeVectorStore:
    def __init__(self):
        self.index = faiss.IndexFlatIP(EMBEDDING_DIMENSION)
        self.doc_store: Dict[int, str] = {}
        self._ensure_directories()
    def _ensure_directories(self):
        os.makedirs(os.path.dirname(INDEX_FILE), exist_ok=True)

    # Adding the Text Chunks and Corresponding Embeddings to the Texts
    def add_chunks(self, chunks: List[str], embeddings: List[List[float]]):
        if not chunks or not embeddings:
            logger.warning("Empty Chunks or Embeddings Provided to get Vector Store..")
            return 
        if len(chunks) != len(embeddings):
            raise ValueError("Mismatch Between Chunks and Embeddings..")

        # Faiss Req Numpy Array in float32
        vectors = np.array(embeddings, dtype=np.float32)
        if vectors.shape[1] != EMBEDDING_DIMENSION:
            raise ValueError(
                f"Expected embedding dimension {EMBEDDING_DIMENSION}, "
                f"but received {vectors.shape[1]}"
        )

        # Track Start_id
        start_id = self.index.ntotal

        # Adding Vectors to Faiss
        self.index.add(vectors)

        # Store the Original Text with alongside with New Faiss Id
        for i, chunk in enumerate(chunks):
            self.doc_store[start_id + i] = chunk
        logger.info("Successfully Added %d chunks in Faiss", len(chunks))

    # Searching in the Index for Most Similar Chunks to the Query
    def search(self, query_embedding: List[float], top_k: int = 3) -> List[str]:
        if self.index.ntotal == 0:
            logger.warning("Searching in Empty Faiss Index..")
            return []
        # Convert the Query to float32 numpy array and reshape for Faiss
        query_vector = np.array([query_embedding], dtype=np.float32)

        # perform the Search Based on Indices and Nearest Neighbours..
        top_k = min(top_k, self.index.ntotal)
        distances, indices = self.index.search(query_vector, top_k)

        # Retrieve the Original Text Chunks Based on the Matched ID..
        results = []
        for idx in indices[0]:
            if idx != -1 and idx in self.doc_store:
                results.append(self.doc_store[idx])

        logger.debug("Retrieved Top %d Matches from Vector Store", len(results))
        return results
    # Saves the Faiss Index and documents store in Disk
    def save_index(self):
        try:
            faiss.write_index(self.index, INDEX_FILE)
            with open(DOC_STORE_FILE, 'wb') as f:
                pickle.dump(self.doc_store, f)
            logger.info("Vector Store Successfully Saved into Disk..")
        except Exception as e:
            logger.error("Failed to Save Vector Store into Disk: %s", str(e))
            raise
    # Load the Faiss Index and Document Store into Disk..
    def load_index(self):
        if os.path.exists(INDEX_FILE) and os.path.exists(DOC_STORE_FILE):
            try:
                self.index = faiss.read_index(INDEX_FILE)
                with open(DOC_STORE_FILE, 'rb') as f:
                    self.doc_store = pickle.load(f)
                logger.info("Vector Store Loaded. Total vector: %d", self.index.ntotal)
            except Exception as e:
                logger.exception("Failed to Store Existing Vector Store")
                raise
        else:
            logger.info("No existing vector store found. Starting fresh.")