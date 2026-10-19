import os
import time
import requests
import streamlit as st
from settings import API_BASE_URL

def get_flask_client():
    """Reuse one Flask session for this Streamlit user."""
    if "flask_api_client" not in st.session_state:
        st.session_state["flask_api_client"] = requests.Session()

    return st.session_state["flask_api_client"]

def get_interview_state(client):
    response = client.get(
        f"{API_BASE_URL}/interview/api/state",
        timeout=15
    )
    response.raise_for_status()
    return response.json()

def render_ai_interview():
    # Ensure that a resume has been analyzed first.
    if not st.session_state.get("resume_uploaded", False):
        st.warning("Please analyze your resume before starting an interview")

        if st.button("Go to Resume Upload"):
            st.session_state["page"] = "welcome"
            st.rerun()
        st.stop()
    # Clear the answer only on the next rerun.
    if st.session_state.pop("clear_interview_answer", False):
        st.session_state["interview_answer_input"] = ""

    # Styling
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

        .service-label {
            color: #b8860b;
            font-size: 0.9rem;
            font-weight: 700;
            letter-spacing: 0.12rem;
        }

        .service-title {
            font-size: 2.4rem;
            font-weight: 750;
            margin-top: 0.3rem;
            margin-bottom: 1.5rem;
        }

        .section-heading {
            font-size: 1.25rem;
            font-weight: 700;
            margin-bottom: 0.75rem;
        }

        .output-panel {
            padding: 1.25rem;
            border: 1px solid rgba(128, 128, 128, 0.3);
            border-radius: 12px;
            min-height: 130px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Page Header
    st.markdown(
        '<div class="service-label">AI SERVICE</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="service-title">🎤 AI Interview</div>',
        unsafe_allow_html=True
    )

    # Navigation
    back_col, new_col, spacer = st.columns(
        [1.5, 1.5, 4]
    )
    client = get_flask_client()

    with back_col:
        if st.button("Back to Services", use_container_width=True):
            st.session_state["page"] = "services"
            st.rerun()

    with new_col:
        if st.button("New Interview", use_container_width=True):
            try:
                response = client.post(
                    f"{API_BASE_URL}/interview/api/new",
                    timeout=15
                )
                response.raise_for_status()
                st.session_state["interview_answer_input"] = ""
                st.rerun()
            except requests.exceptions.RequestException as e:
                st.error(f"Could not start a new Interview: {e}")

    # Load Interview State 
    try:
        interview_state = get_interview_state(client)
    except (requests.exceptions.RequestException, ValueError) as e:
        st.error(f"Unable to load the interview: {e}")
        st.stop()

    conversation = interview_state.get("conversation", [])
    status = interview_state.get("status", "idle")
    result = interview_state.get("result")
    error = interview_state.get("error")

    # Chat Panel
    st.markdown(
        '<div class="section-heading">Chat</div>',
        unsafe_allow_html=True
    )

    send_clicked = False
    candidate_answer = ""

    with st.container(border=True):
        # Keep the latest generated response in the Output panel.
        displayed_conversation = conversation
        if (
            result
            and conversation
            and conversation[-1].get("role") in ("ai", "interviewer")
        ):
            displayed_conversation = conversation[:-1]

        if not displayed_conversation:
            st.info("Your interview conversation will appear here..")

        for turn in displayed_conversation:
            role = turn.get("role", "")
            content = turn.get("content", "")

            if role in ("ai", "interviewer"):
                with st.chat_message("assistant"):
                    st.markdown(content)
            elif role == "candidate":
                with st.chat_message("user"):
                    st.markdown(content)

        st.markdown("#### Your Answer")
        candidate_answer = st.text_area(
            "Enter Your Interview answer",
            key="interview_answer_input",
            height=120,
            placeholder="Type your answer here..",
            label_visibility="collapsed",
            disabled=(status == "generating")
            )
        send_col, refresh_col = st.columns(2)
        with send_col:
            send_clicked = st.button(
                "Send Answer",
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

    # SEND ANSWER TO FLASK
    if send_clicked:
        if not candidate_answer.strip():
            st.warning("Please enter your answer before submitting.")
        else:
            try:
                response = client.post(
                    f"{API_BASE_URL}/interview/api/chat",
                    json = {
                        "candidate_answer": candidate_answer.strip()
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
                            "The Interview API could not accept your answer."
                        )
                    )
                else:
                    # Flask performs generation in its background worker.
                    deadline = time.monotonic() + 180
                    latest_state = payload

                    with st.spinner(
                        "Evaluating your answer and preparing"
                        "the next interview question"
                    ):
                        while time.monotonic() < deadline:
                            time.sleep(1)
                            latest_state = get_interview_state(client)

                            if latest_state.get("status") in (
                                "completed",
                                "error"
                            ):
                                break
                    st.session_state["clear_interview_answer"] = True

                    if latest_state.get("status") == "generating":
                        st.session_state["interview_generation_pending"] = True
                    st.rerun()
            except requests.exceptions.RequestException as e:
                st.error(f"Could not send your answer: {e}")

    # Output Panel
    st.markdown(
        '<div class="section-heading">Output</div>',
        unsafe_allow_html=True
    )

    with st.container(border=True):
        if status == "generating":
            st.info(
                "Your answer is being evaluated. "
                "The next question will appear when generation finishes."
            )
        elif status == "error":
            st.error(
                error or "inter response generation failed"
            )
        elif result:
            st.markdown(result)

        elif conversation:
            st.write(
                "Your interview feedback and next question "
                "will appear here after you submit an answer."
            )
        else:
            st.write("No interview output is available yet.")