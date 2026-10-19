import os
import logging
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, project_root)

from backend.utils.logger import setup_logging
from backend.document.pdf_loader import load_resume
from backend.document.chunker import chunk_text

# Logging Configuration
setup_logging()
logger = logging.getLogger(__name__)

# Passes a sample PDF through the extraction, cleaning, and chunking pipeline.
def run_pipeline_test(pdf_path: str):
    print("*"*50)
    print("STARTING PIPELINE TEST")
    print("*"*50)

    logger.info("Initializing Test File: %s", pdf_path)
    if not os.path.exists(pdf_path):
        logger.error("File Not Exists: %s", pdf_path)
        print("Place a Valid Pdf to Test the Process..")
        return 
    try:
        # Load and Clean 
        print("\n Loading and Cleaning the Pdf..")
        cleaned_text = load_resume(pdf_path)

        if not cleaned_text:
            print("\n Extraction Completed But Text Not Found...!")
            return 
        print(f"✅ Success! Extracted {len(cleaned_text)} characters.")
        print("Preview of the first 250 characters:")
        print("-" * 40)
        print(cleaned_text[:250] + "...\n")
        print("-" * 40)

        # Chunk the Text
        print("\n Chunking the Text(Resume Aware)...")
        chunks = chunk_text(
            cleaned_text,
            chunk_size=5,
            overlap=1
        )
        print(f"✅ Success! Generated {len(chunks)} overlapping chunks.")

        # Verify the Output
        print("\n Inspecting the first 3 Chunks..")
        for i, chunk in enumerate(chunks[:3]):
            print(f"\n--Chunk {i + 1}--")
            print(chunk)
        print("\n" + "*"*50)
        print("🎉 PIPELINE TEST COMPLETED SUCCESSFULLY")
        print("*"*50)

    except Exception as e:
        logger.exception("The pipeline test encountered a fatal error.")
        print(f"\n❌ PIPELINE FAILED: Check the terminal logs above for the stack trace.")

if __name__ =="__main__":
    TEST_FILE_PATH = "data/raw_uploads/Resume_Sudheer.pdf"
    os.makedirs(os.path.dirname(TEST_FILE_PATH), exist_ok=True)
    run_pipeline_test(TEST_FILE_PATH)