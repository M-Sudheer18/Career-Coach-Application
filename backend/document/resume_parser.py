import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Generates a strict prompt instructing the LLM to return only valid JSON
def get_extraction_prompt(resume_text: str) -> str:
    return f"""
        You are an expert AI technical recruiter.
        Extract structured information from the provided resume.
        Return ONLY a valid JSON object.
        Do not wrap the response in markdown or ```json blocks.
        Use exactly these keys:
        {{
            "candidate_name": "Full name or null",
            "email": "Email address or null",
            "phone": "Phone number or null",
            "primary_role": "Most relevant role based on the resume or null",
            "top_skills": ["Up to 8 core technical skills"],
            "years_experience": "Number of years or 'Entry-Level' or null"
        }}
        IMPORTANT:
        - Use only information supported by the resume.
        - Do not invent missing information.
        - If information is unavailable, return null.
        - Do not add additional keys.
        RESUME TEXT:
        {resume_text}
        """
# Prompts an LLM to extract structured metadata from the resume text and returns it as a parsed Python dictionary
def parse_llm_response(raw_response: str) -> Dict[str, Any]:
    if not raw_response:
        raise ValueError("LLM returned an empty response.")
    try:
        extracted_data = json.loads(raw_response)
        if not isinstance(extracted_data, dict):
            raise ValueError("LLM response is not a JSON object.")
        logger.info(
                "Successfully parsed structured resume data for candidate: %s",
                extracted_data.get("candidate_name", "Unknown")
            )
        return extracted_data
    except json.JSONDecodeError:
        logger.exception("LLM failed to return valid JSON.")
        logger.debug("Raw LLM response: %s", raw_response)
        raise

def extract_resume_metadata(cleaned_text: Dict) -> Dict[str, Any]:
    # Takes cleaned text, builds the prompt, calls the AI, and parses the response.
    if not cleaned_text:
        logger.error("No text provided to the resume parser.")
        raise ValueError("Cleaned text is empty.")
    logger.debug("Generating extraction prompt...")
    prompt = get_extraction_prompt(cleaned_text)

    logger.debug("Sending prompt to AI module...")
    # PRODUCTION CALL (Uncomment when backend/ai/llm_client.py is ready):
    # raw_llm_response = generate_ai_response(prompt)
    raise NotImplementedError(
        "AI connection is not yet implemented. "
        "Build backend/ai/gemini_client.py to execute this prompt."
    )