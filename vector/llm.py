"""Ollama chat client."""

import requests

from vector import config


class LLMError(Exception):
    pass


def chat(messages: list[dict], num_predict: int = config.MAX_REPLY_TOKENS) -> str:
    payload = {
        "model": config.MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": config.TEMPERATURE,
            "top_p": config.TOP_P,
            "num_predict": num_predict,
        },
    }
    try:
        res = requests.post(config.OLLAMA_URL, json=payload, timeout=config.REQUEST_TIMEOUT)
        res.raise_for_status()
    except requests.Timeout as e:
        raise LLMError("model timed out") from e
    except requests.RequestException as e:
        raise LLMError(f"cannot reach Ollama at {config.OLLAMA_URL} — is `ollama serve` running?") from e
    return res.json().get("message", {}).get("content", "").strip()


def infer_intent(user_input: str) -> str:
    return chat(
        [
            {"role": "system", "content": "State the user's intent in one short line. Nothing else."},
            {"role": "user", "content": user_input},
        ],
        num_predict=30,
    )
