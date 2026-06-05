# nlp2cmd-planner

**IntentIR → ExecutionPlanIR** przez strategie planowania (`PlanStrategy`).

## Użycie

```python
from nlp2cmd_planner import PlanningPipeline

plan = PlanningPipeline().run("znajdz pliki *.py w src")
print(plan.steps[0].dsl)  # find src -name "*.py"
```

## Strategie

| Strategia | Warunek | Wynik |
|-----------|---------|-------|
| `RuleShellPlanStrategy` | `target_kind=shell`, intencje `find` / `list` / … | `find …` / `ls -la` |
| `RestWorkflowPlanStrategy` | `NLP2CMD_NLP2DSL_WORKFLOW=1` + intencja workflow / REST | `POST /workflow/run` z DSL backendu |

Router wybiera **pierwszą** pasującą strategię (shell ma pierwszeństwo przed REST).

### Workflow REST

```bash
export NLP2CMD_NLP2DSL_WORKFLOW=1
export NLP2DSL_BACKEND_URL=http://127.0.0.1:8010

nlp2cmd plan "Wyslij fakture na 1500 PLN do a@b.pl" --json
```

Niedopasowane intencje (np. `navigate`/browser bez strategii) → `UnsupportedIntentError` → użyj legacy nlp2cmd (`-q … -r`).

## Instalacja

```bash
pip install -e packages/pact-ir
pip install -e packages/nlp2cmd-intent
pip install -e packages/nlp2cmd-planner
```

## Testy

```bash
pytest packages/nlp2cmd-planner/tests/
```
