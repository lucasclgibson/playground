"""`sparkle` entry point — a tiny argparse dispatch over two commands."""

from __future__ import annotations

import argparse
import sys

from . import __version__


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sparkle",
        description="A tiny terminal home for small local agents.",
    )
    parser.add_argument("--version", action="version", version=f"sparkle {__version__}")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("onboard", help="set up your provider and first agent")

    chat_p = sub.add_parser("chat", help="chat with an agent (defaults to the last used)")
    chat_p.add_argument("agent", nargs="?", default=None, help="agent name")

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if not sys.stdin.isatty() or not sys.stdout.isatty():
        print("sparkle needs an interactive terminal (TTY).", file=sys.stderr)
        return 1

    if args.command == "onboard":
        from . import onboard

        return onboard.run()

    if args.command == "chat":
        from . import chat

        return chat.run(args.agent)

    parser.print_help()
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
