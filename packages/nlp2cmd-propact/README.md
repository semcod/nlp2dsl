# nlp2cmd-propact

Bridge **ExecutionPlanIR → Propact markdown** + **HybridPlanExecutor**.

## Propact blocks

| `target_kind` | Markdown |
|---------------|----------|
| `shell` | ` ```propact:shell` ` |
| `rest` | ` ```propact:rest` ` |
| `mcp` | ` ```propact:mcp` ` |
| `ws` | ` ```propact:ws` ` |
| `browser`, `sql`, `desktop` | ` ```propact:delegate` ` (wykonanie przez nlp2cmd) |

## Użycie (Python)

```python
from nlp2cmd_planner import PlanningPipeline
from nlp2cmd_propact import HybridPlanExecutor, plan_to_propact_markdown

plan = PlanningPipeline().run("znajdz pliki *.py w src")
print(plan_to_propact_markdown(plan))

result = HybridPlanExecutor().run(plan, dry_run=False)
print(result.stdout)
```

## CLI

```bash
export NLP2CMD_INTEGRATION=1
export LANG=C.UTF-8

nlp2cmd plan "znajdz pliki *.py w src"
nlp2cmd plan "znajdz pliki *.py w src" --explain    # execution_route per step
nlp2cmd plan "znajdz pliki *.py w src" --json       # + execution_routes
nlp2cmd plan "znajdz pliki *.py w src" --execute    # hybrid executor
nlp2cmd plan "znajdz pliki *.py w src" --execute --dry-run
```

Struktura zapytania (IntentIR): `nlp2dsl show "…"`.

## Wykonanie bez Propact

Gdy `propact` nie jest w PATH, plany **shell-only** wykonują się przez subprocess (`NLP2CMD_PROPACT_FALLBACK=shell`, domyślnie). Plany REST/MCP/WS wymagają `pip install 'propact[semantic]'`.

## Instalacja

```bash
./scripts/setup-dev.sh   # z katalogu nlp2dsl
pip install -e ../nlp2cmd[integration]
```

Browser/desktop/canvas → delegacja do legacy **nlp2cmd** (`PipelineRunner`).
