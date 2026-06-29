"""mcp2nlp2dsl CLI."""

from __future__ import annotations

import argparse

from mcp2nlp2dsl.server import run_server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mcp2nlp2dsl")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("serve", help="Start stdio MCP server")
    args = parser.parse_args(argv)
    if args.cmd == "serve":
        run_server()
        return 0
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
