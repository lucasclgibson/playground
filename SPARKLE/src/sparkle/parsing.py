"""Small-model robustness layer: pull a tool call out of imperfect output.

Tries hardest-to-softest:
  1. native OpenAI `tool_calls` field
  2. a fenced ```json / ```tool / <tool_call> block in the content
  3. the first balanced {...} object that looks like update_self

Plus tolerant JSON repair (trailing commas, single quotes, surrounding prose).
Never raises — on total failure it returns None and the agent simply talked.
"""

from __future__ import annotations

import json
import re

KNOWN_TOOLS = {"update_self"}


def _try_json(text: str):
    try:
        return json.loads(text)
    except Exception:
        return None


def _repair(text: str):
    """Best-effort repair of almost-JSON emitted by small models."""
    candidate = text.strip()
    # strip trailing commas before } or ]
    candidate = re.sub(r",\s*([}\]])", r"\1", candidate)
    obj = _try_json(candidate)
    if obj is not None:
        return obj
    # naive single -> double quote swap (only if no double quotes present)
    if '"' not in candidate and "'" in candidate:
        swapped = candidate.replace("'", '"')
        obj = _try_json(swapped)
        if obj is not None:
            return obj
    return None


def _balanced_spans(text: str):
    """Yield every balanced {...} substring, outermost first."""
    starts: list[int] = []
    for i, ch in enumerate(text):
        if ch == "{":
            starts.append(i)
        elif ch == "}" and starts:
            start = starts.pop()
            if not starts:  # outermost closed
                yield text[start : i + 1]


def _normalise(obj) -> tuple[str, dict] | None:
    """Turn a parsed object into (tool_name, args_dict)."""
    if not isinstance(obj, dict):
        return None

    # wrapped form: {"name": "update_self", "arguments": {...}}
    name = obj.get("name") or obj.get("tool") or obj.get("tool_name")
    args = obj.get("arguments")
    if args is None:
        args = obj.get("args")
    if isinstance(args, str):
        args = _repair(args) or {}

    if name in KNOWN_TOOLS and isinstance(args, dict):
        return name, args

    # bare args form: {"soul": "..."} with no wrapper
    bare = {k: v for k, v in obj.items() if k in ("system", "soul", "tools")}
    if bare and name is None and args is None:
        return "update_self", bare

    return None


def extract_tool_call(tool_calls, content: str | None):
    """Return (tool_name, args) or None. Never raises."""
    try:
        # 1) native tool_calls
        for call in tool_calls or []:
            fn = (call or {}).get("function", {}) if isinstance(call, dict) else {}
            name = fn.get("name")
            raw_args = fn.get("arguments")
            args = raw_args if isinstance(raw_args, dict) else (
                _try_json(raw_args) or _repair(raw_args or "") or {}
            )
            if name in KNOWN_TOOLS:
                return name, (args if isinstance(args, dict) else {})

        text = content or ""

        # 2) fenced / tagged blocks
        block_patterns = [
            r"```(?:json|tool)?\s*(\{.*?\})\s*```",
            r"<tool_call>\s*(\{.*?\})\s*</tool_call>",
        ]
        for pat in block_patterns:
            for m in re.finditer(pat, text, re.DOTALL):
                obj = _try_json(m.group(1)) or _repair(m.group(1))
                hit = _normalise(obj) if obj is not None else None
                if hit:
                    return hit

        # 3) any balanced brace span that mentions a known tool / our fields
        for span in _balanced_spans(text):
            if not any(t in span for t in KNOWN_TOOLS) and not re.search(
                r'"(system|soul|tools)"', span
            ):
                continue
            obj = _try_json(span) or _repair(span)
            hit = _normalise(obj) if obj is not None else None
            if hit:
                return hit
    except Exception:
        return None

    return None
