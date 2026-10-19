import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE, override=True)

SECRET_KEY = os.getenv("FLASK_SECRET_KEY")


class Config:
    SECRET_KEY = SECRET_KEY
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")