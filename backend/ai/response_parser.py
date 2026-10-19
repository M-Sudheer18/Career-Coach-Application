import re
import json
import logging
from typing import Dict, Union, Any

logger = logging.getLogger(__name__)




# Forces an LLM response into a valid Python dictionary
def parse_json_response(raw_response: str) -> Dict[str, Any]:

    if not raw_response or not raw_response.strip():
        logger.error("Empty response received for JSON parsing.")
        raise ValueError("Response can't be empty.")

    raw_response = raw_response.strip()

    # Remove Markdown code fences
    json_match = re.search(
        r"```(?:json)?\s*(.*?)\s*```",
        raw_response,
        re.DOTALL | re.IGNORECASE
    )

    if json_match:
        clean_string = json_match.group(1).strip()
    else:
        clean_string = raw_response

    # Temporary
    # Try normal JSON parsing
    try:
        parsed_data = json.loads(clean_string)

        if isinstance(parsed_data, dict):
            return parsed_data

        # Valid JSON but not a dict (e.g. a list). Don't raise here —
        # that used to escape this function's error handling and get
        # caught by rag.py's outer except instead.
        logger.warning(
            "Parsed JSON was valid but not a dict (got %s). Wrapping it.",
            type(parsed_data).__name__
        )
        return {"data": parsed_data}

    except json.JSONDecodeError:
        logger.debug(
            "Direct JSON parsing failed. "
            "Trying to extract JSON object."
        )


    # Try normal JSON parsing
    # try:
    #     parsed_data = json.loads(clean_string)

    #     if not isinstance(parsed_data, dict):
    #         raise ValueError(
    #             "Parsed JSON data is not a dictionary."
    #         )

    #     return parsed_data

    # except json.JSONDecodeError:
    #     logger.debug(
    #         "Direct JSON parsing failed. "
    #         "Trying to extract JSON object."
    #     )

    # # Try to find JSON inside other text
    # json_object_match = re.search(
    #     r"\{.*\}",
    #     clean_string,
    #     re.DOTALL
    # )

    # if json_object_match:
    #     extracted_json = json_object_match.group(0).strip()
    #     try:
    #         parsed_data = json.loads(extracted_json)
    #         if not isinstance(parsed_data, dict):
    #             raise ValueError(
    #                 "Extracted JSON data is not a dictionary."
    #             )
    #         return parsed_data
    #     except json.JSONDecodeError:
    #         pass

        # Try to find JSON inside other text.
    # NOTE: using a non-greedy/bounded scan instead of r"\{.*\}",
    # because that greedy regex grabs from the first '{' to the LAST '}'
    # in the whole string -- including any trailing commentary the
    # model added after the JSON (e.g. "...}\n\nLet me know if..."),
    # which produces a malformed blob that fails to parse.
    start = clean_string.find("{")
    if start != -1:
        depth = 0
        in_string = False
        escape = False
        for idx in range(start, len(clean_string)):
            c = clean_string[idx]
            if in_string:
                if escape:
                    escape = False
                elif c == "\\":
                    escape = True
                elif c == '"':
                    in_string = False
                continue
            if c == '"':
                in_string = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    extracted_json = clean_string[start:idx + 1]
                    try:
                        parsed_data = json.loads(extracted_json)
                        if isinstance(parsed_data, dict):
                            return parsed_data
                        return {"data": parsed_data}
                    except json.JSONDecodeError:
                        pass
                    break

    # JSON parsing completely failed
    logger.error("Failed to parse AI response as JSON.")

    logger.debug(
        "Raw AI Output:\n%s",
        raw_response
    )

    return {
        "error": "Failed to parse the AI Response",
        "raw_text": raw_response
    }


# TEXT RESPONSE PARSER
# Clean a normal text response from the LLM.
# Useful for 'career_coach', 'ai_interview', and 'cover_letter'
def parse_text_response(raw_response: str) -> str:

    if not raw_response:
        return ""

    clean_text = raw_response.strip()

    # Remove conversational filler if the AI ignores instructions
    filter_phrases = [
        "Here is the Cover Letter:",
        "Here is the Response:",
        "Certainly!",
        "Sure!",
        "Sure,"
    ]

    for phrase in filter_phrases:
        if clean_text.lower().startswith(phrase.lower()):
            clean_text = clean_text[len(phrase):].strip()
    return clean_text


def process_ai_output(
    raw_response: str,
    expected_format: str = "text"
) -> Union[str, Dict[str, Any]]:

    if expected_format.lower() == "json":
        return parse_json_response(raw_response)

    return parse_text_response(raw_response)