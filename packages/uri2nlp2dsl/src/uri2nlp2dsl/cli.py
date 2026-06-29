"""uri2nlp2dsl CLI."""

from __future__ import annotations

import argparse
import json
import sys

from uri2nlp2dsl.decode import decode_uri, run_uri
from uri2nlp2dsl.resolve import resolve_nl


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="uri2nlp2dsl")
    sub = parser.add_subparsers(dest="cmd")

    dec = sub.add_parser("decode", help="URI → DSL line")
    dec.add_argument("--uri", required=True)

    run = sub.add_parser("run", help="URI → dispatch")
    run.add_argument("--uri", required=True)
    run.add_argument("--file")
    run.add_argument("--json", action="store_true")

    res = sub.add_parser("resolve", help="NL → command URI")
    res.add_argument("prompt")
    res.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    if args.cmd == "decode":
        print(decode_uri(args.uri))
        return 0
    if args.cmd == "run":
        result = run_uri(args.uri, default_file=args.file)
        if args.json:
            print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        else:
            if result.error:
                print(f"error: {result.error}", file=sys.stderr)
            if result.output:
                print(result.output.rstrip())
        return 0 if result.ok else 1
    if args.cmd == "resolve":
        hits = resolve_nl(args.prompt)
        if args.json:
            print(json.dumps([h.to_dict() for h in hits], ensure_ascii=False, indent=2))
        else:
            for hit in hits:
                print(hit.uri)
        return 0
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
