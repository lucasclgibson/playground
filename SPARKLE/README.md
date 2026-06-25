# ✦ SPARKLE

A super-simple, lightweight terminal home for small local agents — the lean
alternative to bloated agent frameworks.

SPARKLE does three things and nothing else:

1. Talks to **any OpenAI-compatible API** — Ollama, vLLM, or OpenAI itself.
2. Treats an **agent as a directory** of three thin markdown files you own.
3. Lets the agent **rewrite its own soul** when you describe who you want it to be.

It's built for **small local models**: tight prompts, one tool, and a parser
that forgives messy output.

## What is an agent?

Just a folder:

```
my-agent/
├── system.md   # core behaviour / system prompt
├── soul.md     # personality, voice, vibe  ← the bit that changes most
└── tools.md    # human-readable notes on its one tool
```

No database, no config buried in the agent. Edit the markdown by hand any time,
or let the agent edit itself.

## Install

Requires Python 3.11+.

```bash
pipx install ./SPARKLE        # isolated, recommended
# or
pip install ./SPARKLE
```

This adds a single `sparkle` command.

## Use

```bash
sparkle onboard            # first-run wizard: provider → agent → chat
sparkle chat               # chat with your most recent agent
sparkle chat my-agent      # chat with a named agent
```

### Onboarding

`sparkle onboard` walks you through:

1. Pick a provider — Ollama, vLLM, or OpenAI-compatible.
2. Enter the base URL, API key (blank for local), and model name. SPARKLE pings
   it so you find out it works *now*, not mid-conversation.
3. Name your agent.
4. Pick the folder it lives in (Tab to search/complete paths).
5. SPARKLE scaffolds the markdown and drops you into the chat.

Your brand-new agent greets you and asks who you want it to be. Describe it in
detail; it calls its one tool, `update_self`, to rewrite its own markdown — then
asks you to `/reset` so the new self loads.

### In chat

| command | what it does |
| --- | --- |
| `/reset`, `/new` | start fresh and reload the agent's markdown |
| `/exit`, `/quit` | leave |
| `/help` | show commands |

## Provider quick reference

| provider | base URL |
| --- | --- |
| Ollama | `http://localhost:11434/v1` |
| vLLM | `http://localhost:8000/v1` |
| OpenAI | `https://api.openai.com/v1` |

Config lives in `~/.config/sparkle/config.toml`.

## Why so small?

Two runtime dependencies — `prompt_toolkit` (the TUI) and `httpx` (the HTTP).
Everything else is the Python standard library. That's the whole point.
