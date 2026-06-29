"""cli2nlp2dsl — REPL / exec / run."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dsl2nlp2dsl import execute_dsl, execute_dsl_line


def run_shell(*, default_file: str | None = None, json_out: bool = False) -> int:
    print("cli2nlp2dsl shell — NLP2DSL control DSL (exit/quit to leave)")
    exit_code = 0
    while True:
        try:
            line = input("nlp2dsl> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line.lower() in {"exit", "quit", ":q"}:
            break
        result = execute_dsl_line(line, default_file=default_file)
        if json_out:
            print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        else:
            if result.error:
                print(f"error: {result.error}", file=sys.stderr)
            if result.output:
                print(result.output.rstrip())
        if not result.ok:
            exit_code = 1
    return exit_code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cli2nlp2dsl", description="NLP2DSL control DSL shell")
    sub = parser.add_subparsers(dest="cmd")

    shell = sub.add_parser("shell", help="Interactive REPL")
    shell.add_argument("--file", help="Default app.nlp2dsl.less path")
    shell.add_argument("--json", action="store_true")

    run = sub.add_parser("run", help="Run a .dsl script file")
    run.add_argument("script")
    run.add_argument("--file")
    run.add_argument("--json", action="store_true")

    one = sub.add_parser("exec", help="Execute one DSL command")
    one.add_argument("command")
    one.add_argument("--file")
    one.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    cmd = args.cmd or "shell"

    if cmd == "shell":
        return run_shell(default_file=args.file, json_out=args.json)
    if cmd == "run":
        text = Path(args.script).read_text(encoding="utf-8")
        results = execute_dsl(text, default_file=args.file)
        code = 0
        for result in results:
            if args.json:
                print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
            else:
                if result.error:
                    print(f"error: {result.error}", file=sys.stderr)
                if result.output:
                    print(result.output.rstrip())
            if not result.ok:
                code = 1
        return code
    if cmd == "exec":
        result = execute_dsl_line(args.command, default_file=args.file)
        if args.json:
            print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        else:
            if result.error:
                print(f"error: {result.error}", file=sys.stderr)
            if result.output:
                print(result.output.rstrip())
        return 0 if result.ok else 1
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
