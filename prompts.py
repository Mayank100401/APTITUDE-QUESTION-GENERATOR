"""Topic lists and prompt templates for the Aptitude Question Generator."""

TOPICS = {
    "Quantitative Aptitude": [
        "Percentages",
        "Profit and Loss",
        "Ratio and Proportion",
        "Time and Work",
        "Time, Speed and Distance",
        "Simple and Compound Interest",
        "Averages",
        "Probability",
        "Permutation and Combination",
        "Number Series",
    ],
    "Logical Reasoning": [
        "Blood Relations",
        "Coding-Decoding",
        "Direction Sense",
        "Syllogisms",
        "Seating Arrangement",
        "Clocks and Calendars",
    ],
    "Verbal Ability": [
        "Synonyms and Antonyms",
        "Sentence Correction",
        "Odd One Out",
    ],
}

DIFFICULTY_NOTES = {
    "Easy": "Easy: one-step or two-step problems with small, friendly numbers.",
    "Medium": "Medium: typical campus-placement level, 2-3 steps of working.",
    "Hard": "Hard: tricky multi-step problems like those in top-company placement tests.",
}

SYSTEM_PROMPT = (
    "You are an expert aptitude test setter for campus placement exams in India. "
    "You write accurate, unambiguous questions and double-check every calculation. "
    "You reply with ONE valid JSON object and nothing else - no markdown, no commentary."
)

USER_PROMPT_TEMPLATE = """Create {n} multiple-choice aptitude questions.

Category   : {category}
Topic      : {topic}
Difficulty : {difficulty_note}

Rules:
- Each question has exactly 4 options and exactly ONE correct option.
- Options must be plain text WITHOUT letter prefixes (no "A)", "B." etc).
- Wrong options must be plausible (typical student mistakes), and all 4 options must be different.
- Questions must be different from each other and self-contained.
- Write the step-by-step "solution" FIRST, work the problem out carefully, and only then give the "answer" letter (A, B, C or D) that matches your working.
- Keep each solution short (2-5 lines).

Return JSON in exactly this shape:
{{"questions": [
  {{"question": "...", "options": ["...", "...", "...", "..."], "solution": "...", "answer": "B"}}
]}}
"""


def build_prompts(category: str, topic: str, difficulty: str, n: int):
    """Return (system_prompt, user_prompt) for the chosen settings."""
    user = USER_PROMPT_TEMPLATE.format(
        n=n,
        category=category,
        topic=topic,
        difficulty_note=DIFFICULTY_NOTES.get(difficulty, difficulty),
    )
    return SYSTEM_PROMPT, user
