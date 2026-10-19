import os
import json 
import requests
import streamlit as st
from settings import API_BASE_URL

# Flask API Helpers
def get_flask_client():
    """Reuse the same Flask session across ReZume pages."""
    if "flask_api_client" not in st.session_state:
        st.session_state["flask_api_client"] = requests.Session()
    return st.session_state["flask_api_client"]

def get_resume__score_state(client):
    response = client.get(
        f"{API_BASE_URL}/career/api/score/state",
        timeout=15
    )
    response.raise_for_status()
    return response.json()


# Page
def render_resume_scorer():
    # Require an analyzed resume.
    if not st.session_state.get("resume_uploaded", False):
        st.warning("Please analyze your resume before using Resume Scorer.")

        if st.button("Back to Resume Upload"):
            st.session_state["page"]= "welcome"
            st.rerun()

        st.stop()

    client = get_flask_client()

    # Page - Styling 
    st.markdown(
            """
            <style>
            [data-testid="stSidebar"],
            [data-testid="stSidebarNav"],
            [data-testid="collapsedControl"] {
                display: none !important;
            }

            .block-container {
                max-width: 1050px;
                padding-top: 2rem;
                padding-bottom: 3rem;
            }

            .rezume-heading {
                font-size: 1rem;
                font-weight: 700;
                letter-spacing: 0.06rem;
                color: #b8860b;
                margin-bottom: 1.5rem;
            }

            .scorer-title {
                font-size: 2.35rem;
                font-weight: 750;
                margin-bottom: 1.5rem;
            }

            .section-title {
                font-size: 1.3rem;
                font-weight: 700;
                margin-bottom: 0.5rem;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

    # Header 
    st.markdown(
        '<div class="rezume-heading">ReZume / Resume Scorer</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="scorer-title">Resume Scorer</div>',
        unsafe_allow_html=True
    )

    # Navigation
    back_col, new_col, spacer = st.columns([1.5, 1.5, 4])
    with back_col:
        if st.button("Back to Services", use_container_width=True):
            st.session_state["page"] = "services"
            st.rerun()

    with new_col:
        if st.button("New Scrore", use_container_width=True):
            try:
                response = client.post(
                    f"{API_BASE_URL}/career/api/score/new",
                    timeout=15
                )
                response.raise_for_status()
                st.session_state["resume_scorer_job_description"] = ""
                st.rerun()
            except requests.exceptions.RequestException as e:
                st.error(f"Could not reset Resume Scorer: {e}")

    # Load Background Scoring Style
    try:
        score_state = get_resume__score_state(client)
    except (requests.exceptions.RequestException, ValueError) as e:
        st.error(f"Unable to load Resume Scorer State: {e}")
        st.stop()

    status = score_state.get("status", "idle")
    result = score_state.get("result")
    error  = score_state.get("error")
    saved_job_description = score_state.get("job_description", "")

    # Track the scoring request across Streamlit reruns.
    if "resume_score_request_pending" not in st.session_state:
        st.session_state["resume_score_request_pending"] = False

    if status == "generating":
        st.session_state["resume_score_request_pending"] = True 

    elif status in ("completed", "error", "idle"):
        st.session_state["resume_score_request_pending"] = False

    scoring_in_progress = (
        status == "generating"
        or st.session_state["resume_score_request_pending"]
    )           

    # Restore saved input when returning to this page.
    if (
        saved_job_description
        and "resume_scorer_job_description" not in st.session_state
    ):
        st.session_state["resume_scorer_job_description"] = (
            saved_job_description
        )

    # Job Description
    st.markdown(
        '<div class="section-title">Job Description</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "Enter the job description to evaluate your resume against."
    )

    job_description = st.text_area(
        "Job Description",
        key="resume_scorer_job_description",
        height=100,
        placeholder="Paste the Target Job Description Here...",
        label_visibility="collapsed",
        disabled= scoring_in_progress
    )

    score_col, refresh_col = st.columns([1.5, 1])
    with score_col:
        score_clicked = st.button(
            "Score Resume",
            type="primary",
            use_container_width=True,
            disabled=scoring_in_progress
        )
    with refresh_col:
        refresh_clicked = st.button(
            "🔄 Refresh Status",
            use_container_width=True
        )
        if refresh_clicked:
            st.rerun()

    # Call Exists Flask API
    if score_clicked:
        if not job_description.strip():
            st.warning("Please Enter a Job Description first")
        else:
            try:
                response = client.post(
                    f"{API_BASE_URL}/career/api/score",
                    json={
                        "job_description": job_description.strip()
                    },
                    timeout=15
                )
                try:
                    payload = response.json()
                except ValueError:
                    payload = {}

                if response.status_code != 202:
                    st.error(
                        payload.get(
                            "error",
                            "The Resume Scorer API could not accept your request."
                        )
                    )
                else:
                    # Flask accepted the request and started background scoring.
                    st.session_state["resume_score_request_pending"] = True
                    st.rerun()
            except requests.exceptions.RequestException as e:
                st.error(f"Could not submit the scoring request: {e}")

    # Scoring Styles
    if status == "generating":
        st.info(
            "Your resume is being scored in the background. "
            "You can visit another service and return later, "
            "or select Refresh Status to check its progress."
        )   
    elif status == "error":
        st.error(error or "Resume Scoring Failed")

    elif status == "completed":
        st.success("Resume Scoring Completed..")


    # Score Output
    st.markdown(
        '<div class="section-title">Score</div>',
        unsafe_allow_html=True
    )

    st.caption("Your resume scoring result will appear below.")

    # Convert a string or structured JSON result for display.
    if result is None:
        result_text = ""
    elif isinstance(result, str):
        result_text = result
    else:
        result_text = json.dumps(
            result,
            ensure_ascii=False,
            indent=2
        )

    # Refresh the displayed value before rendering the widget.
    st.session_state["resume_scorer_output"] = result_text
    st.text_area(
        "Resume Score",
        key="resume_scorer_output",
        height=180,
        placeholder="Your score will appear here after scoring completes.",
        label_visibility="collapsed",
        disabled=True
    )