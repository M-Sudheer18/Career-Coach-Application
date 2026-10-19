import logging
from typing import Dict, Any, Union
from backend.ai.vector_store_manager import get_shared_vector_store
from backend.ai.rag import run_rag_pipeline
logger = logging.getLogger(__name__)

# Generation of Cover Letters
class CoverLetterService:
    def __init__(self):
        logger.info("Initiazing Cover Letter Service..")
        self.vector_store = get_shared_vector_store()
        # try:
        #     self.vector_store.load_index()
        #     if self.vector_store.index.ntotal == 0:
        #         logger.warning(
        #             "vector Store is Empty"
        #             "Cover letter Generation may not work Perfectly.."
        #         )
        # except Exception as e:
        #     logger.exception("Unable to Load the Index from Vector Store..")
        #     raise

    # Generaetes a Cover Letter Based on the Job Description...
    def generate(self, job_description: str) -> Union[str, Dict[str, Any]]:
        logger.info("Cover Letter Processing Generation Request..")
        if not job_description or not job_description.strip():
            return {"error": "Job Description can't be Empty..."}
        job_description = job_description.strip()
        query = (
            "Please write a professional, ATS-friendly cover letter "
            "for the following job description: \n\n"
            "JOB DESCRIPTION:\n"
            f"{job_description}"
        )
        try:
            response = run_rag_pipeline(
                user_query=query,
                vector_store=self.vector_store,
                service_type="cover_letter",
                expected_format="text",
                top_k=5
            )
            logger.info(
                    "Cover letter generated successfully."
            )
            return response
        except Exception as e:
            logger.exception("Cover Letter Genaration Failed..")
            return {
                "error": "Unable to return the Cover Letter"
                # "details": str(e)
            }