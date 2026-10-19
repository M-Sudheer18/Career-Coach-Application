import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
from flask import (
    Blueprint,
    request,
    jsonify,
    render_template
)
from backend.services.recommendation_service import RecommendationService

logger = logging.getLogger(__name__)

recommendation_bp = Blueprint(
    "recommendation",
    __name__,
    url_prefix="/career"
)

_recommendation_service = None

_recommendation_executor = ThreadPoolExecutor(
    max_workers=2,
    thread_name_prefix="recommendation"
)
_recommendation_lock = threading.Lock()
_recommendation_state = {
    "job_id": None,
    "status": "idle",
    "target_role": "",
    "result": None,
    "error": None
}

def get_recommendation_service():
    global _recommendation_service
    if _recommendation_service is None:
        logger.info("Lazy Loading Recommendation Service..")
        _recommendation_service = RecommendationService()

    return _recommendation_service

def _generate_recommendations(
    job_id: str,
    target_role: str
):
    """Generate Recomm.. in the Background"""
    logger.info(
        "Starting Background Recommendation Generation. "
        "job_id=%s",
        job_id
    )
    try:
        svc = get_recommendation_service()
        result = svc.get_recommendation(
            target_role=target_role
        )
        with _recommendation_lock:
            if _recommendation_state["job_id"] != job_id:
                return
            if isinstance(result, dict) and result.get("error"):
                _recommendation_state["status"] = "error"
                _recommendation_state["error"] = (
                    result.get("error")
                )
                _recommendation_state["result"] = None
            else:
                _recommendation_state["status"] = "completed"
                _recommendation_state["result"] = result
                _recommendation_state["error"]  = None
        logger.info(
            "Recommendation generation completed. "
            "job_id=%s",
            job_id
        )
    except Exception:

        logger.exception(
            "Recommendation background generation failed. "
            "job_id=%s",
            job_id
        )
        with _recommendation_lock:
            if _recommendation_state["job_id"] == job_id:
                _recommendation_state["status"] = "error"
                _recommendation_state["result"] = None
                _recommendation_state["error"]  = (
                    "Unable to Generate a recommendation"
                )

@recommendation_bp.route(
    "/recommendations",
    methods=["GET"]
)
def recommendations_page():
    return render_template(
        "career/recommendations.html"
    )

@recommendation_bp.route("/api/recommendations", methods=["POST"])
def api_get_recommendations():
    """Career Recommendation Generations."""
    data = request.get_json(silent=True) or {}
    target_role = data.get("target_role", "")

    if target_role is None:
        target_role = ""

    if not isinstance(target_role, str):
        return jsonify({
            "error": "Target role must be a string"
        }), 400

    target_role = target_role.strip()
    with _recommendation_lock:
        if _recommendation_state["status"] == "generating":
            return jsonify({
                "error": "Response is already Generating"
            }), 409
        job_id = str(uuid4())
        _recommendation_state["job_id"] = job_id
        _recommendation_state["status"] = "generating"
        _recommendation_state["target_role"] = target_role
        _recommendation_state["result"] = None
        _recommendation_state["error"]  = None
    logger.info(
        "Starting background Recommendation generation. "
        "job_id=%s",
        job_id
    )

    _recommendation_executor.submit(
        _generate_recommendations,
        job_id,
        target_role
    )
    return jsonify({
        "message": "Recommendation generation started.",
        "job_id": job_id,
        "status": "generating"
    }), 202

@recommendation_bp.route("/api/recommendations/state", methods=["GET"])
def api_recommendations_state():
    """Return the current Recommendation generation state."""
    with _recommendation_lock:
        return jsonify({
            "job_id": _recommendation_state["job_id"],
            "status": _recommendation_state["status"],
            "target_role": _recommendation_state["target_role"],
            "result": _recommendation_state["result"],
            "error": _recommendation_state["error"]
        }), 200

@recommendation_bp.route("/api/recommendations/new", methods=["POST"])
def api_new_recommendations():
    """Reset Recommendation state for a new request."""
    with _recommendation_lock:
        if _recommendation_state["status"] == "generating":
            return jsonify({
                "error": "Generation is Still in Progress"
            }), 409

        _recommendation_state["job_id"] = None
        _recommendation_state["status"] = "idle"
        _recommendation_state["target_role"] = ""
        _recommendation_state["result"] = None
        _recommendation_state["error"] = None

    return jsonify({
        "message": "Recommendation state reset.",
        "status": "idle"
    }), 200