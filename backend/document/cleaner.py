import re
import logging 

logger =logging.getLogger(__name__)

# Normalizes extracted text for better downstream processing (like LLM chunking).
# Removes excessive whitespaces and normalizes line breaks
def clean_extracted_text(text: str) -> str:
    if not text:
        logger.debug("Received Empty String for Cleaning")
        return ""
    original_len = len(text)
    # Replacing Multiple Spaces into Single Space
    cleaned_text = re.sub(r'[ \t]+', ' ', text)
    # Replacing 3 or more consecutive newlines with exactly two (preserves paragraph breaks)
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
    cleaned_text = cleaned_text.strip()

    logger.debug(
        "Text Cleaned Original Length: %d and Cleaned Length: %d",
        original_len,
        len(cleaned_text)
    )
    return cleaned_text
