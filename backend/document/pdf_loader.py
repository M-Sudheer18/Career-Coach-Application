import os
# import re
import logging 
# import fitz  #pymupdf

# Import the specialized functions from your other modules
from backend.document.text_extractor import extract_text_from_pdf
from backend.document.cleaner import clean_extracted_text

logger = logging.getLogger(__name__)

# %s → string/any object (str(value))
# %d → integer
# %f → float
# Loads a PDF resume from the given file path, 
# extracts its text using PyMuPDF,
# and cleans the output for optimal AI/LLM processing.
def load_resume(file_path: str) -> str:
    logger.info("Loading the Resume: %s", file_path)
    if not os.path.exists(file_path):
        logger.error("File Not Found: %s", file_path)
        raise FileNotFoundError(f"File does not exist: {file_path}")
    try:
        # Extract the raw text
        raw_text = extract_text_from_pdf(file_path)
        # Clean and normalize the text
        final_text = clean_extracted_text(raw_text)

        if not final_text:
            logger.warning("Extraction is Completed but after Cleaning No Text Found in %s", file_path)
        else:
            logger.debug(
                "Extracted and Cleaned the %d Characters and %s text", 
                len(final_text), 
                file_path
            )
        return final_text
    except Exception as e:
        logger.exception("Failed to extract text from %s.", file_path)
        raise