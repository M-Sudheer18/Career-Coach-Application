import os
from pathlib import Path

from dotenv import load_dotenv

# ReZume project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load the root .env file
load_dotenv(PROJECT_ROOT / ".env")

# Read the Flask API URL from the environment
API_BASE_URL = os.getenv("FLASK_API_BASE_URL", "").strip().rstrip("/")

if not API_BASE_URL:
    raise RuntimeError(
        "FLASK_API_BASE_URL is missing. "
        "Configure it in the project-root .env file or deployment environment."
    )