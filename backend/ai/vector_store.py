
import os
import numpy as np
import faiss
import pickle
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

EMBEDDING_DIMENSION = 768

INDEX_FILE = "data/vector_index/faiss_index.bin"
DOC_STORE_FILE = "data/vector_index/doc_store.pkl"


class ResumeVectorStore:
    def __init__(self):
        self.index = faiss.IndexFlatIP(EMBEDDING_DIMENSION)
        self.doc_store: Dict[int, str] = {}
        self._ensure_directories()

    def _ensure_directories(self):
        os.makedirs(os.path.dirname(INDEX_FILE), exist_ok=True)

    def add_chunks(
        self,
        chunks: List[str],
        embeddings: List[List[float]],
    ):
        if not chunks or not embeddings:
            logger.warning("Empty chunks or embeddings provided.")
            return

        if len(chunks) != len(embeddings):
            raise ValueError("Mismatch between chunks and embeddings.")

        vectors = np.asarray(embeddings, dtype=np.float32)

        if vectors.ndim != 2:
            raise ValueError("Embeddings must be a 2D array.")

        if vectors.shape[0] != len(chunks):
            raise ValueError("Embedding count does not match chunk count.")

        if vectors.shape[1] != EMBEDDING_DIMENSION:
            raise ValueError(
                f"Expected embedding dimension {EMBEDDING_DIMENSION}, "
                f"but received {vectors.shape[1]}."
            )

        start_id = self.index.ntotal
        self.index.add(vectors)

        for i, chunk in enumerate(chunks):
            self.doc_store[start_id + i] = chunk

        logger.info("Successfully added %d chunks to FAISS.", len(chunks))

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 3,
    ) -> List[str]:
        if not query_embedding:
            logger.warning("Received an empty query embedding.")
            return []

        if self.index.ntotal == 0:
            logger.warning("Searching an empty FAISS index.")
            return []

        query_vector = np.asarray(
            [query_embedding],
            dtype=np.float32,
        )

        if query_vector.shape[1] != EMBEDDING_DIMENSION:
            raise ValueError(
                f"Expected query dimension {EMBEDDING_DIMENSION}, "
                f"but received {query_vector.shape[1]}."
            )

        top_k = min(top_k, self.index.ntotal)
        _, indices = self.index.search(query_vector, top_k)

        results = []

        for idx in indices[0]:
            if idx != -1 and idx in self.doc_store:
                results.append(self.doc_store[idx])

        logger.debug("Retrieved %d matches from FAISS.", len(results))
        return results

    def save_index(self):
        try:
            self._ensure_directories()

            faiss.write_index(self.index, INDEX_FILE)

            with open(DOC_STORE_FILE, "wb") as file:
                pickle.dump(self.doc_store, file)

            logger.info("FAISS index and document store saved.")

        except Exception:
            logger.exception("Failed to save the vector store.")
            raise

    def load_index(self):
        if not (
            os.path.exists(INDEX_FILE)
            and os.path.exists(DOC_STORE_FILE)
        ):
            logger.info("No existing vector store found. Starting fresh.")
            return

        try:
            loaded_index = faiss.read_index(INDEX_FILE)

            if loaded_index.d != EMBEDDING_DIMENSION:
                logger.warning(
                    "Existing FAISS index has dimension %d; expected %d. "
                    "The old index is incompatible with Gemini embeddings. "
                    "Resetting it; upload the resume again to rebuild it.",
                    loaded_index.d,
                    EMBEDDING_DIMENSION,
                )

                self.index = faiss.IndexFlatIP(EMBEDDING_DIMENSION)
                self.doc_store = {}
                self.save_index()
                return

            with open(DOC_STORE_FILE, "rb") as file:
                loaded_doc_store = pickle.load(file)

            self.index = loaded_index
            self.doc_store = loaded_doc_store

            logger.info(
                "Vector store loaded successfully. Total vectors: %d",
                self.index.ntotal,
            )

        except Exception:
            logger.exception("Failed to load the vector store.")
            raise
