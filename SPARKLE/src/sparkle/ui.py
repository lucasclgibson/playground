"""All terminal presentation in one place: colours, banner, prompts, streaming.

Plain ANSI keeps this dependency-light; prompt_toolkit owns the interactive
input widgets elsewhere. Everything degrades gracefully when output isn't a TTY.
"""

from __future__ import annotations

import sys

from . import __version__

_TTY = sys.stdout.isatty()


def _c(code: str) -> str:
    return code if _TTY else ""


DIM = _c("\033[2m")
BOLD = _c("\033[1m")
RESET = _c("\033[0m")
PINK = _c("\033[38;5;213m")
CYAN = _c("\033[38;5;80m")
GREY = _c("\033[38;5;245m")
YELLOW = _c("\033[38;5;221m")
RED = _c("\033[38;5;203m")


def banner(agent_name: str, model: str) -> None:
    print()
    print(f"{PINK}{BOLD}  ✦ SPARKLE{RESET}{GREY} v{__version__}{RESET}")
    print(f"{GREY}  agent {RESET}{CYAN}{agent_name}{RESET}{GREY}  ·  model {RESET}{CYAN}{model}{RESET}")
    print(f"{GREY}  /reset to reload  ·  /exit to leave{RESET}")
    print(f"{DIM}  {'─' * 48}{RESET}")
    print()


def user_prompt():
    """Return prompt_toolkit-styled prompt fragments for the input line."""
    from prompt_toolkit.formatted_text import FormattedText

    return FormattedText([("#5fd7af bold", "› ")])


def agent_say_start(agent_name: str) -> None:
    sys.stdout.write(f"\n{PINK}{BOLD}{agent_name}{RESET}{DIM} ·{RESET} ")
    sys.stdout.flush()


def stream(text: str) -> None:
    sys.stdout.write(text)
    sys.stdout.flush()


def agent_say_end() -> None:
    sys.stdout.write("\n")
    sys.stdout.flush()


def tool_note(note: str) -> None:
    print(f"{YELLOW}  ⚙ {note}{RESET}")


def info(text: str) -> None:
    print(f"{GREY}{text}{RESET}")


def error(text: str) -> None:
    print(f"{RED}✗ {text}{RESET}", file=sys.stderr)


def help_text() -> None:
    print(f"{GREY}  /reset, /new  start fresh and reload the agent's markdown")
    print(f"  /exit, /quit  leave the chat")
    print(f"  /help         this message{RESET}")
