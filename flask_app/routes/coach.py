import uuid
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from flask import (
    Blueprint,
    jsonify,
    request,
    session
)
from backend.services.career_service import CareerService
logger = logging.getLogger(__name__)

# Blueprint for Career Coach
coach_bp = Blueprint(
    "coach",
    __name__,
    url_prefix="/career"
)

_career_service = None

def get_career_service():
    global _career_service
    if _career_service is None:
        logger.info("Lazy Loading Career Coach Service..")
        _career_service = CareerService()
    return _career_service

def get_session_id():
    """Get or Create Uniques Session ID for the Current Browser"""
    if "career_coach_session_id" not in session:
        session["career_coach_session_id"] = str(uuid.uuid4())
    return session["career_coach_session_id"]

class CareerCoachState:
    """Stores Career Coach state for the lifetime of the Flask process."""
    def __init__(self):
        self._states = {}
        self._lock = threading.RLock()
        self.executor = ThreadPoolExecutor(
            max_workers=4,
            thread_name_prefix="career-coach-generation"
        )
    def _create_default_state(self):
        return {
            "messages": [],
            "current_question": "",
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
        """Return the Current Coach State.."""
        state = self._get_or_create_state(
            session_id
        )
        with self._lock:
            return {
                "messages": list(state["messages"]),
                "current_question": state["current_question"],
                "status": state["status"],
                "job_id": state["job_id"],
                "error": state["error"],
                "result": state["result"]
            }
    def reset(self, session_id):
        """Clear the current Career Coach conversation."""
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
        question
    ):
        """Start Career Coach generation in the background."""
        if not question or not question.strip():
            return {
                "error": "Question is Required.."
            }
        question = question.strip()
        state = self._get_or_create_state(
            session_id
        )
        with self._lock:
            if state["status"] == "generating":
                return {
                    "error": (
                        "A Career Coach response is "
                        "Already being Generated.."
                    ),
                    "job_id": state["job_id"]
                }
            job_id = str(uuid.uuid4())
            state["current_question"] = question
            state["status"] = "generating"
            state["job_id"] = job_id
            state["error"]  = None
            state["result"] = None
            state["messages"].append({
                "role": "user",
                "content": question
            })
        logger.info(
            "Starting background Career Coach generation. "
            "job_id=%s",
            job_id
        )
        self.executor.submit(
            self._generate,
            session_id,
            job_id,
            question
        )
        return {
            "job_id": job_id,
            "status": "generating"
        }

    def _generate(
        self,
        session_id,
        job_id,
        question
    ):
        """Perform the generation in Background.."""
        try:
            service = get_career_service()
            result = service.handle_ai_request(
                service_type="career_coach",
                user_input=question
            )
            if (
                isinstance(result, dict)
                and result.get("error")
            ):
                with self._lock:
                    state = self._states.get(
                        session_id
                    )
                    if state and state["job_id"] == job_id:
                        state["status"] = "error"
                        state["error"]  = result.get(
                            "error",
                            "Career Coach Generation Failed.."
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
                state["error"]  = None
                state["messages"].append({
                    "role": "assistant",
                    "content": str(result)
                })
            logger.info(
                "Career Coach generation completed successfully. "
                "job_id=%s",
                job_id
            )
        except Exception:
            logger.exception(
                "Background Career Coach generation failed. "
                "job_id=%s",
                job_id
            )
            with self._lock:
                state = self._states.get(
                    session_id
                )
                if state and state["job_id"] == job_id:
                    state["status"] = "error"
                    state["error"]  = (
                        "Career Coach generation Failed"
                    )
                    state["result"] = None

_career_coach_state = CareerCoachState()

# Get Current Career Coach State
@coach_bp.route(
    "/api/chat/state",
    methods=["GET"]
)
def career_coach_state():
    try:
        session_id = get_session_id()
        state = _career_coach_state.get_state(
            session_id=session_id
        )
        return jsonify(state), 200
    except Exception:
        logger.exception(
            "Failed to load Career Coach state."
        )
        return jsonify({
            "error": (
                "Unable to load Career Coach state."
            )
        }), 500

# Start Career Coach Generation
@coach_bp.route(
    "/api/chat",
    methods=["POST"]
)
def api_career_chat():
    data = request.get_json(
        silent=True
    ) or {}
    question = data.get(
        "question",
        ""
    )
    if (
        not isinstance(question, str)
        or not question.strip()
    ):
        return jsonify({
            "error": "question is required"
        }), 400

    try:
        session_id = get_session_id()
        result = _career_coach_state.start_generation(
            session_id=session_id,
            question=question.strip()
        )
        if result.get("error"):
            return jsonify(result), 409
        return jsonify(result), 202
    except Exception:
        logger.exception(
            "Career Coach API failed."
        )
        return jsonify({
            "error": (
                "Unable to process the Career Coach request."
            )
        }), 500

# Start New Career Coach Conversation
@coach_bp.route(
    "/api/chat/new",
    methods=["POST"]
)
def new_career_coach():
    try:
        session_id = get_session_id()
        state = _career_coach_state.reset(
            session_id=session_id
        )
        return jsonify(state), 200
    except Exception:
        logger.exception(
            "Failed to start a new Career Coach conversation."
        )
        return jsonify({
            "error": (
                "Unable to start a new Career Coach conversation."
            )
        }), 500