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
from backend.services.career_service import CareerService
logger = logging.getLogger(__name__)

resume_scorer_bp = Blueprint(
    "resume_scorer",
    __name__,
    url_prefix="/career"
)

# Career Service
_career_service = None
def get_career_service():
    global _career_service
    if _career_service is None:
        logger.info("Lazy Loading Career Service..")
        _career_service = CareerService()
    return  _career_service

# Session ID
def get_session_id():
    if "resume_scorer_session_id" not in session:
        session["resume_scorer_session_id"] = str(uuid.uuid4())
    return session["resume_scorer_session_id"]

# RESUME SCORER STATE MANAGER
class ResumeScorerState:
    def __init__(self):
        self._states = {}
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(
            max_workers=4,
            thread_name_prefix="resume-scorer-generation"
        )

    # Default State
    def _create_default_state(self):
        return {
            "job_description": "",
            "status": "idle",
            "job_id": None,
            "error": None,
            "result": None
        }

    # Get or Create State
    def _get_or_create_state(self, session_id):
        with self._lock:
            if session_id not in self._states:
                self._states[session_id] = (
                    self._create_default_state()
                )
            return self._states[session_id]

    # Get Current State
    def get_state(self, session_id):
        state = self._get_or_create_state(session_id)
        with self._lock:
            return {
                "job_description": state["job_description"],
                "status": state["status"],
                "job_id":state["job_id"],
                "error": state["error"],
                "result": state["result"]
            }

    # Reset / New Score
    def reset(self, session_id):
        with self._lock:
            self._states[session_id] = (
                self._create_default_state()
            )
            return dict(self._states[session_id])

    # Start Background Generation
    def start_generation(
        self,
        session_id,
        job_description
    ):
        if not job_description or not job_description.strip():
            return { "error": "Job Description can't be Empty.." }
        job_description = job_description.strip()
        state = self._get_or_create_state(session_id)
        with self._lock:
            # Prevent duplicate generation
            if state["status"] == "generating":
                return {
                    "error": (
                        "A Resume Score is already "
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
                "Starting background Resume Score generation. "
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

    # Background Generation Worker
    def _generate(
        self,
        session_id,
        job_id,
        job_description
    ):
        try:
            service = get_career_service()
            result = service.handle_ai_request(
                service_type="resume_scorer",
                user_input=job_description
            )
            # Service returned an error
            if isinstance(result, dict) and result.get("error"):
                with self._lock:
                    state = self._states.get(session_id)
                    if state and state["job_id"] == job_id:
                        state["status"] = "error"
                        state["error"] = result.get(
                            "error",
                            "Resume Score Generation Failed."
                        )
                        state["result"] = None
                return

            # Successful Generation
            with self._lock:
                state = self._states.get(session_id)
                if not state or state["job_id"] != job_id:
                    return
                state["status"] = "completed"
                state["result"] = result
                state["error"]  = None
            logger.info(
                "Resume Score generation completed successfully. "
                "job_id=%s", job_id
            )
        except Exception:
            logger.exception(
                "Background Resume Score generation failed. "
                "job_id=%s",
                job_id
            )
            with self._lock:
                state = self._states.get(session_id)
                if state and state["job_id"] == job_id:
                    state["status"] = "error"
                    state["error"] = (
                        "Resume Score generation failed."
                    )
                    state["result"] = None

# GLOBAL STATE MANAGER
_resume_score_state = ResumeScorerState()

# PAGE ROUTE
@resume_scorer_bp.route("/scorer", methods=["GET"])
def resume_score_page():
    return render_template("career/resume_scorer.html")

# State API
@resume_scorer_bp.route("/api/score/state", methods=["GET"])
def resume_scorer_state():
    try:
        session_id = get_session_id()
        state = _resume_score_state.get_state(
            session_id=session_id
        )
        return jsonify(state), 200
    except Exception:
        logger.exception(
            "Failed to load Resume Scorer state."
        )
        return jsonify({
            "error": "Unable to load Resume Scorer state."
        }), 500

# GENERATE SCORE API
@resume_scorer_bp.route("/api/score", methods=["POST"])
def api_resume_score():
    data = request.get_json(silent=True) or {}
    job_description = data.get("job_description", "")
    if not isinstance(job_description, str) or not job_description.strip():
        return jsonify({
            "error": "Job Description is Required.."
        }), 400
    try:
        session_id = get_session_id()
        result = _resume_score_state.start_generation(
            session_id=session_id,
            job_description=job_description.strip()
        )
        if result.get("error"):
            return jsonify(result), 400
        return jsonify(result), 202
    except Exception:
        logger.exception(
            "Resume Scorer API failed."
        )
        return jsonify({
            "error": "Unable to process Resume Score API."
        }), 500
    
# NEW SCORE API
@resume_scorer_bp.route("/api/score/new", methods=["POST"])
def new_resume_score():
    try:
        session_id = get_session_id()
        state = _resume_score_state.reset(
            session_id=session_id
        )
        return jsonify(state), 200
    except Exception:

        logger.exception(
            "Failed to start a new Resume Score."
        )
        return jsonify({
            "error": "Unable to start a new Resume Score."
        }), 500