import logging
import os
from uuid import uuid4

from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    session,
    current_app
)

logger = logging.getLogger(__name__)

main_bp = Blueprint("main", __name__)


@main_bp.route("/", methods=["GET"])
def home():
    """Render the Main Web Page"""
    return render_template("home.html")


@main_bp.route("/profile", methods=["GET"])
def profile_page():
    """Render the Profile Page"""
    user_name = session.get(
        "user_name",
        "User Name"
    )
    profile_image = session.get(
        "profile_image",
        None
    )
    return render_template(
        "profile.html",
        user_name = user_name,
        profile_image = profile_image
    )

@main_bp.route("/profile/update-name", methods=["POST"])
def update_profile_name():
    data = request.get_json()
    user_name = data.get(
        "user_name",
        ""
    ).strip()
    if not user_name:
        return jsonify({
            "success": False,
            "message": "Name Can't be Empty"
        }), 400
    session["user_name"] = user_name
    return jsonify({
        "success": True,
        "user_name": user_name
    })

@main_bp.route("/profile/upload-image", methods=["POST"])
def upload_profile_image():
    if "profile_image" not in request.files:
        return jsonify({
            "success": False,
            "message": "No Image Selected"
        }), 400
    image = request.files["profile_image"]
    if image.filename == "":
        return jsonify({
            "success": False,
            "message": "No image Selected"
        }), 400
    upload_folder = os.path.join(
        current_app.static_folder,
        "images",
        "profiles"
    )
    os.makedirs(
        upload_folder,
        exist_ok=True
    )
    extension = os.path.splitext(
        image.filename
    )[1]
    filename = (
        f"{uuid4().hex}{extension}"
    )
    image_path = os.path.join(
        upload_folder,
        filename
    )
    image.save(image_path)
    profile_image = (
        f"/static/images/profiles/{filename}"
    )
    session["profile_image"] = profile_image
    return jsonify({
        "success": True,
        "profile_image": profile_image
    })