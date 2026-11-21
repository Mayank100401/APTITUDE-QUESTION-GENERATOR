"""Turn the raw LLM reply into clean, validated quiz questions."""

import json
import re

LETTERS = "ABCD"


class QuizParseError(ValueError):
    """Raised when the model reply cannot be turned into usable questions."""


def _extract_json(text: str):
    """Find and parse JSON inside the reply (handles ```json fences and extra text)."""
    if not isinstance(text, str) or not text.strip():
        raise QuizParseError("The model returned an empty reply.")
    text = text.strip()

    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if fence:
        text = fence.group(1).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    starts = [i for i in (text.find("{"), text.find("[")) if i != -1]
    if not starts:
        raise QuizParseError("No JSON found in the model reply.")
    start = min(starts)
    end = max(text.rfind("}"), text.rfind("]"))
    if end <= start:
        raise QuizParseError("Incomplete JSON in the model reply.")
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        raise QuizParseError(f"Invalid JSON from the model: {exc}") from exc


_PREFIX = re.compile(r"^\s*(?:\(?[A-Da-d]\)|[A-Da-d][.):])\s+")


def _clean_option(opt) -> str:
    return _PREFIX.sub("", str(opt)).strip()


def _normalise_answer(answer, options):
    """Return the answer as a letter A-D, or None if it cannot be understood."""
    if answer is None:
        return None
    ans = str(answer).strip()
    if not ans:
        return None

    # "B", "b", "B)", "B. 24"
    if ans[0].upper() in LETTERS and (len(ans) == 1 or ans[1] in ").:- "):
        return ans[0].upper()

    # "2" -> 2nd option (1-based)
    if ans.isdigit() and 1 <= int(ans) <= 4:
        return LETTERS[int(ans) - 1]

    # The answer text itself
    for i, opt in enumerate(options):
        if ans.lower() == opt.lower():
            return LETTERS[i]
    return None


def _validate(item):
    if not isinstance(item, dict):
        return None
    question = str(item.get("question", "")).strip()
    options = item.get("options")
    if not question or not isinstance(options, list) or len(options) != 4:
        return None
    options = [_clean_option(o) for o in options]
    if any(not o for o in options) or len({o.lower() for o in options}) != 4:
        return None
    answer = _normalise_answer(item.get("answer"), options)
    if answer is None:
        return None
    solution = str(item.get("solution") or item.get("explanation") or "").strip()
    return {
        "question": question,
        "options": options,
        "answer": answer,
        "solution": solution or "No solution provided.",
    }


def parse_questions(text: str):
    """Parse the LLM reply into a list of valid question dicts.

    Invalid questions are skipped; raises QuizParseError if none are usable.
    """
    data = _extract_json(text)
    if isinstance(data, dict):
        data = data.get("questions", data.get("data"))
    if not isinstance(data, list):
        raise QuizParseError("JSON does not contain a 'questions' list.")

    questions = [q for q in (_validate(item) for item in data) if q]
    if not questions:
        raise QuizParseError("No valid questions found in the model reply.")
    return questions
