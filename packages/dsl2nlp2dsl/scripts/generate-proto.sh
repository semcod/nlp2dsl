#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/src"
mkdir -p "$OUT/dsl2nlp2dsl/v1"
python3 -m grpc_tools.protoc -I "$ROOT/proto" --python_out="$OUT" \
  "$ROOT/proto/dsl2nlp2dsl/v1/command.proto" \
  "$ROOT/proto/dsl2nlp2dsl/v1/result.proto"
echo "Generated protobuf → $OUT/dsl2nlp2dsl/v1"
