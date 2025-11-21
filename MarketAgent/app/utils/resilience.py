import json
import re
import sys
from typing import Any, Callable, Dict

from loguru import logger
from tenacity import (
    after_log,
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


def setup_logging():
    """Configures loguru to log to file and stderr."""
    logger.remove()  # Remove default handler

    # Log to console (stderr)
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
    )

    # Log to file with rotation
    logger.add(
        "logs/market_agent.log",
        rotation="10 MB",
        retention="1 week",
        level="DEBUG",
        compression="zip",
    )


def clean_json_response(raw_text: str) -> Dict[str, Any]:
    """
    Attempts to clean and parse a JSON string from an LLM response.
    Removes markdown code blocks and handles common formatting errors.
    """
    # Remove markdown code blocks (```json ... ```)
    text = re.sub(r"```json\s*", "", raw_text)
    text = re.sub(r"```\s*$", "", text)
    text = text.strip()

    # Try to find the first '{' and last '}'
    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1:
        text = text[start: end + 1]

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}. Raw Text: {raw_text}")
        raise


# Decorator for API calls
retry_api_call = retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    before_sleep=before_sleep_log(logger, "WARNING"),
    after=after_log(logger, "INFO"),
)