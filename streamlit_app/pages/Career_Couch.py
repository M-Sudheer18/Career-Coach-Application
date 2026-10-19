import os
import requests
import streamlit as st
from settings import API_BASE_URL

# Flask API Helpers
def get_flask_client():
    """Reuse the same Flask session across ReZume pages."""
    if "flask_api_client" not in st.session_state:
        st.session_state["flask_api_client"] = requests.Session()

    return st.session_state["flask_api_client"]

def get_career_coach_state(client):
    response = client.get(
        f"{API_BASE_URL}/career/api/chat/state",
        timeout=15
    )
    response.raise_for_status()
    return response.json()

# Page
def render_career_coach():
    # Require a successfully analyzed resume.
    if not st.session_state.get("resume_uploaded", False):
        st.warning(
            "Please analyze your resume before using Career Coach."
        )
        if st.button("Back to Resume Upload"):
            st.session_state["page"] = "welcome"
            st.rerun()
        st.stop()

    # Clear input on the next rerun, before creating the widget.
    if st.session_state.pop("clear_career_coach_questions", False):
        st.session_state["career_coach_questions"] = "" 

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

        .coach-title {
            font-size: 2.35rem;
            font-weight: 750;
            margin-bottom: 1.5rem;
        }

        .section-title {
            font-size: 1.3rem;
            font-weight: 700;
            margin-bottom: 0.75rem;
        }

        .chat-panel {
            padding: 1rem;
            border: 1px solid rgba(128, 128, 128, 0.3);
            border-radius: 12px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Heading
    st.markdown(
        '<div class="rezume-heading">ReZume / Career Coach</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="coach-title">Career Coach</div>',
        unsafe_allow_html=True
    )

    # Navigation
    back_col, new_col, spacer = st.columns([1.5, 1.7, 4])
    with back_col:
        if st.button("Back to Services", use_container_width=True):
            st.session_state["page"] = "services"
            st.rerun()

    with new_col:
        if st.button("New Conversation", use_container_width=True):
            try:
                response = client.post(
                    f"{API_BASE_URL}/career/api/chat/new",
                    timeout=15
                )
                response.raise_for_status()
                st.session_state["clear_career_coach_questions"] = True
                st.rerun()
            except requests.exceptions.RequestException as e:
                st.error(f"Could not start a new conversation: {e}")

    # Load Current Chat State
    try:
        coach_state = get_career_coach_state(client)
    except (requests.exceptions.RequestException, ValueError) as e:
        st.error(f"Unable to load Career Coach history: {e}")
        st.stop()

    messages = coach_state.get("messages", [])
    status = coach_state.get("status", "idle")
    result = coach_state.get("result")
    error = coach_state.get("error")

    # Ask me Anything
    with st.form("career_coach_form", clear_on_submit=False):
        input_col, send_col = st.columns([8, 1])
        with input_col:
            question = st.text_input(
                "Ask me Anything",
                key="career_coach_questions",
                placeholder="Ask me Anything..",
                label_visibility="collapsed",
                disabled=(status == "generating")
            )

        with send_col:
            send_clicked = st.form_submit_button(
                "➜",
                help = "Send Question",
                use_container_width=True,
                disabled=(status == "generating")
            )

    # Send Question to Flask
    if send_clicked:
        if not question.strip():
            st.warning("Please enter a question first.")
        else:
            try:
                response = client.post(
                    f"{API_BASE_URL}/career/api/chat",
                    json = {
                        "question": question.strip()
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
                            "The Career Coach API could not accept your question."
                        )
                    )
                else:
                    # Flask generates the response in the background.
                    st.session_state["clear_career_coach_questions"] = True
                    st.rerun()

            except requests.exceptions.RequestException as e:
                st.error(f"Could not send your question: {e}")

    # Generation Status
    if status == "generating":
        st.info(
            "ReZume Career Coach is preparing your response. "
            "Generation continues in the Flask backend."
        )
        if st.button("Refresh Status", key="refresh_career_coach"):
            st.rerun()
    elif status == "error":
        st.error(error or "Career Coach Response Generation Failed...")


    # Chat History
    st.markdown(
        '<div class="section-title">Chat History</div>',
        unsafe_allow_html=True
    )

    with st.container(border=True):
        if not messages:
            st.caption(
                "Your questions and Career Coach responses "
                "will appear here."
            )

        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")

            if role == "user":
                with st.chat_message("user"):
                    st.markdown(content)
            elif role == "assistant":
                with st.chat_message("assistant"):
                    st.markdown(content)

        if status == "generating":
            st.caption("Waiting for the Career Coach response...")
        elif status == "completed" and result and not any(
            message.get("role") == "assistant"
            and message.get("content") == str(result)
            for message in messages
        ):
            st.markdown(str(result))