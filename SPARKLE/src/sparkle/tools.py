"""The one tool SPARKLE ships: an agent rewriting its own definition."""

from __future__ import annotations

from pathlib import Path

from . import agent as agent_mod

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "update_self",
        "description": (
            "Rewrite your own definition so you become who the user wants. "
            "Provide only the parts you want to change."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "system": {"type": "string", "description": "New system.md body (optional)."},
                "soul": {"type": "string", "description": "New soul.md persona body (optional)."},
                "tools": {"type": "string", "description": "New tools.md body (optional)."},
            },
        },
    },
}

# What we hand the API in the `tools` field.
SCHEMAS = [TOOL_SCHEMA]


def execute(agent_dir, args: dict) -> str:
    """Apply update_self. Writes only provided, non-empty fields. Never raises."""
    if not isinstance(args, dict):
        return "update_self received no usable fields, so nothing changed."

    written: list[str] = []
    skipped_empty = False
    for field in ("system", "soul", "tools"):
        value = args.get(field)
        if value is None:
            continue
        if not isinstance(value, str) or not value.strip():
            skipped_empty = True
            continue
        try:
            agent_mod.write_field(agent_dir, field, value)
            written.append(f"{field}.md")
        except Exception as e:  # pragma: no cover - defensive
            return f"Tried to update myself but hit an error: {e}"

    if not written:
        if skipped_empty:
            return "I left myself unchanged — the new text was empty."
        return "No recognised fields to update, so nothing changed."

    files = ", ".join(written)
    return (
        f"Updated {files} in {Path(agent_dir).name}. "
        "Tell the user to run /reset so the new you loads."
    )
