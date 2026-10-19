import logging
import uuid

from flask import (
    Blueprint,
    request,
    jsonify,
    render_template,
    session
)
from backend.services.interview_service import InterviewService
logger = logging.getLogger(__name__)

interview_bp = Blueprint(
    "interview",
    __name__,
    url_prefix="/interview"
)

_interview_service = None

def get_interview_service():
    global _interview_service

    if _interview_service is None:
        logger.info("Lazy loading Interview Service..")
        _interview_service = InterviewService()
    return _interview_service

def get_session_id():
    # Get or Create a Unique Session Id for the Current Browser..
    if "interview_session_id" not in session:
        session["interview_session_id"] = str(uuid.uuid4())
    return session["interview_session_id"]

# HTML Route "GET"
@interview_bp.route("/", methods=["GET"])
def interview_page():
    """Renders the AI Technical Interview Page."""
    return render_template("interview/index.html")

# API Action Route "POST"
@interview_bp.route("/api/state", methods=["GET"])
def interview_state():
    """Returns the current interview state."""
    try:
        session_id = get_session_id()
        svc = get_interview_service()

        state = svc.get_state(
            session_id=session_id
        )
        return jsonify(state), 200
    except Exception as e:
        logger.exception(
            "Failed to Load an Insterview State.."
        )
        return jsonify({
            "error": "Unable to load interview State"
        }), 500

# Start AI interview Generation
@interview_bp.route("/api/chat", methods=["POST"])
def ai_interview_chat():
    # Starts ai interview Generation in the Background
    data = request.get_json(silent=True) or {}
    candidate_answer = data.get(
        "candidate_answer",
        ""
    )
    if (
        not isinstance(candidate_answer, str)
        or not candidate_answer.strip()
    ):
        return jsonify({
            "error": "Candidate answer is Required.."
        }), 400
    try:
        session_id = get_session_id()
        svc = get_interview_service()
        result = svc.start_generation(
            session_id=session_id,
            candidate_answer=candidate_answer.strip()
        )
        if result.get("error"):
            return jsonify(result), 409
        return jsonify(result), 202
    except Exception:
        logger.exception(
            "Interview API Failed.."
        )
        return jsonify({
            "error": "Unable to Process the Interview chat"
        }), 500

# Start New Interview
@interview_bp.route("/api/new", methods=["POST"])
def new_interview():
    """Clears the current interview and starts a new one."""
    try:
        session_id = get_session_id()
        svc = get_interview_service()
        state = svc.reset_interview(
            session_id=session_id
        )
        return jsonify(state), 200
    except Exception:
        logger.exception(
            "Failed to start a new interview."
        )
        return jsonify({
            "error": "Unable to start a new interview."
        }), 500