# uri2nlp2dsl

Dekoduje `nlp2dsl://cmd/VERB?...` → linia DSL → `dsl2nlp2dsl.dispatch()`.

```bash
uri2nlp2dsl decode --uri 'nlp2dsl://cmd/PARSE?text=wyślij+fakturę'
uri2nlp2dsl run --uri 'nlp2dsl://cmd/PLAN?text=wyślij+fakturę&mode=auto'
```

Powrót: [packages/README.md](../README.md)
