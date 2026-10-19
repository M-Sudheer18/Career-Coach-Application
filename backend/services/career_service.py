import logging
from typing import Dict, Union, Any
from backend.ai.vector_store_manager import get_shared_vector_store
from backend.ai.rag import run_rag_pipeline
logger = logging.getLogger(__name__)

# The bridge between the web API and the RAG engine
class CareerService:
    VALID_SERVICES = {
        "career_coach",
        "resume_scorer",
    }
    def __init__(self):
        logger.info("Initializing Career Service and loading Vector store into RAM...")
        self.vector_store = get_shared_vector_store()
    
    # Takes a Raw input from frontend, formats it into a precise prompts and triggers the Rag Pipeline..
    def handle_ai_request(self, service_type:str, user_input: str) -> Union[str, Dict[str, Any]]:
        logger.info("Handling Frontend Requests for service: %s", service_type)
        if not user_input or not user_input.strip():
            return {"error": "User input can't be Empty.."}
        user_input = user_input.strip()

        if service_type not in self.VALID_SERVICES:
            return {
                "error": f"Unsupported service type: {service_type}"
            }
        if service_type == "resume_scorer":
            expected_format = "text"
            top_k = 5
            query = (
                "Please evaluate my resume against the following "
                "job description and return the exact requested "
                "JSON format:\n\n"
                f"{user_input}"
            )
       
        elif service_type == "career_coach":
            expected_format = "text"
            query = user_input
            top_k = 3
        try:
            # Trigger Rag Pipeline..
            response = run_rag_pipeline(
                user_query=query,
                vector_store=self.vector_store,
                service_type=service_type,
                expected_format=expected_format,
                top_k=top_k
            )
            logger.info(
                    "Career Service request completed successfully."
                )
            return response
        except Exception as e:
            logger.exception("Career Service Encountered with a Failure..")
            if expected_format == "json":
                return {
                    "error": "An error occurred while processing your request."
                }
            return "I apologize, but I encountered an error processing your request. Please try again."