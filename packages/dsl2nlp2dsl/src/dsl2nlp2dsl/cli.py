"""dsl2nlp2dsl CLI — exec / run / validate-schema / replay."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dsl2nlp2dsl.bus import execute_dsl, execute_dsl_line
from dsl2nlp2dsl.codec import roundtrip_text
from dsl2nlp2dsl.events import default_event_store
from dsl2nlp2dsl.schema_registry import validate_schema_registry


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dsl2nlp2dsl", description="NLP2DSL control DSL bus")
    sub = parser.add_subparsers(dest="cmd")

    exec_p = sub.add_parser("exec", help="Execute one DSL command")
    exec_p.add_argument("command")
    exec_p.add_argument("--file", help="Default manifest file")
    exec_p.add_argument("--json", action="store_true")

    run_p = sub.add_parser("run", help="Run a .dsl script")
    run_p.add_argument("script")
    run_p.add_argument("--file")
    run_p.add_argument("--json", action="store_true")

    sub.add_parser("validate-schema", help="Validate JSON Schema registry")

    enc = sub.add_parser("encode", help="Text DSL → JSON dict or protobuf")
    enc.add_argument("command")
    enc.add_argument("--format", choices=["json", "text", "protobuf"], default="json")
    enc.add_argument("--output", help="Write protobuf bytes to file")

    dec = sub.add_parser("decode", help="Round-trip text DSL or decode protobuf")
    dec.add_argument("command", nargs="?", help="Text DSL line")
    dec.add_argument("--input", help="Protobuf input file")
    dec.add_argument("--format", choices=["text", "protobuf"], default="text")

    rep = sub.add_parser("replay", help="Replay EventStore")
    rep.add_argument("--file", default="app.nlp2dsl.less")

    args = parser.parse_args(argv)
    cmd = args.cmd or "exec"

    if cmd == "validate-schema":
        errors = validate_schema_registry()
        if errors:
            for err in errors:
                print(err, file=sys.stderr)
            return 1
        print("schema OK")
        return 0

    if cmd == "encode":
        if args.format == "protobuf":
            from dsl2nlp2dsl.codec import encode_protobuf

            blob = encode_protobuf(args.command)
            if args.output:
                Path(args.output).write_bytes(blob)
            else:
                sys.stdout.buffer.write(blob)
            return 0
        from dsl2nlp2dsl.codec import encode_text

        data, errors = encode_text(args.command)
        if errors:
            print("; ".join(errors), file=sys.stderr)
            return 1
        if args.format == "json":
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            from dsl2nlp2dsl.grammar import to_text

            print(to_text(data))
        return 0

    if cmd == "decode":
        try:
            if args.format == "protobuf":
                from dsl2nlp2dsl.codec import decode_protobuf

                if not args.input:
                    print("--input required for protobuf decode", file=sys.stderr)
                    return 1
                print(decode_protobuf(Path(args.input).read_bytes()))
            else:
                if not args.command:
                    print("command required", file=sys.stderr)
                    return 1
                print(roundtrip_text(args.command))
        except (ValueError, OSError) as exc:
            print(str(exc), file=sys.stderr)
            return 1
        return 0

    if cmd == "replay":
        store = default_event_store(args.file)
        for event in store.replay():
            print(json.dumps(event.to_dict(), ensure_ascii=False))
        return 0

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

    result = execute_dsl_line(args.command, default_file=args.file)
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        if result.error:
            print(f"error: {result.error}", file=sys.stderr)
        if result.output:
            print(result.output.rstrip())
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
