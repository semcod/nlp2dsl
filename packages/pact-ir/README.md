# pact-ir

Wspólna reprezentacja zamiaru i planu wykonania między **nlp2cmd**, **nlp2dsl** i **Propact**.

## Typy

- `IntentIR` — co użytkownik chce (format `nlp2cmd.intent_ir.v1`)
- `ExecutionPlanIR` — jak to wykonać (format `nlp2cmd.execution_plan_ir.v1`)
- `TargetKind` — shell, browser, rest, sql, …
- `ExecutionRisk` — low, medium, high, destructive

## Przykład

```python
from pact_ir import IntentIR, ExecutionPlanIR, PlanStep, TargetKind

intent = IntentIR(
    query="znajdź pliki *.py w src",
    intent="find",
    domain="shell",
    target_kind=TargetKind.SHELL,
    confidence=0.95,
)
plan = ExecutionPlanIR.from_intent(
    intent,
    steps=[
        PlanStep(
            id="s1",
            action="shell_find",
            target_kind=TargetKind.SHELL,
            dsl='find src -name "*.py"',
        )
    ],
    source="rule_shell",
)
```

## Instalacja

```bash
pip install -e packages/pact-ir
```

Zależność pozostałych pakietów w `packages/` — instaluj pierwszy.
