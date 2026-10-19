import os
import requests
import pymupdf
import streamlit as st
from pathlib import Path
from settings import API_BASE_URL

APP_DIR = Path(__file__).resolve().parent

st.set_page_config(
    page_title="ReZume",
    page_icon=str(APP_DIR / "images" / "favicon.png"),
    layout="wide"
)

def get_flask_client():
    """Reuse the same Flask session cookie across API calls."""
    if "flask_api_client" not in st.session_state:
        st.session_state["flask_api_client"] = requests.Session()

    return st.session_state["flask_api_client"]

if "resume_uploaded" not in st.session_state:
    st.session_state["resume_uploaded"] = False

if "resume_filename" not in st.session_state:
    st.session_state["resume_filename"] = None

if "resume_text" not in st.session_state:
    st.session_state["resume_text"] = None

if "page" not in st.session_state:
    st.session_state["page"] = "welcome"

# STYLING
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
        padding-top: 3rem;
        padding-bottom: 3rem;
    }

    .welcome-title {
        text-align: center;
        font-size: 3rem;
        font-weight: 750;
        margin-bottom: 0.5rem;
    }

    .welcome-subtitle {
        text-align: center;
        font-size: 1.15rem;
        color: #7b8190;
        margin-bottom: 2.5rem;
    }

    .service-card {
        padding: 1.25rem 0.75rem;
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 12px;
        text-align: center;
        min-height: 110px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# HEADER
if st.session_state["page"] in ("welcome", "services"):
    st.markdown(
        '<div class="welcome-title">ReZume</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="welcome-subtitle">'
        'Your personal AI-powered career assistant'
        '</div>',
        unsafe_allow_html=True
    )

# WELCOME / RESUME UPLOAD PAGE
if st.session_state["page"] == "welcome":
    st.markdown("## Welcome!")
    st.write(
        "Upload your resume to get started. "
        "Once your resume is processed successfully, "
        "you can access the AI-powered career services."
    )
    st.markdown("### 📄 Upload Your Resume")
    st.write("Choose your resume in PDF format.")

    uploaded_file = st.file_uploader(
        "Select your resume",
        type=["pdf"],
        accept_multiple_files=False
    )

    left, right = st.columns([3, 1], gap="large")
    with left:
        if uploaded_file is not None:
            st.info(f"Selected File: {uploaded_file.name}")
            st.caption(
                f"File size: {uploaded_file.size / 1024:.1f} KB"
            )
        else:
            st.info("Please Upload your resume PDF first.")

    with right:
        analyze_clicked = st.button(
            "Analyze Resume",
            type="primary",
            use_container_width=True,
            disabled=uploaded_file is None
        )
    if analyze_clicked and uploaded_file is not None:
        try:
            pdf_bytes = uploaded_file.getvalue()
            if not pdf_bytes.startswith(b"%PDF-"):
                raise ValueError(
                    "The selected file is not a valid PDF.",
                    "Please upload a valid resume PDF."
                )
            with pymupdf.open(stream=pdf_bytes, filetype="pdf") as pdf:
                if pdf.page_count == 0:
                    raise ValueError(
                        "The PDF contains no pages."
                    )

                extracted_text = "\n".join(
                    page.get_text() for page in pdf
                ).strip()
            if not extracted_text:
                raise ValueError(
                    "No readable text was found in this PDF. "
                    "Please upload a text-based resume."
                )

            # Send the PDF to the Flask backend
            with st.spinner(
                "Analyzing Your Resume.., Please Wait while the AI Pipeline Process it..",
            ):
                response = requests.post(
                    f"{API_BASE_URL}/resume/upload",
                    files={
                        "resume": (
                            uploaded_file.name,
                            pdf_bytes,
                            "application/pdf"
                        )
                    },
                    timeout=300
                )

            # Read the backend response
            try:
                result = response.json()
            except ValueError:
                result = {}

            # Handle unsuccessful processing
            if (
                not response.ok
                or result.get("status") == "error"
                or "error" in result
            ):
                error_message = result.get(
                    "error",
                    result.get(
                        "message",
                        "The backend could not process your resume."
                    )
                )
                st.error(
                    f"Resume processing failed: {error_message}"
                )
            else:
                # Save the successful session state
                st.session_state["resume_uploaded"] = True
                st.session_state["resume_filename"] = (
                    uploaded_file.name
                )
                st.session_state["resume_text"] = extracted_text
                st.session_state["page"] = "services"
                
                st.success(
                    "Resume processed successfully!"
                )

                # Open the services dashboard
                st.rerun()
        except ValueError as e:
            st.error(str(e))

        except requests.exceptions.Timeout:
            st.error(
                "The resume-processing request timed out. "
                "Check the Flask server and try again."
            )

        except requests.exceptions.ConnectionError:
            st.error(
                "Could not connect to the Flask backend. "
                "Make sure Flask is running at "
                f"{API_BASE_URL}."
            )

        except requests.exceptions.RequestException as e:
            st.error(
                f"Request failed: {e}"
            )

        except Exception as e:
            st.error(
                f"Unable to read or process the PDF: {e}"
            )

# Service Dashboard
elif st.session_state["page"] == "services":
    if not st.session_state["resume_uploaded"]:
        st.session_state["page"] = "welcome"
        st.rerun()
    st.success(
        f"Resume Analyzed: "
        f"{st.session_state['resume_filename']}"
    )
    
    st.markdown("## Your AI Career Services")
    st.write(
        "Choose a service to continue working with your resume."
    )

    services = [
        ("🎤", "AI Interview"),
        ("✉️", "Cover Letter"),
        ("📊", "Resume Scorer"),
        ("🧭", "Career Recommendations"),
        ("💬", "Career Coach"),
    ]

    page_routes = {
        "AI Interview": "ai_interview",
        "Cover Letter": "cover_letter",
        "Resume Scorer": "resume_scorer",
        "Career Recommendations": "career_recommendations",
        "Career Coach": "career_coach",
    }

    for start in range(0, len(services), 3):
        columns = st.columns(3, gap="medium")

        for column, (icon, service) in zip(
            columns, services[start:start + 3]
        ):
            with column:
                with st.container(border=True):
                    st.markdown(
                        f"""
                        <div style="text-align:center;
                                    padding:12px;
                                    font-size:2.5rem;">
                            {icon}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    if st.button(
                        service,
                        key=f"open_{page_routes[service]}",
                        use_container_width=True
                    ):
                        st.session_state["page"] = page_routes[service]
                        st.rerun()

elif st.session_state["page"] == "ai_interview":
    from pages.Ai_Interview import render_ai_interview
    render_ai_interview()

elif st.session_state["page"] == "cover_letter":
    from pages.Cover_Letter import render_cover_letter
    render_cover_letter()

elif st.session_state["page"] == "resume_scorer":
    from pages.Resume_Scorer import render_resume_scorer
    render_resume_scorer()

elif st.session_state["page"] == "career_recommendations":
    from pages.Career_Recommendations import render_career_recommendations
    render_career_recommendations()

elif st.session_state["page"] == "career_coach":
    from pages.Career_Couch import render_career_coach
    render_career_coach()

    if st.button("Back to Resume Upload"):
        st.session_state["page"] = "welcome"
        st.rerun()