import os
import requests
import streamlit as st
from settings import API_BASE_URL

# Flask Client
def get_flask_client():
    """Share the persistent Flask session across ReZume pages."""
    if "flask_api_client" not in st.session_state:
        st.session_state["flask_api_client"] = requests.Session()
    return st.session_state["flask_api_client"]

def get_cover_letter_state(client):
    response = client.get(
        f"{API_BASE_URL}/career/api/cover_letter/state",
        timeout=15
    )
    response.raise_for_status()
    return response.json()


# Cover Letter Page
def render_cover_letter():
    # Require successful resume processing first.
    if not st.session_state.get("resume_uploaded", False):
        st.warning("Please analyze your resume before using Cover Letter.")

        if st.button("Back to Resume Upload"):
            st.session_state["page"] = "welcome"
            st.rerun()
        st.stop()

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

        .cover-title {
            font-size: 2.35rem;
            font-weight: 750;
            margin-bottom: 0.4rem;
        }

        .cover-subtitle {
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

    client = get_flask_client()

    # Header
    st.markdown(
        '<div class="rezume-heading">ReZume / Cover Letter</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="cover-title">Cover Letter</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="cover-subtitle">'
        'Generate a professional, ATS-friendly cover letter '
        'tailored to your target job.'
        '</div>',
        unsafe_allow_html=True
    )

    # Navigation
    back_col, new_col, spacer = st.columns([1.5, 1.7, 4])
    with back_col:
        if st.button("Back to Services", use_container_width=True):
            st.session_state["page"] = "services"
            st.rerun()

    with new_col:
        if st.button("New Cover Letter", use_container_width=True):
            try:
                response = client.post(
                    f"{API_BASE_URL}/career/api/cover_letter/new",
                    timeout=15
                )
                response.raise_for_status()

                # Clear the previous input before the text area is rendered.
                st.session_state["cover_letter_job_description"] = ""
                st.rerun()
            except requests.exceptions.RequestException as e:
                st.error(f"Could not reset the cover letter: {e}")

    # Load Background Generation State
    try:
        cover_state = get_cover_letter_state(client)
    except (requests.exceptions.RequestException, ValueError) as e:
        st.error(f"Unable to Load Cover Letter Status: {e}")
        st.stop()

    status = cover_state.get("status", "idle")
    result = cover_state.get("result") or ""
    error  = cover_state.get("error")
    saved_job_description = cover_state.get("job_description", "")

    # Restore the saved job description when revisiting this page.
    if (
        saved_job_description
        and "cover_letter_job_description" not in st.session_state
    ):
        st.session_state["cover_letter_job_description"] = (
            saved_job_description
        )

    # Job Description
    st.markdown(
        '<div class="section-title">Job Description</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "Paste the job description for the role you are applying for."
    )

    job_description = st.text_area(
        "Job Description",
        key="cover_letter_job_description",
        height=220,
        placeholder=(
            "Paste the complete job description here, "
            "including responsibilities and required skills..."
        ),
        label_visibility="collapsed",
        disabled=(status == "generating")
    )
    
    generate_col, refresh_col = st.columns([1.5, 1])
    with generate_col:
        generate_clicked = st.button(
            "Generate Cover Letter",
            type="primary",
            use_container_width=True,
            disabled=(status == "generating")
        )
    with refresh_col:
        if status == "generating":
            refresh_clicked = st.button(
                "Refresh Status",
                use_container_width=True
            )
            if refresh_clicked:
                st.rerun()

    # Generate Using Flask Api
    if generate_clicked:
        if not job_description.strip():
            st.warning("Please enter a job description first.")
        else:
            try:
                response = client.post(
                    f"{API_BASE_URL}/career/api/cover_letter",
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
                            "The Cover Letter API Could Not accept your Request"
                        )
                    )
                else:
                    # Generation continues on the Flask server
                    st.rerun()
            except requests.exceptions.RequestException as e:
                st.error(f"Could not submit the cover letter request: {e}")

    # Generation Status
    if status == "generating":
        st.info(
            "Your cover letter is being generated in the background. "
            "You can visit another service and return later, "
            "or use Refresh Status to check its progress."
        )
    elif status == "error":
        st.error(error or "Cover Letter Generation Failed")
    elif status == "completed":
        st.success("Your cover letter is ready.")

    # generated Cover Letter Output
    st.markdown(
        '<div class="section-title">Generated Cover Letter</div>',
        unsafe_allow_html=True
    )
    st.caption(
        "Your generated cover letter will appear below."
    )

    # Set the displayed value before creating its widget.
    st.session_state["cover_letter_output_text"] = result
    st.text_area(
        "Generated Cover Letter",
        key="cover_letter_output_text",
        height=300,
        placeholder=(
            "Your generated cover letter will appear here "
            "after generation completes."
        ),
        label_visibility="collapsed",
        disabled=True
    )

    if status == "completed" and result:
        st.download_button(
            "Dowload Cover Letter",
            data=result,
            file_name="ReZume_cover_letter.txt",
            mime="text/plain",
            use_container_width=False
        )