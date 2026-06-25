"""Tiny sync client for any OpenAI-compatible /chat/completions endpoint.

One code path for vllm, ollama and openai. Streams SSE; tolerates the framing
differences between servers; falls back to a plain JSON POST if streaming isn't
really happening. Tool calls are read AFTER the stream ends, never from deltas.
"""

from __future__ import annotations

import json

import httpx

DEFAULT_TEMPERATURE = 0.4
DEFAULT_MAX_TOKENS = 1024


class LLMError(Exception):
    pass


class Client:
    def __init__(self, base_url: str, api_key: str, model: str, timeout: float = 120.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or ""
        self.model = model
        self.timeout = timeout
        # populated after each chat_stream call
        self.last_content: str = ""
        self.last_tool_calls: list[dict] = []

    # -- internals -----------------------------------------------------------

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def _url(self) -> str:
        return f"{self.base_url}/chat/completions"

    def _body(self, messages, tools, stream, max_tokens=None) -> dict:
        body = {
            "model": self.model,
            "messages": messages,
            "temperature": DEFAULT_TEMPERATURE,
            "max_tokens": max_tokens or DEFAULT_MAX_TOKENS,
            "stream": stream,
        }
        if tools:
            body["tools"] = tools
        return body

    @staticmethod
    def _merge_tool_calls(acc: dict, deltas) -> None:
        """Accumulate streamed tool_call fragments keyed by index."""
        for d in deltas or []:
            idx = d.get("index", 0)
            slot = acc.setdefault(idx, {"function": {"name": "", "arguments": ""}})
            if d.get("id"):
                slot["id"] = d["id"]
            fn = d.get("function") or {}
            if fn.get("name"):
                slot["function"]["name"] = fn["name"]
            if fn.get("arguments"):
                slot["function"]["arguments"] += fn["arguments"]

    # -- public --------------------------------------------------------------

    def chat_stream(self, messages, tools=None):
        """Yield text deltas. After exhaustion, read .last_content / .last_tool_calls."""
        self.last_content = ""
        self.last_tool_calls = []
        tool_acc: dict = {}
        content_parts: list[str] = []
        saw_stream = False

        try:
            with httpx.stream(
                "POST",
                self._url(),
                headers=self._headers(),
                json=self._body(messages, tools, stream=True),
                timeout=self.timeout,
            ) as resp:
                if resp.status_code >= 400:
                    body = resp.read().decode("utf-8", "replace")
                    raise LLMError(f"server returned {resp.status_code}: {body[:300]}")

                for line in resp.iter_lines():
                    if not line:
                        continue
                    if not line.startswith("data:"):
                        # not SSE after all — bail to non-streaming fallback
                        break
                    saw_stream = True
                    data = line[len("data:") :].strip()
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                    except Exception:
                        continue
                    choices = chunk.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    piece = delta.get("content")
                    if piece:
                        content_parts.append(piece)
                        yield piece
                    if delta.get("tool_calls"):
                        self._merge_tool_calls(tool_acc, delta["tool_calls"])
        except httpx.HTTPError as e:
            raise LLMError(f"could not reach model server: {e}") from e

        if not saw_stream:
            # Fallback: plain non-streaming request.
            text, calls = self._complete(messages, tools)
            self.last_content = text
            self.last_tool_calls = calls
            if text:
                yield text
            return

        self.last_content = "".join(content_parts)
        self.last_tool_calls = [tool_acc[k] for k in sorted(tool_acc)]

    def _complete(self, messages, tools):
        try:
            resp = httpx.post(
                self._url(),
                headers=self._headers(),
                json=self._body(messages, tools, stream=False),
                timeout=self.timeout,
            )
        except httpx.HTTPError as e:
            raise LLMError(f"could not reach model server: {e}") from e
        if resp.status_code >= 400:
            raise LLMError(f"server returned {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        choice = (data.get("choices") or [{}])[0]
        msg = choice.get("message") or {}
        return msg.get("content") or "", msg.get("tool_calls") or []

    def validate(self) -> tuple[bool, str]:
        """1-token ping so onboarding fails fast with a friendly message."""
        try:
            resp = httpx.post(
                self._url(),
                headers=self._headers(),
                json=self._body(
                    [{"role": "user", "content": "ping"}], None, stream=False, max_tokens=1
                ),
                timeout=30.0,
            )
        except httpx.HTTPError as e:
            return False, f"could not reach {self._url()} ({e})"
        if resp.status_code == 200:
            return True, ""
        return False, f"server returned {resp.status_code}: {resp.text[:200]}"
