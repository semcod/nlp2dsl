# Roadmap refaktoryzacji nlp2dsl: platforma kontraktów 30/60/90

Ten dokument przekłada kierunek z `REFACTOR-PLAN.md` na plan wykonawczy. Cel nie jest
"więcej LLM", tylko spójna platforma: naturalny język jako wejście, kontrakt jako
źródło prawdy, DSL jako deterministyczny plan, walidacja jako bramka i worker jako
kontrolowany efekt uboczny.

## Zasady architektury

1. Jedna definicja akcji zasila parser, formularz, DSL, walidację, executor i dokumentację.
2. Każdy request przechodzi etapy: `parse -> clarify -> plan -> validate -> simulate -> execute`.
3. Side effects mają idempotency key, audit trail i rozróżnienie preview/commit.
4. LLM może proponować kontrakty i walidatory, ale runtime używa tylko zatwierdzonych artefaktów.
5. Ewaluacja mierzy klasy błędów, nie tylko pass rate.

## Granice modułów

| Bounded context | Odpowiedzialność | Docelowe moduły |
|-----------------|------------------|-----------------|
| `intent-understanding` | parse rules/LLM, entity extraction, clarification, provenance pól | `nlp-service/app/routing`, `nlp-service/app/parsing`, docelowo `nlp2dsl_sdk/understanding` |
| `action-contracts` | kontrakty akcji, schema, formularze, capability metadata, wersje | `nlp2dsl_sdk/contracts`, później `packages/contract` |
| `workflow-planning` | DSL/IR, plan kroków, mapowanie encji, preview/simulate | `nlp-service/app/dsl`, `nlp2dsl_sdk/workflow` |
| `validation-policy` | preflight/post-exec checks, policy, attachment, runtime availability | `nlp2dsl_sdk/validation`, cienkie adaptery backend/nlp-service/worker |
| `workflow-execution` | dispatch, idempotencja, retry, worker/delegate/mullm, audit | `backend/app/routers`, `backend/app/engine`, `worker` |
| `observability-eval` | events, traces, TestQL, golden dataset, regression reports | `examples/.nlp2dsl`, `scripts`, `testql-scenarios` |

## Docelowa struktura repo

```text
nlp2dsl_sdk/
  contracts/
    action.py           # ActionContract, FieldContract, Capability
    registry.py         # registry loader + versioning
    forms.py            # JSON Schema/form schema from contract
    prompt_catalog.py   # LLM prompt fragments from contracts
  workflow/
    dsl.py              # Workflow/Step canonical models
    planning.py         # plan/simulate helpers
    events.py           # WorkflowCreated, StepValidated, ...
  validation/
    issue.py
    pipeline.py
    rules/
  evaluation/
    golden.py
    metrics.py
  export/
    markpact.py           # ActionContract + DSL → README
    pactown.py            # ecosystem manifest

nlp-service/app/
  routing/              # intent + parser orchestration
  dsl/                  # mapper + planner API
  conversation/         # state machine, slot fill, clarification
  routers/              # thin HTTP layer

backend/app/
  routers/
  execution/            # dispatcher, idempotency, events
  audit/                # execution log/read model

worker/
  executors/            # side-effect handlers by action family
```

## Roadmap 30 dni

**Cel:** ustabilizować kontrakty i request lifecycle bez dużego przestawiania runtime.

1. Wydzielić `ActionContract` w SDK.
   - Pola: `name`, `version`, `category`, `required`, `optional`, `quality_required`,
     `input_model`, `execution_backend`, `capabilities`, `approval_required`.
   - Adaptery: istniejący registry nlp-service -> `ActionContract`.
   - Kryterium: `/nlp/actions`, `/workflow/actions`, worker drift check i formularze używają tych samych danych.
   - Status: rozpoczęte w `nlp2dsl_sdk/contracts/` jako warstwa kompatybilna z obecnym registry.

