import os
import requests
import streamlit as st
from settings import API_BASE_URL

# Flask API Helpers
def get_flask_client():
    """Reuse the persistent Flask client across ReZume pages."""
    if "flask_api_client" not in st.session_state:
        st.session_state["flask_api_client"] = requests.Session()
    return st.session_state["flask_api_client"]

def get_recommendation_state(client):
    response = client.get(
        f"{API_BASE_URL}/career/api/recommendations/state",
        timeout=15
    )
    response.raise_for_status()
    return response.json()

# Career Recommendations Page
def render_career_recommendations():
    # Require a successfully analyzed resume.
    if not st.session_state.get("resume_uploaded", False):
        st.warning("Please analyze your resume before using Career Recommendations.")
        if st.button("Back to Resume Upload"):
            st.session_state["page"] = "welcome"
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

        .recommendation-title {
            font-size: 2.35rem;
            font-weight: 750;
            margin-bottom: 0.5rem;
        }

        .recommendation-subtitle {
            color: #7b8190;
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
        '<div class="rezume-heading">'
        'ReZume / Career Recommendations'
        '</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="recommendation-title">'
        'Career Recommendations'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="recommendation-subtitle">'
        'Discover skills, certifications, projects, and next steps '
        'based on your resume and career goals.'
        '</div>',
        unsafe_allow_html=True
    )

    # Navigation
    back_col, new_col, spacer = st.columns([1.5, 1.8, 4])
    with back_col:
        if st.button("Back to Services", use_container_width=True):
            st.session_state["page"] = "services"
            st.rerun()

    with new_col:
        if st.button("New Recommendation", use_container_width=True):
            try:
                response = client.post(
                    f"{API_BASE_URL}/career/api/recommendations/new",
                    timeout=15
                )
                response.raise_for_status()
                st.session_state["recommendations_target_role"] = ""
                st.rerun()
            except requests.exceptions.RequestException as e:
                st.error(
                    f"Could not reset recommendations: {e}"
                )

    # Load Generation State 
    try:
        recommendation_state = get_recommendation_state(client)
    except (requests.exceptions.RequestException, ValueError) as e:
        st.error(f"Unable to load recommendation state: {e}")
        st.stop()

    status = recommendation_state.get("status", "idle")
    result = recommendation_state.get("result")
    error  = recommendation_state.get("error")
    saved_target_role = recommendation_state.get("target_role", "")

    # Restore the submitted target role when revisiting this page.
    if (
        saved_target_role
        and "recommendations_target_role" not in st.session_state
    ):
        st.session_state["recommendations_target_role"] = saved_target_role

    # Target Role
    st.markdown(
        '<div class="section-title">Target Role</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "Enter your career goal, such as Data Scientist or AI Engineer. "
        "Leave it blank for general recommendations based on your resume."
    )

    target_role = st.text_input(
        "Target Role",
        key="recommendations_target_role",
        placeholder="e.g., Data Scientist, AI  Engineer, Python Developer",
        disabled= (status == "generating"),
        label_visibility="collapsed"
    )

    action_col, refresh_col = st.columns([1.6, 1])
    with action_col:
        generate_clicked = st.button(
            "Generate Recommendations",
            type="primary",
            use_container_width=True,
            disabled=(status == "generating")
        )

    with refresh_col:
        if status == "generating":
            if st.button("Refresh Status", use_container_width=True):
                st.rerun()

    # Call Flask API
    if generate_clicked:
        try:
            response = client.post(
                f"{API_BASE_URL}/career/api/recommendations",
                json = {
                    "target_role": target_role.strip()
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
                        "The Recommendations API could not accept your request."
                    )
                )
            else:
                st.rerun()
        except requests.exceptions.RequestException as e:
            st.error(
                f"Could not Submit your Recommendtaion Request: {e}"
            )

    # Generation Status
    if status == "generating":
        st.info(
            "Your recommendations are being generated in the background. "
            "You can visit another service and return later, or refresh "
            "the status to check progress."
        )
    elif status == "error":
        st.error(error or "Career Recommendation generation failed..")
    elif status == "completed":
        st.success("Your Career Recommendation are ready..")

    # Recommendations Output
    st.markdown(
        '<div class="section-title">Recommendations</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "Your skills, certification, project, and next-step recommendations "
        "will appear here."
    )

    with st.container(border=True):
        if status == "completed" and result:
            if isinstance(result, str):
                st.markdown(result)
            else:
                st.json(result)
        elif status == "error":
            st.write("No Recommendations were generated..")
        elif status == "generating":
            st.write("Preparing your personalized recommendations...")
        else:
            st.write(
                "Your recommendations will appear here after generation."
            )