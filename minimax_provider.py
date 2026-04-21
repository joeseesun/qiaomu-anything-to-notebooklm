"""MiniMax LLM provider for content analysis.

Provides an alternative to NotebookLM for the deep-analysis Q&A workflow,
using the MiniMax OpenAI-compatible Chat API.

Supported models:
  - MiniMax-M2.7            (default)
  - MiniMax-M2.7-highspeed
"""
from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

MINIMAX_BASE_URL = "https://api.minimax.io/v1"
MINIMAX_DEFAULT_MODEL = "MiniMax-M2.7"
MINIMAX_MODELS = ["MiniMax-M2.7", "MiniMax-M2.7-highspeed"]

# Maximum characters of content passed as system context (≈ 50 000 tokens worst-case)
MAX_CONTENT_LENGTH = 50_000


def _get_client(api_key: str | None = None, base_url: str | None = None):
    """Return an OpenAI-compatible client pointed at the MiniMax API."""
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ImportError(
            "The 'openai' package is required for the MiniMax provider. "
            "Install it with: pip install openai"
        ) from exc

    resolved_key = api_key or os.environ.get("MINIMAX_API_KEY")
    if not resolved_key:
        raise ValueError(
            "MiniMax API key is required. "
            "Set MINIMAX_API_KEY environment variable or pass api_key."
        )

    resolved_url = base_url or os.environ.get("MINIMAX_BASE_URL", MINIMAX_BASE_URL)
    return OpenAI(api_key=resolved_key, base_url=resolved_url)


def analyze_content(
    content: str,
    questions: list[str],
    *,
    model: str = MINIMAX_DEFAULT_MODEL,
    api_key: str | None = None,
    base_url: str | None = None,
) -> list[str]:
    """Answer *questions* about *content* using the MiniMax Chat API.

    Args:
        content:   The source text to analyse (will be truncated if too long).
        questions: List of questions to ask about the content.
        model:     MiniMax model ID to use (default: MiniMax-M2.7).
        api_key:   Override MINIMAX_API_KEY environment variable.
        base_url:  Override MINIMAX_BASE_URL environment variable.

    Returns:
        List of answer strings, one per question.
    """
    client = _get_client(api_key=api_key, base_url=base_url)
    truncated = content[:MAX_CONTENT_LENGTH]

    system_prompt = (
        "You are an expert content analyst. "
        "Read the following content carefully and answer every question concisely and accurately.\n\n"
        f"--- CONTENT START ---\n{truncated}\n--- CONTENT END ---"
    )

    answers: list[str] = []
    for question in questions:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            temperature=1.0,
            max_tokens=1024,
        )
        answer = response.choices[0].message.content or ""
        answers.append(answer)

    return answers