2. Ujednolicić lifecycle requestu.
   - Dodać jawne modele: `ParseResult`, `ClarificationRequest`, `PlanResult`,
     `ValidationReport`, `ExecutionRequest`.
   - Obecne endpointy mogą zostać, ale wewnątrz powinny składać te etapy.
   - Kryterium: trace conversation pokazuje etap, status i źródło decyzji.
   - Status: rozpoczęte w `nlp2dsl_sdk/workflow/`; dodany plan lifecycle oraz
     kompatybilne endpointy `/workflow/plan`, `/workflow/validate` i `/workflow/execute`.

3. Domknąć idempotencję side effects.
   - Dodać `idempotency_key` do workflow/step execution.
   - Backend deduplikuje `send_email`, `send_invoice`, `crm_update` na poziomie requestu.
   - Kryterium: ponowne `uruchom` nie wykonuje side effect drugi raz i zwraca poprzedni wynik.
   - Status: **zrobione** — wspólny helper `backend/app/workflow_execute.py` obsługuje
     `/workflow/execute`, `/workflow/from-text?execute=true` (jawny key) oraz chat `uruchom`
     (auto-key z `conversation_id` + fingerprint DSL); memory/Postgres store, replay i konflikt.

4. Rozszerzyć golden dataset.
   - Osobne przypadki dla: entity extraction, DSL mapping, unnecessary clarification,
     unsafe execution block, attachment validation.
   - Kryterium: raport pokazuje metryki per akcja i per klasa błędu.
   - Status: **zrobione** — `nlp2dsl_sdk/evaluation/` (golden_cases.yaml, metrics),
     przykład `16-golden-eval`, klasyfikacja outcome per focus/action.

5. CI validate exportu markpact/pactown.
   - Kryterium: canonical DSL (`report_and_email`, `full_report_flow`) przechodzi
     `markpact` parse + `pactown` load w CI.
   - Status: **zrobione** — `scripts/validate-publish-export.py --strict`,
     workflow `platform-ci.yml`.

6. Contract drift gate (intract-aligned preflight).
   - Kryterium: nlp-service registry, worker handlers i backend fallback bez driftu.
   - Status: **zrobione** — `nlp2dsl_sdk/validation/contract_drift.py`,
     `scripts/validate-contract-drift.py`, `GET /workflow/catalog/drift`, `intract.yaml`.

## Roadmap 60 dni

**Cel:** zrobić z walidacji i polityk moduł współdzielony, a z wykonania kontrolowany pipeline.

1. Przenieść contracts do jednego pakietu.
   - Opcja przejściowa: `nlp2dsl_sdk/contracts`.
   - Opcja docelowa: `packages/contract`.
   - Kryterium: backend, nlp-service i worker importują te same modele.

2. Rozdzielić API etapów.
   - `POST /nlp/parse`
   - `POST /workflow/plan`
   - `POST /workflow/validate`
   - `POST /workflow/simulate`
   - `POST /workflow/execute`
   - Kryterium: `/workflow/from-text` i chat są kompozycją tych etapów, nie osobną logiką.
   - Status: **częściowo** — `/workflow/plan`, `/validate`, `/simulate`, `/execute` działają;
     `/workflow/from-text` obsługuje `execute` i `simulate` jako kompozycję plan→validate→stage.

3. Event-driven execution v1.
   - Zdarzenia: `WorkflowCreated`, `StepPlanned`, `StepValidated`, `AwaitingUserInput`,
     `StepExecutionRequested`, `StepExecuted`, `ExecutionFailed`, `WorkflowCompleted`.
   - Zapisać eventy w repo backendu obok obecnej historii workflow.
   - Kryterium: da się odtworzyć status workflow z eventów i zbudować transcript/audit.
   - Status: **zrobione (v1)** — `nlp2dsl_sdk/workflow/events.py`, persystencja w
     `WorkflowRepo.append_event`, `GET /workflow/history/{id}/events`, correlation ID
     z `X-Request-ID`, replay snapshot przez `workflow_snapshot_from_events`.

