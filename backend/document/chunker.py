import re
import logging
from typing import List

logger = logging.getLogger(__name__)

# Splits the Chunks into Overlapping Chunks while Respecting the Boundaries
# Prepare the Data for Vector Embeddings and Semantic Search
def chunk_text(
        text: str, 
        chunk_size: int = 5, 
        overlap: int = 1
    ) -> List[str]:
    if not text:
        logger.warning("Received the Empty Text..")
        return []
    if chunk_size <= 0:
        raise ValueError("Chunk Size Must be Greater than 0")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "Overlap Must is >= 0 and must be Smaller than chunks size"
        )
    logger.debug(
        "Starting the Chunking Text Len: %d Chars," 
        "Max Size: %d and "
        "Overlap: %d",
        len(text), 
        chunk_size,
        overlap
    )
    raw_lines = re.split(
        r'\n|•|(?<=\s)-(?=\s)',
        str(text)
    )
    # Clean lines and remove very short/junk lines.
    cleaned_lines = []
    for line in raw_lines:
        clean_line = re.sub(r'\s+', ' ', line).strip()
        if len(clean_line) > 5:
            cleaned_lines.append(clean_line)

    chunks = []
    step = chunk_size - overlap
    for i in range(0, len(cleaned_lines), step):
        chunk_lines = cleaned_lines[i:i + chunk_size]
        if not chunk_lines:
            continue
        chunk = "\n".join(chunk_lines)
        chunks.append(chunk)
        # Stop when the final chunk has been reached.
        if i+chunk_size >= len(cleaned_lines):
            break

    logger.debug(
        "Successfully generated %d resume-aware chunks.",
        len(chunks)
    )
    return chunks

