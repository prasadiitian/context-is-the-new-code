"""model.py -- the one place the engine talks to a model."""
import json
import os
import time
import urllib.error
import urllib.request

RETRY_ON = {429, 500, 502, 503, 504}     # busy or rate-limited


class ModelError(RuntimeError):
    """The model could not be reached or gave no usable reply."""


def load_env(path: str = ".env") -> None:
    """Read KEY=VALUE lines from a .env file, if there is one."""
    if not os.path.exists(path):
        return
    with open(path) as handle:
        for line in handle:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                value = value.strip().strip('"').strip("'")
                os.environ.setdefault(key.strip(), value)


load_env()


class ScriptedModel:
    """Replays fixed replies. For tests and for running offline."""
    name = "scripted"

    def __init__(self, replies):
        self.replies = list(replies)
        self.requests = []           # every request it was sent

    def complete(self, request) -> str:
        self.requests.append(request)
        return self.replies.pop(0)


class HttpModel:
    """Any endpoint that speaks the chat-completions format."""

    def __init__(self, url=None, model=None, key=None):
        self.url = url or os.environ["MODEL_URL"]
        self.name = model or os.environ["MODEL_NAME"]
        self.key = key or os.environ.get("MODEL_KEY", "")
        self.usage = {}              # token counts from last call

    def complete(self, request) -> str:
        body = {"model": self.name, "messages": to_wire(request)}
        req = urllib.request.Request(
            self.url, data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {self.key}"})
        for _ in range(3):           # a reply can come back empty
            reply = send(req)
            self.usage = reply.get("usage", {})
            choice = (reply.get("choices") or [{}])[0]
            text = (choice.get("message") or {}).get("content")
            if text:
                return text
        reason = choice.get("finish_reason", "not given")
        raise ModelError(
            f"model returned no text three times "
            f"(finish reason: {reason})")


def send(req, attempts: int = 4, wait: float = 2.0) -> dict:
    """Send a request. Retry when the provider is busy."""
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as error:
            detail = error.read().decode(errors="replace")[:300]
            if error.code not in RETRY_ON or attempt == attempts:
                raise ModelError(
                    f"model call failed with HTTP {error.code}: "
                    f"{detail}") from None
            time.sleep(wait * 2 ** (attempt - 1))


def to_wire(request) -> list[dict]:
    """Drop our source tags; keep only what the model should get."""
    wire = [{"role": "system", "content": request["system"]}]
    for msg in request["messages"]:
        role = "user" if msg["role"] == "tool" else msg["role"]
        wire.append({"role": role, "content": msg["content"]})
    return wire


def get_model(fallback_replies):
    """A real model when MODEL_URL is set, else a scripted one."""
    if os.environ.get("MODEL_URL"):
        return HttpModel()
    return ScriptedModel(fallback_replies)
