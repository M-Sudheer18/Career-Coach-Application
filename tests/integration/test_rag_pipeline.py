import sys
import os
import logging

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, project_root)

from backend.utils.logger import setup_logging
from backend.document.pdf_loader import load_resume
from backend.document.chunker import chunk_text
from backend.ai.embeddings import get_embeddings_batch
from backend.ai.vector_store import ResumeVectorStore
from backend.ai.rag import run_rag_pipeline

from dotenv import load_dotenv
load_dotenv()
key = os.getenv("GEMINI_API_KEY")


setup_logging()
logger = logging.getLogger(__name__)

def test_full_architecture(pdf_path: str):
    print("Starting to test End to End Pipeline..")
    if not os.path.exists(pdf_path):
        print(f"Error Please place a Valid Pdf FIle: {pdf_path}")
        return
    try:
        # Document Parsing
        print("Step 1: Extracting and Chunking Resume..")
        cleaned_text = load_resume(pdf_path)
        chunks = chunk_text(cleaned_text, chunk_size=5, overlap=1)
        print(f"Successfully Generated the {len(chunks)} from text..")

        # Embeddings 
        print(f"Step 2: Getting Embeddings..")
        embeddings = get_embeddings_batch(chunks)
        print(f"Successfully Generated the {len(embeddings)} Embeddings..")

        # Vector Databases
        print("Step 3: Populating Faiss Vector Store..")
        vector_store = ResumeVectorStore()
        # for testing i dont want to Save it 
        vector_store.add_chunks(chunks, embeddings)
        print(f"Vector Store is loaded and Ready..")

        # Rag
        print("Step 4: Querying the AI..")
        user_query = "What are the core technical skills listed in this resume? Give me a brief summary."
        print(f"User: {user_query}")
        final_answer = run_rag_pipeline(
            user_query=user_query,
            vector_store=vector_store,
            service_type="career_coach",
            expected_format="text",
            top_k=3
        )
        print("AI Response..")
        print(final_answer)
        print("Pipeline Tested Successfully..")
    except Exception as e:
        logger.exception("The Test got a Error...")
        print("Pipeline Failed..")

if __name__ == "__main__":
    TEST_FILE_PATH = os.path.join(
        project_root,
        "data",
        "raw_uploads",
        "Resume_Sudheer.pdf"
    )
    test_full_architecture(TEST_FILE_PATH)