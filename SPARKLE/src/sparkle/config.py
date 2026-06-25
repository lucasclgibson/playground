"""Global SPARKLE config: one small TOML file.

Holds the provider connection plus a registry of known agents. Read with stdlib
`tomllib`; written by hand-emitting a tiny TOML document (no write-only dep).

Shape:

    [provider]
    kind     = "ollama"
    base_url = "http://localhost:11434/v1"
    api_key  = ""
    model    = "llama3.2"

    [[agents]]
    name = "gizmo"
    path = "/home/user/agents/gizmo"

    [state]
    last = "gizmo"
"""

from __future__ import annotations

import os
import tomllib
from pathlib import Path


def config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME")
    if base:
        root = Path(base)
    elif os.name == "nt":
        root = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        root = Path.home() / ".config"
    return root / "sparkle"


def config_path() -> Path:
    return config_dir() / "config.toml"


def read() -> dict:
    path = config_path()
    if not path.exists():
        return {}
    with path.open("rb") as f:
        return tomllib.load(f)


def _esc(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def write(cfg: dict) -> None:
    """Hand-emit the flat config document."""
    lines: list[str] = []

    provider = cfg.get("provider")
    if provider:
        lines.append("[provider]")
        for key in ("kind", "base_url", "api_key", "model"):
            lines.append(f'{key} = "{_esc(str(provider.get(key, "")))}"')
        lines.append("")

    for agent in cfg.get("agents", []):
        lines.append("[[agents]]")
        lines.append(f'name = "{_esc(str(agent.get("name", "")))}"')
        lines.append(f'path = "{_esc(str(agent.get("path", "")))}"')
        lines.append("")

    state = cfg.get("state")
    if state and state.get("last"):
        lines.append("[state]")
        lines.append(f'last = "{_esc(str(state["last"]))}"')
        lines.append("")

    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".toml.tmp")
    tmp.write_text("\n".join(lines), encoding="utf-8")
    os.replace(tmp, path)


# --- high-level helpers -----------------------------------------------------

def save_provider(kind: str, base_url: str, api_key: str, model: str) -> None:
    cfg = read()
    cfg["provider"] = {
        "kind": kind,
        "base_url": base_url,
        "api_key": api_key,
        "model": model,
    }
    write(cfg)


def get_provider() -> dict | None:
    return read().get("provider")


def register_agent(name: str, path: str) -> None:
    cfg = read()
    agents = cfg.get("agents", [])
    path = str(Path(path).resolve())
    # de-dupe by name; latest registration wins
    agents = [a for a in agents if a.get("name") != name]
    agents.append({"name": name, "path": path})
    cfg["agents"] = agents
    cfg.setdefault("state", {})["last"] = name
    write(cfg)


def list_agents() -> list[dict]:
    return read().get("agents", [])


def set_last(name: str) -> None:
    cfg = read()
    cfg.setdefault("state", {})["last"] = name
    write(cfg)


def resolve_agent(name: str | None) -> dict | None:
    """Return {'name', 'path'} for the requested agent, or the last-used one."""
    agents = list_agents()
    if not agents:
        return None
    if name:
        for a in agents:
            if a.get("name") == name:
                return a
        return None
    last = read().get("state", {}).get("last")
    if last:
        for a in agents:
            if a.get("name") == last:
                return a
    return agents[-1]
