import logging
from backend.ai.vector_store import ResumeVectorStore
logger = logging.getLogger(__name__)

_shared_vector_store = None
def get_shared_vector_store() -> ResumeVectorStore:
    """ Laods in Lazy way to store the single shared instance in the Faiss"""
    global _shared_vector_store
    if _shared_vector_store is None:
        logger.info("Initializing the shared Vector Store into Faiss..")
        _shared_vector_store = ResumeVectorStore()
        try:
            _shared_vector_store.load_index()
            if _shared_vector_store.index.ntotal == 0:
                logger.warning("Shared Vector is Loaded but it is Empty..")
            else:
                logger.info(
                    "Shared Vector store loading with %d vectors",
                    _shared_vector_store.index.ntotal
                )
        except Exception as e:
            logger.warning(
                "Could not load Vector index on startup." 
                "Has a resume been uploaded yet?"
            )
    return _shared_vector_store

def set_shared_vector_store(
    vector_store: ResumeVectorStore
) -> None:
    """Replace the shared Vector Store with a newly processed one."""
    global _shared_vector_store
    _shared_vector_store = vector_store
    logger.info(
        "Shared Vector Store replaced successfully."
    )

def reload_shared_vector_store():
    """refresh of the vector store in RAM (used after a new PDF upload)"""
    global _shared_vector_store
    logger.info("Reloading the shared Faiss Vector store after the update..")
    new_vector_store = ResumeVectorStore()
    try:
        new_vector_store.load_index()
        if new_vector_store.index.ntotal == 0:
            logger.warning("Reloaded Vector Store is empty.")
        else:
            logger.info(
                "Reloaded Vector Store with %d vectors.",
                new_vector_store.index.ntotal
            )
        _shared_vector_store = new_vector_store
    except Exception as e:
        logger.exception("Failed to reloaded the updated vector store..")
        raise

    return _shared_vector_store