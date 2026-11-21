"""Glue code: build the prompt, call the LLM, parse and validate the questions."""

from llm_client import call_llm
from prompts import build_prompts
from quiz_parser import QuizParseError, parse_questions


def generate_questions(provider, model, api_key, category, topic, difficulty, n, max_attempts=2):
    """Return a list of `n` (or fewer) valid question dicts.

    Retries once with a stricter reminder if the reply cannot be parsed.
    Raises LLMError (network/API problems) or QuizParseError (bad replies).
    """
    system, user = build_prompts(category, topic, difficulty, n)
    last_error = None

    for _ in range(max_attempts):
        raw = call_llm(provider, model, api_key, system, user)
        try:
            return parse_questions(raw)[:n]
        except QuizParseError as exc:
            last_error = exc
            user += (
                "\n\nYour previous reply could not be used. Reply again with ONLY the JSON "
                "object in the exact shape shown, with 4 options per question."
            )

    raise last_error
