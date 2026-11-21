"""PS50 - Aptitude Question Generator (Streamlit app).

Run with:  streamlit run app.py
"""

import csv
import io
import json
import os
import random
from pathlib import Path

import streamlit as st

try:  # optional: load API keys from a .env file
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from generator import generate_questions
from llm_client import PROVIDERS, LLMError
from prompts import DIFFICULTY_NOTES, TOPICS
from quiz_parser import LETTERS, QuizParseError

SAMPLE_FILE = Path(__file__).parent / "sample_questions.json"

st.set_page_config(page_title="Aptitude Question Generator", page_icon="🧮", layout="centered")

# ---------------------------------------------------------------- state
defaults = {"questions": [], "submitted": False, "show_solution": {}, "quiz_id": 0, "meta": ""}
for key, value in defaults.items():
    st.session_state.setdefault(key, value)


def toggle_solution(i):
    shown = st.session_state.show_solution
    shown[i] = not shown.get(i, False)


def submit_quiz():
    st.session_state.submitted = True


def retry_quiz():
    st.session_state.submitted = False
    st.session_state.show_solution = {}
    st.session_state.quiz_id += 1  # new widget keys -> answers are cleared


def load_demo_questions(n):
    data = json.loads(SAMPLE_FILE.read_text(encoding="utf-8"))["questions"]
    random.shuffle(data)
    return data[:n]


def questions_to_csv(questions):
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["No", "Question", "A", "B", "C", "D", "Answer", "Solution"])
    for i, q in enumerate(questions, 1):
        writer.writerow([i, q["question"], *q["options"], q["answer"], q["solution"]])
    return buf.getvalue()


# ------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    demo_mode = st.checkbox("Demo mode (no API key needed)", value=False,
                            help="Uses a few built-in sample questions. Good for testing the UI.")
    provider = model = api_key = None
    if not demo_mode:
        provider = st.selectbox("LLM provider", list(PROVIDERS))
        info = PROVIDERS[provider]
        model = st.text_input("Model", value=info["model"], key=f"model_{provider}")
        if info["env"]:
            env_key = os.getenv(info["env"], "")
            api_key = st.text_input(
                f"{provider} API key",
                value=env_key,
                type="password",
                help=f"Or set {info['env']} in your .env file.",
            )
        else:
            st.caption("Make sure Ollama is running: `ollama serve` and the model is pulled.")
    st.divider()
    st.caption("AI-generated questions can contain mistakes. Always verify before using them for real tests.")

# ---------------------------------------------------------------- main
st.title("🧮 Aptitude Question Generator")
st.write("Generate placement-style aptitude and reasoning questions with answers and step-by-step solutions.")

col1, col2 = st.columns(2)
category = col1.selectbox("Category", list(TOPICS))
topic = col2.selectbox("Topic", TOPICS[category])
col3, col4 = st.columns(2)
difficulty = col3.radio("Difficulty", list(DIFFICULTY_NOTES), index=1, horizontal=True)
count = col4.slider("Number of questions", 3, 10, 5)

if st.button("✨ Generate questions", type="primary"):
    try:
        with st.spinner("Generating questions..."):
            if demo_mode:
                questions = load_demo_questions(count)
            else:
                questions = generate_questions(provider, model, api_key, category, topic, difficulty, count)
        st.session_state.questions = questions
        st.session_state.meta = (
            "Demo questions" if demo_mode else f"{topic} · {difficulty} · {provider} ({model})"
        )
        retry_quiz()
    except LLMError as exc:
        st.error(f"LLM problem: {exc}")
    except QuizParseError as exc:
        st.error(f"The model reply could not be read as questions ({exc}). Please click Generate again.")

questions = st.session_state.questions

if questions:
    st.divider()
    st.subheader("📝 Quiz")
    st.caption(st.session_state.meta)

    submitted = st.session_state.submitted
    score = 0

    for i, q in enumerate(questions):
        st.markdown(f"**Q{i + 1}. {q['question']}**")
        choice = st.radio(
            f"Answer for question {i + 1}",
            options=list(range(4)),
            format_func=lambda k, q=q: f"{LETTERS[k]}. {q['options'][k]}",
            index=None,
            key=f"ans_{st.session_state.quiz_id}_{i}",
            disabled=submitted,
            label_visibility="collapsed",
        )
        correct_idx = LETTERS.index(q["answer"])

        if submitted:
            if choice == correct_idx:
                score += 1
                st.success("Correct ✅")
            elif choice is None:
                st.warning(f"Not answered. Correct answer: {q['answer']}. {q['options'][correct_idx]}")
            else:
                st.error(f"Wrong ❌  Correct answer: {q['answer']}. {q['options'][correct_idx]}")

        shown = st.session_state.show_solution.get(i, False)
        st.button(
            "Hide solution" if shown else "Show solution",
            key=f"sol_btn_{st.session_state.quiz_id}_{i}",
            on_click=toggle_solution,
            args=(i,),
        )
        if shown:
            st.info(f"**Answer: {q['answer']}. {q['options'][correct_idx]}**\n\n{q['solution']}")
        st.write("")

    if not submitted:
        st.button("✅ Submit answers", type="primary", on_click=submit_quiz)
    else:
        st.subheader(f"Your score: {score} / {len(questions)}")
        st.progress(score / len(questions))
        st.button("🔁 Retry same questions", on_click=retry_quiz)

    st.divider()
    d1, d2 = st.columns(2)
    d1.download_button("⬇️ Download JSON", json.dumps({"questions": questions}, indent=2),
                       file_name="aptitude_questions.json", mime="application/json")
    d2.download_button("⬇️ Download CSV", questions_to_csv(questions),
                       file_name="aptitude_questions.csv", mime="text/csv")
