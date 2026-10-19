import logging
from typing import List
from backend.ai.embeddings import get_embedding
from backend.ai.vector_store import ResumeVectorStore

logger = logging.getLogger(__name__)

# Retrieves the most semantically relevant resume chunks for a given user query
# query: The natural language question from the user.
# vector_store: An active, loaded instance of ResumeVectorStore.
# top_k: The maximum number of text chunks to return.
def retrieve_relevant_chunks(
        query: str,
        vector_store: ResumeVectorStore,
        top_k: int = 3
) -> List[str]:
    # Strict with Input Validation 
    if not query or not query.strip():
        logger.warning("Empty Query is Provided to Retriever Returns None")
        return []
    if vector_store is None:
        logger.critical("No Vector store is Provided to Retriever to get the Data")
        raise ValueError("Vector Can't be None..")
    if top_k <= 0:
        raise ValueError("top_k must be greater than 0.")
    try:
        logger.debug("Generation Query Embedding for Retrieval..")
        query_embedding = get_embedding(query)
        if not query_embedding:
            logger.warning("Query Embedding is Not Successful for query: %s", query)
            return []
        logger.debug("Searching Vector Store for Top %d Chunks relevant to Query..", top_k)

        # Faiss Similarity Search 
        results = vector_store.search(
            query_embedding,
            top_k=top_k
        )
        safe_query_log = query[:50] + ("..." if len(query) > 50 else "")
        logger.info(
            "Retrived %d Relevant Chunks for Query %s",
            len(results),
            safe_query_log
        )
        return results
    except Exception as e:
        logger.exception("Failed to Retrieve the Chunks from Data..")
        raise