4. Capability/policy layer.
   - Polityki: kto może wykonać akcję, czy wymaga approval, limity kanałów/URI, dry-run only.
   - Kryterium: walidacja blokuje wykonanie zanim worker dostanie request.
   - Status: **zrobione (v1)** — `nlp2dsl_sdk/validation/capability_policy.py`,
     `backend/app/execution_policy.py`, bramka na `/workflow/execute` i chat `uruchom`,
     opcjonalnie `POST /workflow/validate?check_policy`, ACL przez `/nlp/access/check`.

## Roadmap 90 dni

**Cel:** przygotować platformę do generowanych pluginów i bezpiecznej autonomii.

1. LLM-generated contracts jako workflow, nie magiczny runtime.
   - LLM generuje propozycję `ActionContract` + walidatory + przykłady.
   - System zapisuje ją jako draft w `.nlp2dsl/generated/contracts`.
   - Runtime ładuje tylko kontrakty zatwierdzone albo podpisane lokalnie.
   - Kryterium: nowa akcja może przejść `draft -> validate -> approve -> active`.
   - Status: **rozpoczęte (v1)** — `nlp2dsl_sdk/contracts/draft.py`,
     `scripts/validate-contract-draft.py`, przykładowy draft `example_notify_webhook.draft.yaml`,
     CI gate `--strict` (drafty z błędami failują; status `draft` OK bez `--require-approved`).

2. Plugin SDK.
   - Struktura pluginu: `plugin.yaml`, `contracts/*.yaml`, `validators/*.py`,
     `executors/*.py`, `tests/*.yaml`.
   - Kryterium: plugin może dodać akcję bez edycji `backend`, `nlp-service` i `worker`.

3. Autonomiczna naprawa walidacji.
   - Resolver bazuje na `ValidationIssue.code`, nie na tekście komunikatu.
   - Strategie: ask user, autofill from DOQL, generate artifact, pick fixture, block unsafe, retry.
   - Kryterium: każdy fix ma audit entry: issue -> strategy -> result.

4. Production readiness.
   - Dead-letter queue dla failed steps.
   - Retry policy per action.
   - Correlation ID we wszystkich zdarzeniach.
   - Dashboard/regression report per action version.

## Kontrakt jako źródło prawdy

Minimalny kontrakt powinien wystarczyć do wygenerowania formularza, promptu, walidacji i
dispatchu:

```yaml
name: send_email
version: 1
category: business
execution_backend: worker
required:
  to:
    type: email
    description: Adres odbiorcy
quality_required:
  body:
    type: string
    description: Treść wiadomości
optional:
  subject:
    type: string
capabilities:
  side_effect: true
  idempotency: required
  approval_required: false
validators:
  preflight:
    - email.to.valid
    - text.body.present_or_clarify
  post_execute:
    - execution.worker.completed
```

## Generowanie pluginów przez LLM

To powinno być możliwe, ale w dwóch fazach:

1. **Draft generation:** LLM generuje kontrakt, walidatory, przykłady i testy do katalogu
   tymczasowego. To jest artefakt do walidacji, nie aktywny kod.
2. **Activation:** lokalny validator uruchamia testy, sprawdza bezpieczeństwo, wymagane pola,
   importy i brak sekretów. Dopiero potem kontrakt trafia do aktywnego registry.

Bez tej separacji LLM mógłby wygenerować walidator, który omija polityki albo wykonuje
niekontrolowany side effect. Granica bezpieczeństwa musi być po stronie registry/policy.

## Metryki sukcesu

| Obszar | Metryka |
|--------|---------|
| Kontrakty | nowa akcja wymaga edycji 1 kontraktu + testu, bez zmian w 3 serwisach |
| Walidacja | 100% błędów runtime ma `ValidationIssue.code` |
| Idempotencja | retry/ponowny `uruchom` nie duplikuje side effects |
| Ewaluacja | raport per action: parse accuracy, entity accuracy, DSL accuracy, clarification rate |
| Observability | każdy workflow ma correlation ID, event log, transcript i artifact trace |
