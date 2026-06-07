"""
ALLICE — Ollama Client
Handles streaming communication with the local Ollama API.
"""

import json
import requests
from typing import Generator, Callable


OLLAMA_BASE = "http://localhost:11434"
AVAILABLE_MODELS = [
    "qwen2.5-coder:7b",
    "qwen3:4b",
    "llama3.2:3b",
    "codellama:7b",
    "mistral:7b",
]


class OllamaClient:
    def __init__(self, model: str = "qwen2.5-coder:7b"):
        self.model = model
        self.base_url = OLLAMA_BASE
        self.chat_url = f"{self.base_url}/api/chat"

    def set_model(self, model: str):
        self.model = model

    def is_available(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return r.ok
        except Exception:
            return False

    def list_models(self) -> list[str]:
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if r.ok:
                data = r.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            pass
        return AVAILABLE_MODELS

    def stream_chat(
        self,
        messages: list[dict],
        on_token: Callable[[str], None],
        on_done: Callable[[str], None],
        on_error: Callable[[str], None],
    ):
        """
        Stream a chat response token by token.
        Calls on_token(chunk) for each partial response,
        on_done(full_reply) when complete,
        on_error(message) on failure.
        """
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": True,
            }

            with requests.post(
                self.chat_url,
                json=payload,
                stream=True,
                timeout=120,
            ) as res:
                if not res.ok:
                    on_error(f"Ollama error {res.status_code}: {res.text[:200]}")
                    return

                full_reply = ""

                for line in res.iter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        # /api/chat format
                        chunk = data.get("message", {}).get("content", "")
                        # fallback: /api/generate format
                        if not chunk:
                            chunk = data.get("response", "")

                        if chunk:
                            full_reply += chunk
                            on_token(chunk)

                        if data.get("done"):
                            break

                    except json.JSONDecodeError:
                        continue

                on_done(full_reply)

        except requests.exceptions.ConnectionError:
            on_error(
                "Cannot connect to Ollama. Make sure Ollama is running:\n"
                "  $ ollama serve"
            )
        except Exception as e:
            on_error(f"Unexpected error: {e}")
