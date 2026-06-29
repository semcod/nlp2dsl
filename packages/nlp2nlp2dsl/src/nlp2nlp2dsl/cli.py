"""nlp2nlp2dsl CLI."""

from __future__ import annotations

import argparse
import json
import sys

from nlp2nlp2dsl.apply import apply_nl
from nlp2nlp2dsl.to_dsl import to_dsl


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="nlp2nlp2dsl")
    sub = parser.add_subparsers(dest="cmd")

    td = sub.add_parser("to-dsl", help="NL → DSL line (no execution)")
    td.add_argument("prompt")
    td.add_argument("--mode", default="auto")

    ap = sub.add_parser("apply", help="NL → DSL → dispatch")
    ap.add_argument("prompt")
    ap.add_argument("--mode", default="auto")
    ap.add_argument("--file")
    ap.add_argument("--json", action="store_true")

    gen = sub.add_parser("generate", help="GENERATE command")
    gen.add_argument("prompt")
    gen.add_argument("--out")
    gen.add_argument("--mode", default="auto")
    gen.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    if args.cmd == "to-dsl":
        print(to_dsl(args.prompt, mode=args.mode))
        return 0
    if args.cmd in {"apply", "generate"}:
        result = apply_nl(args.prompt, mode=args.mode, default_file=getattr(args, "file", None), out=getattr(args, "out", None))
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
