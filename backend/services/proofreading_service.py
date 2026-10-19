import logging
from typing import Dict, Any, Union
from backend.ai.vector_store_manager import get_shared_vector_store
from backend.ai.rag import run_rag_pipeline
logger = logging.getLogger(__name__)

# Scans the resume for grammatical errors, weak phrasing, and structural issues.
class ProofReadingService:
    def __init__(self):
        logger.info("Initializing Interview Service..")
        self.vector_store = get_shared_vector_store()
        # try:
        #     self.vector_store.load_index()
        #     if self.vector_store.index.ntotal == 0:
        #         logger.warning("Vector store is empty.. unable to process Perfect..")
        # except Exception as e:
        #     logger.warning("Vector Index Not Found for Proof Reading Services")
        #     raise
    def proofread(self) -> Union[str, Dict[str, Any]]:
        # Executes the proofreading analysis on the candidate's resume
        logger.info("Executing the Proof Reading Service..")
        query = (
            "Act as an elite executive resume copyeditor. "
            "Review the provided resume context carefully.\n\n"

            "Identify:\n"
            "1. Grammatical errors.\n"
            "2. Spelling mistakes.\n"
            "3. Awkward or unclear wording.\n"
            "4. Excessive passive voice.\n"
            "5. Weak or repetitive action verbs.\n"
            "6. Weak resume bullet points.\n"
            "7. Inconsistent professional language.\n"
            "8. Structural or readability issues when supported "
            "by the provided context.\n\n"

            "For every issue you identify, provide a specific "
            "correction or improvement.\n\n"

            "For weak bullet points, provide an improved version "
            "that is concise, impactful, and achievement-oriented. "
            "Do not invent metrics, achievements, technologies, "
            "or experience that are not present in the resume.\n\n"

            "Use only the supplied resume context. "
            "Do not invent candidate information."
        )
        try:
            response = run_rag_pipeline(
                user_query=query,
                vector_store=self.vector_store,
                service_type="career_coach", 
                expected_format="text",
                top_k=5 
            )
            logger.info("Resume proofreading completed successfully.")
            return response
        except Exception as e:
            logger.exception("Resume proofreading failed.")
            return {"error": "Failed to proofread the resume.", "details": str(e)}