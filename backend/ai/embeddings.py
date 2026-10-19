import logging
from typing import List
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
# Loading Model
try:
    logger.info("Loading Embedding Model: %s..", EMBEDDING_MODEL)
    model = SentenceTransformer(EMBEDDING_MODEL)
    logger.info("Model Loaded Successfully...")
except Exception as e:
    logger.error("Failed to Load the Model: %s", e)
    raise

# Convert the Text into Vector Embedding
def get_embedding(text: str) -> List[float]:
    if not text or not text.strip():
        logger.warning("Received Empty Text..")
        return []
    try:
        logger.debug(
            f"Generating Embeddings for text length of {len(text)}"
        )
        # Encode Method Gives Numpy Array we Have to Convert that into Python List
        embedding = model.encode(text, normalize_embeddings=True)
        return embedding.tolist()
    except Exception as e:
        logger.error("Unable to Create Embedding: %s", e)
        raise

# Generating a embeddings for text Chunks Efficiently to get better for chunker.py
def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    if not texts:
        logger.warning("Received an Empty Texts..")
        return []
    try:
        logger.info("Generating the Embeddings for length of: %d", len(texts))
        embeddings = model.encode(texts, normalize_embeddings=True)
        logger.debug("Successfully Generated Embeddings: %d", len(embeddings))
        return [emb.tolist() for emb in embeddings]
    except Exception as e:
        logger.exception("Failed to Generate / Create Batch Local Embeddings...")
        raise