"""An agent is a directory of three thin markdown files.

    <agent_dir>/
      system.md   core behaviour / system prompt
      soul.md     persona / voice / vibe
      tools.md    human-readable tool notes

Nothing else lives in the agent dir — it stays pure markdown the user owns.
Machine state (name, ordering, last-used) lives in the global config.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from . import prompts

# field name -> file name
FILES = {
    "system": "system.md",
    "soul": "soul.md",
    "tools": "tools.md",
}


@dataclass
class Agent:
    dir: Path
    name: str
    system: str = ""
    soul: str = ""
    tools: str = ""

    def build_system_prompt(self) -> str:
        """Concatenate the three files into one compact system message."""
        parts = [p.strip() for p in (self.system, self.soul, self.tools) if p.strip()]
        return "\n\n".join(parts)


def _atomic_write(path: Path, content: str) -> None:
    """Write content atomically, keeping a single .bak of any prior version."""
    if not content or not content.strip():
        raise ValueError("refusing to write empty content")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        bak = path.with_suffix(path.suffix + ".bak")
        bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


def load(agent_dir, name: str | None = None) -> Agent:
    d = Path(agent_dir)
    name = name or d.name

    def _read(field: str) -> str:
        f = d / FILES[field]
        return f.read_text(encoding="utf-8") if f.exists() else ""

    return Agent(
        dir=d,
        name=name,
        system=_read("system"),
        soul=_read("soul"),
        tools=_read("tools"),
    )


def create_default(agent_dir, name: str) -> Agent:
    """Scaffold a fresh agent directory with fun default markdown."""
    d = Path(agent_dir)
    d.mkdir(parents=True, exist_ok=True)
    _atomic_write(d / FILES["system"], prompts.default_system_md(name))
    _atomic_write(d / FILES["soul"], prompts.default_soul_md(name))
    _atomic_write(d / FILES["tools"], prompts.default_tools_md())
    return load(d, name)


def write_field(agent_dir, field: str, content: str) -> None:
    if field not in FILES:
        raise KeyError(f"unknown agent field: {field}")
    _atomic_write(Path(agent_dir) / FILES[field], content)
