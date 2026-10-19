import os
import yaml
import time
import logging
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types
from google.genai import errors

logger = logging.getLogger(__name__)


# A Client for Interacting with Google API
# Handles Initialization, Configuration, and Network Requests.
def load_model_name():
    root_dir = Path(__file__).resolve().parents[2]
    settings_path = root_dir / "config" / "settings.yaml"

    with open(settings_path, "r", encoding="utf-8") as file:
        settings = yaml.safe_load(file)

    return settings["ai"]["llm_model"]
class GeminiClient:

    def __init__(
        self,
        model_name: Optional[str] = None,
        system_instructions: Optional[str] = None
    ):
        self.model_name = model_name or load_model_name()
        # Check API Key exists before starting
        key = os.getenv("GEMINI_API_KEY")
        logger.info(
            "Gemini API key diagnostic | Loaded: %s | Prefix: %s | Length: %s",
            bool(key),
            key[:3] if key else "NONE",
            len(key) if key else 0
        )

        if not key:
            logger.critical("API key not found!")
            raise ValueError("API Key is Missing..")

        # Configure the SDK
        try:
            self.client = genai.Client(
                api_key=key
            )

            self.system_instructions = system_instructions

            logger.info(
                "Gemini client initialized successfully. Model: %s",
                self.model_name
            )

        except Exception:
            logger.exception(
                "Failed to initialize Gemini client."
            )
            raise

    # Send the Prompt and Get the Response
    def generate_response(
        self,
        prompt: str,
        max_tokens: int = 1024
    ) -> str:

        if not prompt or not prompt.strip():
            logger.warning("Received an Empty Prompt..")
            return ""

        # Configure Generation Parameters
        config = types.GenerateContentConfig(
            system_instruction=self.system_instructions,
            max_output_tokens=max_tokens
        )

        # Application-level retry settings
        max_retries = 3

        for attempt in range(1, max_retries + 1):

            try:
                logger.info(
                    "Sending API request to Gemini. "
                    "Attempt %s/%s | Model: %s | Max Tokens: %s",
                    attempt,
                    max_retries,
                    self.model_name,
                    max_tokens
                )

                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=config
                )

                # Extract the Text Safely
                response_text = response.text
                if not response.text:
                    logger.warning(
                        "Model Generated an Empty Response."
                    )
                    candidates = getattr(
                        response,
                        "candidates",
                        None
                    )
                    if candidates:
                        for index, candidate in enumerate(candidates):
                            logger.warning(
                                "Gemini Candidate %d | Finish Reason: %s",
                                index,
                                getattr(
                                    candidate,
                                    "finish_reason",
                                    None
                                )
                            )
                            content = getattr(
                                candidate,
                                "content",
                                None
                            )
                            if content:
                                parts = getattr(
                                    content,
                                    "parts",
                                    None
                                )
                                logger.warning(
                                    "Gemini Candidate %d | Parts: %s",
                                    index,
                                    parts
                                )
                    prompt_feedback = getattr(
                        response,
                        "prompt_feedback",
                        None
                    )
                    if prompt_feedback:
                        logger.warning(
                            "Gemini Prompt Feedback: %s",
                            prompt_feedback
                        )
                    raise ValueError(
                        "Gemini Returned as Empty Response"
                    )
                logger.info(
                    "Successfully Received a Response from gemini"
                )
                
                return response.text

            except errors.ServerError as e:

                # 503 = Service Unavailable
                # 500 = Internal Server Error
                status_code = getattr(e, "code", None) or getattr(e, "status_code", None)

                if status_code in (500, 503):

                    if attempt < max_retries:

                        wait_time = 2 ** attempt

                        logger.warning(
                            "Gemini server error (%s). "
                            "Retrying in %s seconds... "
                            "Attempt %s/%s",
                            status_code,
                            wait_time,
                            attempt,
                            max_retries
                        )

                        time.sleep(wait_time)
                        continue

                    logger.error(
                        "Gemini server remained unavailable "
                        "after %s attempts.",
                        max_retries
                    )

                    raise

                # Other server errors should not be retried
                logger.exception(
                    "Gemini server error that is not retryable."
                )
                raise

            except errors.ClientError as e:

                # Client errors such as 400, 401, 403, 404
                # generally should NOT be retried.
                logger.exception(
                    "Gemini client/API request error."
                )
                raise

            except Exception:

                logger.exception(
                    "Failed to Send the Request to Model."
                )
                raise

        # This should never normally be reached.
        raise RuntimeError(
            "Gemini generation failed after all retry attempts."
        )