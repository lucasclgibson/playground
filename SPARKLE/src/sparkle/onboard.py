"""`sparkle onboard` — the TUI first-run flow.

provider -> credentials -> validate -> name -> directory picker -> scaffold ->
save config -> drop straight into chat with the new agent.
"""

from __future__ import annotations

import os
from pathlib import Path

from . import agent as agent_mod
from . import chat, config, llm, ui

PROVIDERS = [
    ("ollama", "Ollama (local)", "http://localhost:11434/v1"),
    ("vllm", "vLLM (local/served)", "http://localhost:8000/v1"),
    ("openai", "OpenAI-compatible API", "https://api.openai.com/v1"),
]


def _pick_provider() -> tuple[str, str]:
    from prompt_toolkit.shortcuts import radiolist_dialog

    result = radiolist_dialog(
        title="✦ SPARKLE — choose your model provider",
        text="Which OpenAI-compatible server is your model behind?",
        values=[(kind, label) for kind, label, _ in PROVIDERS],
    ).run()
    if result is None:
        raise KeyboardInterrupt
    default_url = next(url for kind, _, url in PROVIDERS if kind == result)
    return result, default_url


def _ask(message: str, default: str = "", is_password: bool = False) -> str:
    from prompt_toolkit import prompt as pt_prompt

    return pt_prompt(message, default=default, is_password=is_password).strip()


def _pick_directory(default_parent: str) -> Path:
    from prompt_toolkit import prompt as pt_prompt
    from prompt_toolkit.completion import PathCompleter

    completer = PathCompleter(only_directories=True, expanduser=True)
    ui.info("  Pick a folder to keep your agent in (Tab to search/complete).")
    while True:
        raw = pt_prompt(
            "  parent folder › ",
            default=default_parent,
            completer=completer,
        ).strip()
        path = Path(os.path.expanduser(raw or default_parent)).resolve()
        if path.exists() and not path.is_dir():
            ui.error(f"{path} is not a folder. Try again.")
            continue
        return path


def run() -> int:
    ui.info("\n  Welcome to SPARKLE ✦  Let's set up your first agent.\n")

    # 1) provider + creds
    try:
        kind, default_url = _pick_provider()
    except KeyboardInterrupt:
        ui.info("onboarding cancelled.")
        return 1

    while True:
        base_url = _ask("  base URL › ", default=default_url)
        api_key = _ask(
            "  API key (leave blank for local) › ",
            is_password=True,
        )
        model = _ask("  model name › ", default="")
        if not model:
            ui.error("a model name is required.")
            continue

        ui.info("  …checking the connection…")
        ok, err = llm.Client(base_url, api_key, model).validate()
        if ok:
            ui.info("  ✓ connected.\n")
            break
        ui.error(f"couldn't reach the model: {err}")
        from prompt_toolkit.shortcuts import confirm

        if not confirm("  Try the connection details again?"):
            ui.info("  Saving anyway — you can fix it later.\n")
            break

    config.save_provider(kind, base_url, api_key, model)

    # 2) name the agent
    name = ""
    while not name:
        name = _ask("  name your agent › ", default="sparky")
        name = "".join(c for c in name if c.isalnum() or c in "-_").strip("-_")
        if not name:
            ui.error("pick a name with letters or numbers.")

    # 3) where it lives
    parent = _pick_directory(str(Path.cwd()))
    agent_dir = parent / name
    if agent_dir.exists() and any(agent_dir.iterdir()):
        from prompt_toolkit.shortcuts import confirm

        if not confirm(f"  {agent_dir} already exists and isn't empty. Use it anyway?"):
            ui.info("  onboarding cancelled.")
            return 1

    # 4) scaffold the markdown
    agent_mod.create_default(agent_dir, name)
    config.register_agent(name, str(agent_dir))

    ui.info(f"\n  ✓ created agent '{name}' at {agent_dir}")
    ui.info("    system.md · soul.md · tools.md\n")
    ui.info("  Dropping you into the chat — say hi to your new agent ✦\n")

    # 5) straight into chat
    return chat.run(name)
