import os
import json
import requests
import time
from dotenv import load_dotenv
from utils.config import get_config
from utils.logger import get_logger

load_dotenv()
log = get_logger("ai_client")


def _import_ollama():
    """Lazy-import ollama library if available."""
    try:
        import ollama
        return ollama
    except ImportError:
        return None


class AIClient:
    def __init__(self, provider=None):
        cfg = get_config()
        self.provider = provider or cfg.get("ai", {}).get("provider", "openrouter")
        self.api_key = os.getenv("OPENROUTER_API_KEY")

        if self.provider == "ollama":
            self.base_url = cfg.get("ai", {}).get("ollama_url", "http://localhost:11434")
            self.model = cfg.get("ai", {}).get("ollama_model", "qwen2.5:7b")
            self._ollama = _import_ollama()
        else:
            self.base_url = "https://openrouter.ai/api/v1/chat/completions"
            self.model = cfg.get("ai", {}).get("model", "openrouter/auto")
            self.fallbacks = cfg.get("ai", {}).get("fallback_models", [])

        self.temperature = cfg.get("ai", {}).get("temperature", 0.15)
        self.timeout = cfg.get("ai", {}).get("timeout", 90)

        if self.provider == "ollama":
            log.info(f"AI provider: Ollama ({self.model} @ {self.base_url})")
        else:
            log.info(f"AI provider: OpenRouter ({self.model})")

    def switch_provider(self, provider, model=None):
        old_provider = self.provider
        self.provider = provider
        cfg = get_config()
        if provider == "ollama":
            self.base_url = cfg.get("ai", {}).get("ollama_url", "http://localhost:11434")
            self.model = model or cfg.get("ai", {}).get("ollama_model", "qwen2.5:7b")
            self._ollama = _import_ollama()
            log.info(f"Switched to Ollama ({self.model})")
        else:
            self.base_url = "https://openrouter.ai/api/v1/chat/completions"
            self.model = model or cfg.get("ai", {}).get("model", "openrouter/auto")
            self.fallbacks = cfg.get("ai", {}).get("fallback_models", [])
            log.info(f"Switched to OpenRouter ({self.model})")
        return old_provider != self.provider

    def ask(self, messages, temperature=None, timeout=None):
        if self.provider == "ollama":
            return self._ask_ollama(messages, temperature, timeout)
        return self._ask_openrouter(messages, temperature, timeout)

    def _ask_ollama(self, messages, temperature=None, timeout=None):
        temp = temperature or self.temperature
        t_out = timeout or self.timeout

        if self._ollama:
            try:
                resp = self._ollama.chat(
                    model=self.model,
                    messages=messages,
                    options={"temperature": temp},
                    host=self.base_url,
                )
                content = resp.get("message", {}).get("content", "")
                if content:
                    log.info(f"Ollama response ({len(content)} chars)")
                    return content
            except Exception as e:
                log.warning(f"Ollama library error: {e}")

        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "options": {"temperature": temp},
                "stream": False,
            }
            resp = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=t_out,
            )
            resp.raise_for_status()
            result = resp.json()
            content = result.get("message", {}).get("content", "")
            if content:
                log.info(f"Ollama HTTP response ({len(content)} chars)")
                return content
            log.warning("Ollama returned empty response")
            return None
        except requests.exceptions.ConnectionError:
            log.error(f"Cannot connect to Ollama at {self.base_url}")
            return json.dumps({"done": True, "summary": f"Ollama unreachable at {self.base_url}. Is it running?"})
        except Exception as e:
            log.error(f"Ollama error: {e}")
            return json.dumps({"done": True, "summary": f"Ollama error: {str(e)}"})

    def _ask_openrouter(self, messages, temperature=None, timeout=None):
        if not self.api_key:
            log.error("OPENROUTER_API_KEY not set")
            return None

        temp = temperature or self.temperature
        t_out = timeout or self.timeout
        errors = []
        models_to_try = [self.model] + getattr(self, "fallbacks", [])

        for attempt_idx, model in enumerate(models_to_try):
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:7777",
                    "X-Title": "PORT-777",
                }
                data = {"model": model, "messages": messages, "temperature": temp}
                resp = requests.post(self.base_url, headers=headers, json=data, timeout=t_out)
                resp.raise_for_status()
                result = resp.json()
                content = result["choices"][0]["message"]["content"]
                log.info(f"OpenRouter response ({len(content)} chars)")
                return content
            except requests.exceptions.Timeout:
                err = f"Timeout for {model}"
                log.warning(err); errors.append(err)
                continue
            except requests.exceptions.HTTPError as e:
                err = f"HTTP {e.response.status_code} for {model}"
                log.warning(err); errors.append(err)
                if attempt_idx < len(models_to_try) - 1:
                    time.sleep(1)
                continue
            except Exception as e:
                err = str(e)
                log.warning(f"Model {model} failed: {err}")
                errors.append(err)
                continue

        log.error(f"All {len(models_to_try)} OpenRouter models failed")
        return json.dumps({
            "done": True,
            "summary": f"AI unavailable. Errors: {'; '.join(errors[-3:])}"
        })

    def list_providers(self):
        return ["openrouter", "ollama"]

    def list_local_models(self):
        if self.provider != "ollama":
            return []
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            resp.raise_for_status()
            data = resp.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            log.warning(f"Cannot list Ollama models: {e}")
            return []



