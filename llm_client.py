"""Tiny LLM client supporting Gemini, Groq, OpenAI and a local Ollama model.

Only the `requests` library is used, so no provider SDK is needed.
"""

import requests

PROVIDERS = {
    "Gemini": {"model": "gemini-3.8-flash", "env": "GEMINI_API_KEY"},
    "Groq": {"model": "llama-3.3-70b-versatile", "env": "GROQ_API_KEY"},
    "OpenAI": {"model": "gpt-4o-mini", "env": "OPENAI_API_KEY"},
    "Ollama (local)": {"model": "llama3.2", "env": None},
}

TIMEOUT = 90  # seconds

OPENAI_STYLE_URLS = {
    "Groq": "https://api.groq.com/openai/v1/chat/completions",
    "OpenAI": "https://api.openai.com/v1/chat/completions",
}


class LLMError(RuntimeError):
    """Raised for any problem talking to the LLM provider."""


def _post(url, headers, payload):
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=TIMEOUT)
    except requests.exceptions.ConnectionError as exc:
        raise LLMError(
            "Could not connect. Check your internet connection "
            "(or that Ollama is running for the local option)."
        ) from exc
    except requests.exceptions.Timeout as exc:
        raise LLMError("The request timed out. Try again or reduce the question count.") from exc

    if resp.status_code != 200:
        try:
            detail = resp.json()
        except ValueError:
            detail = resp.text[:300]
        if resp.status_code in (401, 403):
            raise LLMError(f"API key rejected ({resp.status_code}). Check your key. Details: {detail}")
        if resp.status_code == 429:
            raise LLMError("Rate limit reached (429). Wait a minute and try again.")
        raise LLMError(f"Provider error {resp.status_code}: {detail}")

    try:
        return resp.json()
    except ValueError as exc:
        raise LLMError("The provider returned a non-JSON response.") from exc


def _call_gemini(model, api_key, system, user, temperature):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {"Content-Type": "application/json", "x-goog-api-key": api_key}
    payload = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {
            "temperature": temperature,
            "responseMimeType": "application/json",
        },
    }
    data = _post(url, headers, payload)
    try:
        parts = data["candidates"][0]["content"]["parts"]
        return "".join(p.get("text", "") for p in parts)
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMError(f"Unexpected Gemini response: {str(data)[:300]}") from exc


def _call_openai_style(provider, model, api_key, system, user, temperature):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    payload = {
        "model": model,
        "temperature": temperature,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    data = _post(OPENAI_STYLE_URLS[provider], headers, payload)
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMError(f"Unexpected {provider} response: {str(data)[:300]}") from exc


def _call_ollama(model, system, user, temperature):
    payload = {
        "model": model,
        "stream": False,
        "format": "json",
        "options": {"temperature": temperature},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    data = _post("http://localhost:11434/api/chat", {"Content-Type": "application/json"}, payload)
    try:
        return data["message"]["content"]
    except (KeyError, TypeError) as exc:
        raise LLMError(f"Unexpected Ollama response: {str(data)[:300]}") from exc


def call_llm(provider, model, api_key, system, user, temperature=0.7):
    """Send one prompt to the chosen provider and return the reply text."""
    if provider not in PROVIDERS:
        raise LLMError(f"Unknown provider: {provider}")
    if provider != "Ollama (local)" and not api_key:
        raise LLMError(f"No API key for {provider}. Enter it in the sidebar or put it in the .env file.")

    if provider == "Gemini":
        return _call_gemini(model, api_key, system, user, temperature)
    if provider in OPENAI_STYLE_URLS:
        return _call_openai_style(provider, model, api_key, system, user, temperature)
    return _call_ollama(model, system, user, temperature)
