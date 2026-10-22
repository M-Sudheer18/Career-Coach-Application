import logging
import math
import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSION = 768
BATCH_SIZE = 16

_client = None


def _get_client():
    global _client

    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured.")

        _client = genai.Client(api_key=api_key)

    return _client


def _normalize_embedding(values: List[float]) -> List[float]:
    norm = math.sqrt(sum(value * value for value in values))

    if norm == 0:
        return values

    return [value / norm for value in values]


def _embed_batch(
    texts: List[str],
    task_type: str,
) -> List[List[float]]:
    response = _get_client().models.embed_content(
        model=EMBEDDING_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(
            task_type=task_type,
            output_dimensionality=EMBEDDING_DIMENSION,
        ),
    )

    if not response.embeddings:
        raise RuntimeError("Gemini returned no embeddings.")

    if len(response.embeddings) != len(texts):
        raise RuntimeError("Unexpected number of embeddings returned.")

    embeddings = []

    for item in response.embeddings:
        if item.values is None:
            raise RuntimeError("Gemini returned an empty embedding.")

        if len(item.values) != EMBEDDING_DIMENSION:
            raise ValueError(
                f"Expected {EMBEDDING_DIMENSION} dimensions, "
                f"received {len(item.values)}."
            )

        embeddings.append(
            _normalize_embedding(list(item.values))
        )

    return embeddings


def get_embedding(text: str) -> List[float]:
    if not text or not text.strip():
        logger.warning("Received empty text.")
        return []

    try:
        logger.info("Generating Gemini query embedding.")

        return _embed_batch(
            [text],
            task_type="RETRIEVAL_QUERY",
        )[0]

    except Exception:
        logger.exception("Failed to generate query embedding.")
        raise


def get_embeddings_batch(
    texts: List[str],
) -> List[List[float]]:
    if not texts:
        logger.warning("Received an empty text list.")
        return []

    if any(not isinstance(text, str) or not text.strip() for text in texts):
        raise ValueError("All input texts must be non-empty strings.")

    try:
        logger.info(
            "Generating Gemini document embeddings for %d texts.",
            len(texts),
        )

        embeddings = []

        for start in range(0, len(texts), BATCH_SIZE):
            batch = texts[start:start + BATCH_SIZE]

            embeddings.extend(
                _embed_batch(
                    batch,
                    task_type="RETRIEVAL_DOCUMENT",
                )
            )

        logger.info(
            "Successfully generated %d embeddings.",
            len(embeddings),
        )

        return embeddings

    except Exception:
        logger.exception("Failed to generate batch embeddings.")
        raise