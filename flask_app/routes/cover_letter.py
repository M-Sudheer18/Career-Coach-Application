import logging
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from flask import (
    Blueprint,
    request,
    jsonify,
    session,
    render_template
)
from backend.services.cover_letter_service import CoverLetterService
logger = logging.getLogger(__name__)

# Blueprint for Cover Letter
cover_letter_bp = Blueprint(
    "cover_letter",
    __name__,
    url_prefix="/career"
)

_cover_letter_service = None

def get_cover_letter_service():
    global _cover_letter_service
    if _cover_letter_service is None:
        logger.info(
            "Lazy Loading Cover Letter Service.."
        )
        _cover_letter_service = CoverLetterService()
    return _cover_letter_service

def get_session_id():
    """Get or create a unique session ID for the current browser."""
    if "cover_letter_session_id" not in session:
        session["cover_letter_session_id"] = str(uuid.uuid4())
    return session["cover_letter_session_id"]

class CoverLetterState:
    """Stores Cover Letter state for the lifetime of the Flask process."""
    def __init__(self):
        self._states = {}
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(
            max_workers=4,
            thread_name_prefix="cover-letter-generation"
        )

    def _create_default_state(self):
        return {
            "job_description": "",
            "status": "idle",
            "job_id": None,
            "error": None,
            "result": None
        }

    def _get_or_create_state(self, session_id):
        with self._lock:
            if session_id not in self._states:
                self._states[session_id] = (
                    self._create_default_state()
                )
            return self._states[session_id]

    def get_state(self, session_id):
        """Return the current Cover Letter state."""
        state = self._get_or_create_state(
            session_id
        )
        with self._lock:
            return {
                "job_description": state["job_description"],
                "status": state["status"],
                "job_id": state["job_id"],
                "error": state["error"],
                "result": state["result"]
            }

    def reset(self, session_id):
        """Clear the current Cover Letter state."""
        with self._lock:
            self._states[session_id] = (
                self._create_default_state()
            )
            return dict(
                self._states[session_id]
            )
    def start_generation(
        self,
        session_id,
        job_description
    ):
        """Start Cover Letter generation in the background."""
        if not job_description or not job_description.strip():
            return {
                "error": "Job description can't be Empty..."
            }
        job_description = job_description.strip()
        state = self._get_or_create_state(
            session_id
        )

        with self._lock:
            if state["status"] == "generating":
                return {
                    "error": (
                        "A Cover Letter is already "
                        "being generated."
                    ),
                    "job_id": state["job_id"]
                }
            job_id = str(uuid.uuid4())
            state["job_description"] = job_description
            state["status"] = "generating"
            state["job_id"] = job_id
            state["error"] = None
            state["result"] = None
        logger.info(
            "Starting background Cover Letter generation. "
            "job_id=%s",
            job_id
        )

        self._executor.submit(
            self._generate,
            session_id,
            job_id,
            job_description
        )
        return {
            "job_id": job_id,
            "status": "generating"
        }

    def _generate(
        self,
        session_id,
        job_id,
        job_description
    ):
        """Perform Cover Letter generation in background."""
        try:
            service = get_cover_letter_service()
            result = service.generate(
                job_description = job_description
            )
            if (
                isinstance(result, dict) and result.get("error")
            ):
                with self._lock:
                    state = self._states.get(
                        session_id
                    )
                    if (
                        state and state["job_id"] == job_id
                    ):
                        state["status"] = "error"
                        state["error"] = result.get(
                            "error",
                            "cover Letter Generation Failed"
                        )
                        state["result"] = None
                return

            with self._lock:
                state = self._states.get(
                    session_id
                )
                if not state or state["job_id"] != job_id:
                    return
                state["status"] = "completed"
                state["result"] = str(result)
                state["error"] = None

            logger.info(
                "Cover Letter generation completed successfully. "
                "job_id=%s", job_id
            )
        except Exception:
            logger.exception(
                "Background Cover Letter generation failed. "
                "job_id=%s", job_id
            )

            with self._lock:
                state = self._states.get(
                    session_id
                )
                if state and state["job_id"] == job_id:
                    state["status"] = "error"
                    state["error"] = ("Cover Letter generation failed.")
                    state["result"] = None

_cover_letter_state = CoverLetterState()

# Cover Letter Page 
@cover_letter_bp.route("/cover_letter", methods=["GET"])
def cover_letter_page():
    return render_template("career/cover_letter.html")

# Get Current Cover Letter State
@cover_letter_bp.route("/api/cover_letter/state", methods = ["GET"])
def cover_letter_state():
    try:
        session_id = get_session_id()
        state = _cover_letter_state.get_state(
            session_id=session_id
        )
        return jsonify(state), 200
    except Exception:
        logger.exception(
            "Failed to load Cover Letter state."
        )
        return jsonify({
            "error": "Unable to load Cover Letter state."
        }), 500

# Start Cover LetterGeneration
@cover_letter_bp.route("/api/cover_letter", methods=["POST"])
def api_generate_cover_letter():
    """Start Cover Letter generation in the background."""
    data = request.get_json(silent=True) or {}
    job_description = data.get("job_description", "")

    if not isinstance(job_description, str) or not job_description.strip():
        return jsonify({
            "error": "Job description is required.."
        }), 400

    try:
        session_id = get_session_id()
        result = _cover_letter_state.start_generation(
            session_id = session_id,
            job_description = job_description.strip()
        )
        if result.get("error"):
            return jsonify(result), 400
        return jsonify(result), 202
    except Exception:
        logger.exception(
            "Cover Letter API failed."
        )
        return jsonify({
            "error": (
                "Unable to process the Cover Letter API."
            )
        }), 500

# Start New Cover Letter
@cover_letter_bp.route("/api/cover_letter/new", methods=["POST"])
def new_cover_letter():
    """Clear the current Cover Letter state."""
    try:
        session_id = get_session_id()
        state = _cover_letter_state.reset(
            session_id=session_id
        )
        return jsonify(state), 200
    except Exception:

        logger.exception(
            "Failed to start a new Cover Letter."
        )

        return jsonify({
            "error": (
                "Unable to start a new Cover Letter."
            )
        }), 500