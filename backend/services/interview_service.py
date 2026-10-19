# technical interview interactions using:
#     Candidate Resume
#           ↓
#     FAISS Retrieval
#           ↓
#     Resume Context
#           ↓
#     Interview History
#           ↓
#     Gemini
#           ↓
#     Evaluation + Next Question

import logging
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Union, Dict, Any, List, Optional
from backend.ai.vector_store_manager import get_shared_vector_store
from backend.ai.rag import run_rag_pipeline
logger = logging.getLogger(__name__)

# Technical interview Interactions..
class InterviewService:
    def __init__(self):
        logger.info("Initializing Interview Service..")
        self.vector_store = get_shared_vector_store()
        self._states = {}

        # Protect the State when Background thread update it
        self._lock = threading.RLock()

        # Generation Run independently from the browser request
        self._executor = ThreadPoolExecutor(
            max_workers=4,
            thread_name_prefix="interview-generation"
        )

    def _create_default_state(self) -> Dict[str, Any]:
        return {
            "conversation": [
                {
                    "role": "ai",
                    "content": (
                        "Welcome to your AI Technical Interview. "
                        "Let's begin. Please introduce yourself and "
                        "tell me about your technical background."
                    )
                }
            ],
            "status": "idle",
            "job_id": None,
            "error": None,
            "result": None
        }
    def _get_or_create_state(self, session_id: str) -> Dict[str, Any]:
        with self._lock:
            if session_id not in self._states:
                self._states[session_id] = self._create_default_state()
            return self._states[session_id]

    def get_state(self, session_id: str) -> Dict[str, Any]:
        # Return the current interview state for a browser session.
        state = self._get_or_create_state(session_id)
        with self._lock:
            return {
                "conversation": [
                    dict(turn)
                    for turn in state["conversation"]
                ],
                "status": state["status"],
                "job_id": state["job_id"],
                "error": state["error"],
                "result": state["result"]
            }

    def reset_interview(self, session_id: str) -> Dict[str, Any]:
        # This Clears Previous Conversation
        with self._lock:
            self._states[session_id] = self._create_default_state()
            return {
                "conversation": [
                    dict(turn)
                    for turn in self._states[session_id]["conversation"]
                ],
                "status": "idle",
                "job_id": None,
                "error": None,
                "result": None
            }

    def start_generation(
        self,
        session_id: str,
        candidate_answer: str
    ) -> Dict[str, Any]:
        """
        Start an AI interview generation in the background.
        The HTTP request returns immediately while the AI generation
        continues on the Flask server.
        """
        if not candidate_answer or not candidate_answer.strip():
            return {
                "error": "Candidate answer can't be Empty.."
            }
        candidate_answer = candidate_answer.strip()
        state = self._get_or_create_state(session_id)
        with self._lock:
            # Do not allow another generation while one is running.
            if state["status"] == "generating":
                return {
                    "error": "An interview Response is already Being Generating..",
                    "job_id": state["job_id"]
                }
            # Save the Candidate answer In=mediately
            state["conversation"].append({
                "role": "candidate",
                "content": candidate_answer
            })

            # Copy the History that belongs to this Generation..
            conversation_history = [
                dict(turn)
                for turn in state["conversation"][:-1]
            ]
            job_id = str(uuid.uuid4())
            state["status"] = "generating"
            state["job_id"] = job_id
            state["error"] = None
            state["result"] = None
        logger.info(
            "Starting background interview generation. job_id=%s",
            job_id
        )

        # Submit Generation to Background Worker
        self._executor.submit(
            self._generate_response,
            session_id,
            job_id,
            candidate_answer,
            conversation_history
        )

        return {
            "job_id": job_id,
            "status": "generating"
        }

    def _generate_response(
        self,
        session_id: str,
        job_id: str,
        candidate_answer: str,
        conversation_history: List[Dict[str, Any]]
    ) -> None:
        # Performs the actual RAG + Gemini generation in the background.
        try:
            response = self.evaluate_ask(
                candidate_answer=candidate_answer,
                conversation_history=conversation_history
            )
            if isinstance(response, dict) and response.get("error"):
                error_message = response.get(
                    "error",
                    "AI Interview generation failed."
                )
                with self._lock:
                    state = self._states.get(session_id)
                    if state and state["job_id"] == job_id:
                        state["status"] = "error"
                        state["error"] = error_message
                        state["result"] = None
                return
            
            with self._lock:
                state = self._states.get(session_id)
                if not state or state["job_id"] != job_id:
                    return
                # Save AI response permanently for the lifetime
                # of this Flask process.
                state["conversation"].append({
                    "role": "ai",
                    "content": str(response)
                })
                state["status"] = "completed"
                state["result"] = str(response)
                state["error"] = None

            logger.info(
                "Interview generation completed successfully. job_id=%s",
                job_id
            )

        except Exception:
            logger.exception(
                "Background Interview generation failed. job_id=%s",
                job_id
            )
            with self._lock:
                state = self._states.get(session_id)
                if state and state["job_id"] == job_id:
                    state["status"] = "error"
                    state["error"] = (
                        "AI Interview generation failed."
                    )
                    state["result"] = None
                
    # Evaluatvate Candidate answers and Asks the Next Question
    def evaluate_ask(
            self, 
            candidate_answer: str,
            conversation_history: Optional[List[Dict[str, str]]] = None
            ) -> Union[str, Dict[str, Any]]:
        logger.info("InterviewService processing candidate response with history.")
        if not candidate_answer or not candidate_answer.strip():
            return {"error": "Candidate answer Can't be Empty..."}
        candidate_answer = candidate_answer.strip()

        history_text = ""
        if conversation_history:
            history_lines = []
            for turn in conversation_history:
                turn_role = turn.get("role", "")
                if turn_role in ("ai", "interviewer"):
                    role = "Hiring Manager"
                elif turn_role == "candidate":
                    role = "Candidate"
                else:
                    role = "Candidate"
                content = turn.get("content", "").strip()
                if content:
                    history_lines.append(f"{role}: {content}")
            if history_lines:
                history_text = (
                    "PREVIOUS INTERVIEW TRANSCRIPT:\n"
                    + "\n".join(history_lines)
                    + "\n\n"
                )

        query = (
            f"{history_text}"
            "CURRENT INTERACTION:\n"
            "The candidate provided the following response "
            "to the previous interview question:\n\n"
            f"{candidate_answer}\n\n"

            "INSTRUCTIONS:\n"
            "1. Briefly evaluate the candidate's response "
            "using only the supplied resume context.\n"
            "2. Do not invent candidate skills or experience.\n"
            "3. Do not repeat a question already present "
            "in the previous interview transcript.\n"
            "4. Ask exactly ONE new technical follow-up question.\n"
            "5. The question must be relevant to the candidate's "
            "actual resume skills.\n"
            "6. Do not reveal the answer to the question.\n"
        )
        try:
            response = run_rag_pipeline(
                user_query=query,
                vector_store=self.vector_store,
                service_type="ai_interview",
                expected_format="text",
                top_k=3
            )
            logger.info("Interview Response generated Successful..")
            return response
        except Exception as e:
            logger.exception("Failed to Generate the Question")
            return {"error": "Ai Interview Evalution Failed.."}