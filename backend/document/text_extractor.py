# import os
import fitz # pymupdf
import logging

logger = logging.getLogger(__name__)

# Opens a PDF and extracts raw text page by page.
# Handles basic encryption and permissions gracefully.

def extract_text_from_pdf(file_path: str) -> str:
    extracted_text = ""
    logger.debug("Opening Pdf for Text Extraction: %s",file_path)

    try:
        with fitz.open(file_path) as doc:
            # Resumes are Rarely password protected or restricted.
            if doc.is_encrypted:
                logger.warning(
                    "Pdf is Encripted: %s"
                    "Trying to Extract..", 
                    file_path
                )
                if not doc.authenticate(""):
                    raise PermissionError(
                        f"Unable to authenticate the Encripted pdf: {file_path}"
                    )
            # Extract the Text Page by Page
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_text = page.get_text("text")
                extracted_text += page_text + "\n\n"
        logger.debug(
            "Successfully Extracted the raw text from %s",
            file_path
        )
        return extracted_text
    except Exception as e:
        logger.exception(
            "Failed to Extract the text from pdf: %s",
            file_path
        )
        raise