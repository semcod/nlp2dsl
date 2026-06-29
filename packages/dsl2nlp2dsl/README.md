# dsl2nlp2dsl

Warstwa kontroli NLP2DSL — grammar DSL, JSON Schema, CQRS bus i EventStore.

Jedyny punkt wykonania mutacji: `dsl2nlp2dsl.dispatch()`.

## Komendy

| Typ | Verbs |
|-----|-------|
| Query | `ORIENT`, `PARSE`, `PLAN`, `VALIDATE`, `HEALTH`, `ACTIONS`, `RESOLVE` |
| Command | `EXECUTE`, `SIMULATE`, `GENERATE`, `CHAT`, `DRAFT`, `OBSERVE`, `COMPOSE` |

## CLI

```bash
dsl2nlp2dsl exec 'PARSE "wyślij fakturę"'
dsl2nlp2dsl exec 'PLAN "wyślij fakturę" MODE auto'
dsl2nlp2dsl exec 'VALIDATE workflow.json'
dsl2nlp2dsl run script.dsl
dsl2nlp2dsl validate-schema
dsl2nlp2dsl encode 'PARSE "hello"' --format protobuf --output command.pb
dsl2nlp2dsl decode --format protobuf --input command.pb
dsl2nlp2dsl replay --file app.nlp2dsl.less
```

## Reprezentacje

| Format | Pliki |
|--------|-------|
| Tekst DSL | REPL, CLI |
| JSON Schema | `schema/commands/*.schema.json` |
| Protobuf | `proto/dsl2nlp2dsl/v1/*.proto` → `src/dsl2nlp2dsl/v1/*_pb2.py` |

Regeneracja protobuf: `bash scripts/generate-proto.sh`

Powrót: [packages/README.md](../README.md) · [README główne](../../README.md)
