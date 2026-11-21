## Problem statement
Placement preparation needs a large amount of practice material. This tool generates aptitude and reasoning
questions with four options, the correct answer and a step-by-step solution, based on the topic and difficulty
chosen by the student. It helps students practise on demand and teachers prepare quick practice sets.

## Tools & model
- Language: Python 3
- Libraries: Streamlit (UI), requests (API calls), python-dotenv (API key from .env)
- LLM: <the one you actually used, e.g. Gemini 2.5 Flash via API / Llama 3.3 70B via Groq / Llama 3.2 via Ollama>

## Procedure
1. Read the problem statement and decided the inputs: category, topic, difficulty and number of questions.
2. Created a free API key (<provider>) and stored it in a `.env` file that is excluded by `.gitignore`.
3. Tested the prompt in the provider playground with 3-5 topics before writing code.
4. Wrote `prompts.py` with the topic list and a prompt that asks for JSON only.
5. Wrote `llm_client.py` to send the prompt to the provider and return the reply text.
6. Wrote `quiz_parser.py` to extract the JSON (even inside markdown fences), remove option prefixes such as "A)",
   and drop invalid questions (not 4 options, duplicate options, unclear answer).
7. Wrote `generator.py` to join the steps and retry once if the reply cannot be parsed.
8. Built the Streamlit UI in `app.py`: radio buttons, Submit, score with progress bar, Show/Hide solution
   button, Retry, and JSON/CSV download.

**Improvement made:** in the first version the model gave the answer letter before the working and sometimes
the letter did not match the solution. Asking for the solution first and the answer last made them agree.

## Challenges
- Model replies sometimes had extra text or ```json fences -> fixed by extracting the JSON in `quiz_parser.py`.
- Options sometimes started with "A)" -> removed with a regular expression.
- API rate limits (429) -> show a clear message and wait before retrying.
- Some generated answers can be wrong -> added a visible warning to verify the questions.


## Conclusion
The app generates topic-wise aptitude quizzes with solutions and a score. It sometimes produces wrong answers on
hard questions because the LLM does not verify its own maths. Future improvement: check numeric answers with
Python/sympy and add a timer mode.

