import os
import sys
import logging

# Project Root — must be configured before project imports
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from flask import Flask
from flask_app.config import Config

from routes.main import main_bp
from routes.coach import coach_bp
from routes.career import career_bp
from routes.resume import resume_bp
from routes.interview import interview_bp
from routes.cover_letter import cover_letter_bp
from routes.resume_scorer import resume_scorer_bp
from routes.recommendation import recommendation_bp

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger(__name__)


# Creating Flask Application
app = Flask(__name__)
app.config.from_object(Config)


# Blueprint Registration
app.register_blueprint(main_bp)
app.register_blueprint(career_bp)
app.register_blueprint(resume_bp)
app.register_blueprint(interview_bp)
app.register_blueprint(cover_letter_bp)
app.register_blueprint(resume_scorer_bp)
app.register_blueprint(recommendation_bp)
app.register_blueprint(coach_bp)


if __name__ == "__main__":
    logger.info("Starting Resume App")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )