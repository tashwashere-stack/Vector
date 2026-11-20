"""Ollama chat client (streaming)."""

import json
from collections.abc import Iterator

import requests

from vector import config


class LLMError(Exception):
    pass


def _payload(messages: list[dict], num_predict: int, stream: bool) -> dict:
    return {
        "model": config.MODEL,
        "messages": messages,
        "stream": stream,
        "keep_alive": config.KEEP_ALIVE,
        "options": {
            "temperature": config.TEMPERATURE,
            "top_p": config.TOP_P,
            "num_predict": num_predict,
            "num_ctx": config.NUM_CTX,
            "stop": config.STOP,
        },
    }


def stream_chat(messages: list[dict], num_predict: int = config.MAX_REPLY_TOKENS) -> Iterator[str]:
    """Yield reply text pieces as the model generates them."""
    try:
        with requests.post(config.OLLAMA_URL, json=_payload(messages, num_predict, True),
                           stream=True, timeout=config.REQUEST_TIMEOUT) as res:
            res.raise_for_status()
            for line in res.iter_lines():
                if not line:
                    continue
                data = json.loads(line)
                if "error" in data:
                    raise LLMError(data["error"])
                if piece := data.get("message", {}).get("content"):
                    yield piece
                if data.get("done"):
                    return
    except requests.Timeout as e:
        raise LLMError("model timed out") from e
    except requests.RequestException as e:
        raise LLMError(f"cannot reach Ollama at {config.OLLAMA_URL} — is `ollama serve` running?") from e


def chat(messages: list[dict], num_predict: int = config.MAX_REPLY_TOKENS) -> str:
    return "".join(stream_chat(messages, num_predict)).strip()


def warm_up(messages: list[dict]) -> None:
    """Load the model and pre-compute the static prompt prefix (KV cache)."""
    chat(messages, num_predict=1)


def infer_intent(user_input: str) -> str:
    return chat(
        [
            {"role": "system", "content": "State the user's intent in one short line. Nothing else."},
            {"role": "user", "content": user_input},
        ],
        num_predict=30,
    )
