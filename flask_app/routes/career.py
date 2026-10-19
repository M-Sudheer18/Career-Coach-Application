import logging
from flask import (
    Blueprint,
    render_template
)
logger = logging.getLogger(__name__)

# Blueprint for Career
career_bp = Blueprint("career", __name__, url_prefix="/career")

# Templates
@career_bp.route("/dashboard", methods=["GET"])
def career_dashboard():
    return render_template("career/dashboard.html")

@career_bp.route("/coach", methods=["GET"])
def coach_page():
    return render_template("career/coach.html")

