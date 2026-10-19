import os
import logging
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, render_template
from backend.services.resume_service import ResumeService

logger = logging.getLogger(__name__)

resume_bp = Blueprint("resume", __name__, url_prefix="/resume")

_resume_service = None
resume_uploaded = False
resume_filename = None
# Lazy Loading
def get_resume_service():
    global _resume_service
    if _resume_service is None:
        logger.info("Lazy Loading Initializing..")
        _resume_service = ResumeService()
    return _resume_service

# HTML Route "GET"
@resume_bp.route("/", methods=["GET"])
def resume_dashboard():
    """Renders the main resume upload and management page."""
    return render_template("resume/index.html")

@resume_bp.route("/status", methods=["GET"])
def resume_status():
    return jsonify({
        "resume_uploaded": resume_uploaded,
        "resume_filename": resume_filename
    })

# API action route "POST"
@resume_bp.route("/upload", methods=["POST"])
def api_upload_resume():
    """API endpoint to handle the PDF upload from the frontend"""
    global resume_uploaded, resume_filename

    # Check the Resume is Sent or not
    if "resume" not in request.files:
        return jsonify({
            "error": "No Resume Uploaded.."
        }), 400
    file = request.files["resume"]

    # Check the file is selected or not
    if file.filename == "":
        return jsonify({
            "error": "No File Selected.."
        }), 400

    # Validate File
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({
            "error": "Only pdf files are Allowed.."
        }), 400
    try:
        # Create Uploads Directory
        upload_folder = os.path.join(
            os.getcwd(),
            "data",
            "uploads"
        )
        os.makedirs(
            upload_folder,
            exist_ok=True
        )
        # Secure filename
        filename = secure_filename(file.filename)

        # Full server path
        file_path = os.path.join(
            upload_folder,
            filename
        )
        file.save(file_path)
        logger.info(
            "Resume Uploaded Successfully..: %s",
            file_path
        )
        # Process Resume
        svc = get_resume_service()
        result = svc.process_resume(
            file_path=file_path
        )

        # Check Processing Error
        if result.get("status") == "error":
            resume_uploaded = False
            return jsonify(result), 500
        resume_uploaded = True
        resume_filename = filename
        return jsonify(result), 200
    except Exception as e:
        logger.exception("Resume Uploading API Failed..")
        return jsonify({
            "error": "Unable to Process the Resume.."
        }), 500