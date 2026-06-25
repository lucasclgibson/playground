"""The chat TUI — a clean terminal REPL inspired by claude-code / opencode.

The turn logic (greeting, streaming, tool handling) is factored out of the
prompt_toolkit loop so it can be driven headlessly in tests.
"""

from __future__ import annotations

import sys

from . import agent as agent_mod
from . import config, llm, parsing, prompts, tools, ui

# How many recent messages to keep (excluding the system prompt) so a small
# context window doesn't overflow. Pairs of user/assistant turns.
HISTORY_LIMIT = 24


def _trim(messages: list[dict]) -> None:
    """Keep the system message + the most recent HISTORY_LIMIT messages."""
    if len(messages) <= HISTORY_LIMIT + 1:
        return
    head = messages[:1]
    tail = messages[-HISTORY_LIMIT:]
    messages[:] = head + tail


def new_session(agent: agent_mod.Agent) -> list[dict]:
    return [{"role": "system", "content": agent.build_system_prompt()}]


def generate_greeting(client: llm.Client, messages: list[dict], emit) -> str:
    """Make a fresh agent speak first, in character. Falls back if the model is silent."""
    messages.append({"role": "user", "content": prompts.GREETING_KICKOFF})
    text = ""
    try:
        for delta in client.chat_stream(messages, tools=None):
            text += delta
            emit(delta)
    except llm.LLMError as e:
        emit(f"[could not reach the model: {e}]")
    text = text.strip()
    if not text:
        text = prompts.FALLBACK_FIRST_MESSAGE
        emit(text)
    messages.append({"role": "assistant", "content": text})
    return text


def handle_turn(client: llm.Client, agent: agent_mod.Agent, messages: list[dict],
                user_text: str, emit) -> str | None:
    """Run one user->assistant turn. Returns a tool-result note if a tool fired."""
    messages.append({"role": "user", "content": user_text})
    reply = ""
    try:
        for delta in client.chat_stream(messages, tools=tools.SCHEMAS):
            reply += delta
            emit(delta)
    except llm.LLMError as e:
        emit(f"[could not reach the model: {e}]")
        messages.pop()  # roll back the user turn we couldn't answer
        return None

    messages.append({"role": "assistant", "content": client.last_content or reply})

    call = parsing.extract_tool_call(client.last_tool_calls, client.last_content or reply)
    note = None
    if call:
        name, args = call
        if name == "update_self":
            note = tools.execute(agent.dir, args)
            messages.append({"role": "user", "content": f"(tool result: {note})"})
    _trim(messages)
    return note


# --- interactive REPL -------------------------------------------------------

def run(name: str | None = None) -> int:
    provider = config.get_provider()
    if not provider:
        ui.error("No provider configured yet. Run `sparkle onboard` first.")
        return 1

    record = config.resolve_agent(name)
    if not record:
        if name:
            ui.error(f"No agent named '{name}'. Run `sparkle onboard` to make one.")
        else:
            ui.error("No agents yet. Run `sparkle onboard` to make your first.")
        return 1

    agent = agent_mod.load(record["path"], record["name"])
    config.set_last(agent.name)
    client = llm.Client(provider["base_url"], provider.get("api_key", ""), provider["model"])

    return repl(client, agent)


def repl(client: llm.Client, agent: agent_mod.Agent) -> int:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import WordCompleter

    session = PromptSession()
    completer = WordCompleter(["/reset", "/new", "/exit", "/help"], sentence=True)

    messages = new_session(agent)

    ui.banner(agent.name, client.model)
    ui.agent_say_start(agent.name)
    generate_greeting(client, messages, ui.stream)
    ui.agent_say_end()

    while True:
        try:
            user_text = session.prompt(ui.user_prompt(), completer=completer).strip()
        except (EOFError, KeyboardInterrupt):
            ui.info("\nbye ✨")
            return 0

        if not user_text:
            continue

        if user_text in ("/exit", "/quit"):
            ui.info("bye ✨")
            return 0
        if user_text in ("/reset", "/new"):
            agent = agent_mod.load(agent.dir, agent.name)  # reload markdown
            messages = new_session(agent)
            ui.info("— session reset, fresh prompt loaded —")
            ui.agent_say_start(agent.name)
            generate_greeting(client, messages, ui.stream)
            ui.agent_say_end()
            continue
        if user_text == "/help":
            ui.help_text()
            continue

        ui.agent_say_start(agent.name)
        try:
            note = handle_turn(client, agent, messages, user_text, ui.stream)
        except KeyboardInterrupt:
            ui.info("\n[interrupted]")
            continue
        ui.agent_say_end()
        if note:
            ui.tool_note(note)

    # unreachable
    return 0
