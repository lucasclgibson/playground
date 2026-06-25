"""End-to-end against a fake OpenAI-compatible server (stdlib only).

Exercises SSE streaming, streamed tool-call accumulation, the non-streaming
fallback, and a full self-editing chat turn — no real model required.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from sparkle import agent as agent_mod
from sparkle import chat, llm


def _last_user(body):
    for m in reversed(body.get("messages", [])):
        if m.get("role") == "user":
            return m.get("content", "")
    return ""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # silence
        pass

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or "{}")
        last = _last_user(body)
        stream = body.get("stream", False)

        # Non-streaming path (validate ping, fallback, or NOSTREAM marker)
        if not stream or "NOSTREAM" in last:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            msg = {"role": "assistant", "content": "pong (non-stream)"}
            payload = {"choices": [{"message": msg}]}
            self.wfile.write(json.dumps(payload).encode())
            return

        # Streaming path
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()

        def send(chunk):
            self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode())

        if "BECOME" in last:
            # stream a native tool call in two argument fragments
            send({"choices": [{"delta": {"tool_calls": [
                {"index": 0, "id": "c1", "function": {"name": "update_self", "arguments": '{"soul": "a '}}
            ]}}]})
            send({"choices": [{"delta": {"tool_calls": [
                {"index": 0, "function": {"arguments": 'serene monk"}'}}
            ]}}]})
            send({"choices": [{"delta": {"content": "Done — tell me to /reset."}}]})
        else:
            for word in ["Hello", " there", " friend"]:
                send({"choices": [{"delta": {"content": word}}]})
        self.wfile.write(b"data: [DONE]\n\n")


@pytest.fixture
def server():
    srv = HTTPServer(("127.0.0.1", 0), Handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    host, port = srv.server_address
    yield f"http://{host}:{port}/v1"
    srv.shutdown()


def test_validate_ping(server):
    ok, err = llm.Client(server, "", "m").validate()
    assert ok, err


def test_stream_plain_text(server):
    client = llm.Client(server, "", "m")
    out = "".join(client.chat_stream([{"role": "user", "content": "hi"}]))
    assert out == "Hello there friend"
    assert client.last_content == "Hello there friend"
    assert client.last_tool_calls == []


def test_non_stream_fallback(server):
    client = llm.Client(server, "", "m")
    out = "".join(client.chat_stream([{"role": "user", "content": "NOSTREAM please"}]))
    assert "non-stream" in out
    assert client.last_content == "pong (non-stream)"


def test_streamed_tool_call_accumulates(server):
    client = llm.Client(server, "", "m")
    list(client.chat_stream([{"role": "user", "content": "BECOME a monk"}], tools=[{"x": 1}]))
    assert len(client.last_tool_calls) == 1
    fn = client.last_tool_calls[0]["function"]
    assert fn["name"] == "update_self"
    assert json.loads(fn["arguments"]) == {"soul": "a serene monk"}


def test_full_self_edit_turn(server, tmp_path):
    d = tmp_path / "gizmo"
    a = agent_mod.create_default(d, "gizmo")
    client = llm.Client(server, "", "m")
    messages = chat.new_session(a)

    note = chat.handle_turn(client, a, messages, "Please BECOME a serene monk", lambda s: None)

    assert note is not None and "soul.md" in note
    assert "serene monk" in (d / "soul.md").read_text()
    # the turn was recorded and a tool-result note appended for the model
    assert any("tool result" in m.get("content", "") for m in messages)


def test_greeting_generation(server, tmp_path):
    d = tmp_path / "gizmo"
    a = agent_mod.create_default(d, "gizmo")
    client = llm.Client(server, "", "m")
    messages = chat.new_session(a)
    chunks = []
    text = chat.generate_greeting(client, messages, chunks.append)
    assert text == "Hello there friend"
    assert "".join(chunks) == "Hello there friend"
    assert messages[-1]["role"] == "assistant"
