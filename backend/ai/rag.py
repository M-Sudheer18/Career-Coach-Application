import logging
from typing import Dict, Any, Union
# Import all
from backend.ai.gemini_client import GeminiClient
from backend.ai.vector_store import ResumeVectorStore
from backend.ai.prompts import build_rag_prompt, get_system_instructions
from backend.ai.response_parser import process_ai_output
from backend.ai.retriever import retrieve_relevant_chunks
logger = logging.getLogger(__name__)


# End to End Pipeline for Rag
# user_query: The question or task requested by the user.
# vector_store: The active FAISS database containing the resume chunks.
# service_type: The UI tool being used (e.g., 'cover_letter', 'resume_scorer').
# expected_format: 'text' or 'json', dictating how the output is parsed.
# top_k: Number of relevant resume chunks to fetch from the database.
def run_rag_pipeline(
        user_query: str,
        vector_store: ResumeVectorStore,
        service_type: str = "career_coach",
        expected_format: str = "text",
        top_k: int = 3
) -> Union[str, Dict[str, Any]]:
    logger.info("Starting RAG Pipeline for Service: %s", service_type)
    if not user_query or not user_query.strip():
        logger.warning("Rag Aborted: User query is Empty")
        raise ValueError("User Query Can't be Empty")
    if vector_store is None:
        logger.error("RAG aborted: Vector store is None.")
        raise ValueError("Vector store cannot be None.")
    if top_k <= 0:
        raise ValueError("top_k must be greater than 0.")

    try:
        # Search for Sprecific persona for requested Tool
        logger.debug("Fetching Instructions..")
        sys_prompt = get_system_instructions(service_type)

        # Initialize Ai Client for Specific Persona
        logger.debug("Initializing Gemini Client..")
        llm_client = GeminiClient(
            system_instructions=sys_prompt
        )

        # Retrieve the relevant resume data from FAISS
        logger.debug("Retrieving Context from Vector Store..")
        retrieved_chunks = retrieve_relevant_chunks(
            query=user_query,
            vector_store=vector_store,
            top_k=top_k
        )
        if not retrieved_chunks:
            logger.warning("No relevant resume chunks found for query.")

        # Combine Both data and query into One prompt..
        logger.debug("Building Grounded Prompt..")
        final_prompt = build_rag_prompt(
            user_query=user_query,
            retrieved_chunks=retrieved_chunks
        )

        # Increase Token Limit if user want full document..
        max_tokens = 2048 if service_type == "cover_letter" else 1024

        # Send to Gemini...
        logger.debug("Send the Prompt to gemini..")
        raw_response = llm_client.generate_response(
            prompt=final_prompt,
            max_tokens=max_tokens
        )
        print("=== RAW GEMINI OUTPUT START ===")
        print(repr(raw_response))
        print("=== RAW GEMINI OUTPUT END ===")

        # Clean and validate the output before returning it to the user
        logger.debug("Cleaning and Validating AI Output")
        final_output = process_ai_output(
            raw_response=raw_response,
            expected_format=expected_format
        )
        logger.info("RAG Pipeline Successfully Completed.")
        return final_output
    except Exception as e:
        logger.exception("The RAG pipeline encountered a critical failure.")
        # Safe fallback for backend doesn't completely crash the UI
        if expected_format == "json":
            return {"error": "The AI service encountered an error.", "details": str(e)}
        return f"An error occurred while generating the AI response: {str(e)}"