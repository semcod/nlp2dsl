# MVP Automation Platform

Reusable Python SDK for the NLP2DSL platform

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Interfaces](#interfaces)
- [Quality Pipeline (`pyqual.yaml`)](#quality-pipeline-pyqualyaml)
- [Configuration](#configuration)
- [Dependencies](#dependencies)
- [Deployment](#deployment)
- [Environment Variables (`.env.example`)](#environment-variables-envexample)
- [Release Management (`goal.yaml`)](#release-management-goalyaml)
- [Code Analysis](#code-analysis)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Intent](#intent)

## Metadata

- **name**: `nlp2dsl`
- **version**: `0.0.14`
- **python_requires**: `>=3.10`
- **license**: Apache-2.0
- **ai_model**: `openrouter/qwen/qwen3-coder-next`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, testql(3), app.doql.less, pyqual.yaml, goal.yaml, .env.example, docker-compose.yml, project/(3 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.less`)

```less markpact:doql path=app.doql.less
// LESS format — define @variables here as needed

app {
  name: nlp2dsl;
  version: 0.0.14;
}

dependencies {
  runtime: requests>=2.31.0;
}

entity[name="NLPIntent"] {
  intent: string!;
  confidence: float!;
}

entity[name="NLPEntities"] {
  amount: float | None;
  currency: str | None;
  to: str | None;
  subject: str | None;
  message: str | None;
  channel: str | None;
  chat_id: str | None;
  title: str | None;
  report_type: str | None;
  format: str | None;
  entity: str | None;
  data: dict | None;
  setting_path: str | None;
  setting_value: str | None;
  section: str | None;
  file_path: str | None;
  content: str | None;
  directory: str | None;
  pattern: str | None;
  line_start: int | None;
  line_end: int | None;
  mode: str | None;
  action_name: str | None;
  action_description: str | None;
  required_fields: list[str] | None;
  aliases: list[str] | None;
  description: str | None;
  language: str | None;
  context: str | None;
  include_tests: bool | None;
  shell_command: str | None;
}

entity[name="DSLStep"] {
  action: string!;
  config: json!;
}

entity[name="WorkflowDSL"] {
  name: string!;
  trigger: str | None;
  steps: list[DSLStep]!;
}

entity[name="ConversationState"] {
  id: string!;
  intent: str | None;
  entities: json!;
  missing: list[str]!;
  dsl: WorkflowDSL | None;
  status: string!;
  history: list[dict]!;
}

entity[name="Step"] {
  id: string!;
  action: string!;
  config: json!;
}

entity[name="ActionInfo"] {
  name: string!;
  description: string!;
  config_schema: json!;
}

database[name="postgres"] {
  type: postgresql;
  url: env.DATABASE_URL;
}

database[name="redis"] {
  type: redis;
  url: env.REDIS_URL;
}

interface[type="api"] {
  type: rest;
  framework: fastapi;
}

interface[type="cli"] {
  framework: argparse;
}
interface[type="cli"] page[name="nlp2dsl-demo"] {

}

integration[name="nlp"] {
  type: api;
}

deploy {
  target: docker-compose;
  compose_file: docker-compose.yml;
}

environment[name="local"] {
  runtime: docker-compose;
  env_file: .env;
  python_version: >=3.10;
}

environment[name="backup"] {
  runtime: docker-compose;
  env_file: .env.backup;
}
```

## Interfaces

### CLI Entry Points

- `nlp2dsl-demo`

### testql Scenarios

#### `testql-scenarios/generated-api-smoke.testql.toon.yaml`

```toon markpact:testql path=testql-scenarios/generated-api-smoke.testql.toon.yaml
# SCENARIO: Auto-generated API Smoke Tests
# TYPE: api
# GENERATED: true
# DETECTORS: FastAPIDetector, WebSocketDetector, ConfigEndpointDetector

CONFIG[5]{key, value}:
  base_url, http://localhost:8101
  timeout_ms, 10000
  retry_count, 3
  retry_backoff_ms, 1000
  detected_frameworks, FastAPIDetector, WebSocketDetector, ConfigEndpointDetector

# Wait for service to be ready
WAIT 1000

# Health check
API GET /api/health 200
ASSERT_STATUS 200

# REST API Endpoints (1 unique)
API[1]{method, endpoint, expected_status}:
  GET, /, 200

# Capture useful values from responses for subsequent tests
# CAPTURE request_id FROM 'headers.x-request-id'
# CAPTURE session_token FROM 'body.token'

ASSERT[2]{field, operator, expected}:
  _status, <, 500
  _status, >=, 200

# Conditional flow for error handling
FLOW[2]{condition, action}:
  _status >= 500, LOG 'Server error detected'
  _status == 429, WAIT 2000  # Rate limit - wait and retry


# Summary by Framework:
#   docker: 7 endpoints
```

#### `testql-scenarios/generated-cli-tests.testql.toon.yaml`

```toon markpact:testql path=testql-scenarios/generated-cli-tests.testql.toon.yaml
# SCENARIO: CLI Command Tests
# TYPE: cli
# GENERATED: true

CONFIG[2]{key, value}:
  cli_command, python -m nlp2dsl
  timeout_ms, 10000

# Test 1: CLI help command
SHELL "python -m nlp2dsl --help" 5000
ASSERT_EXIT_CODE 0
ASSERT_STDOUT_CONTAINS "usage"

# Test 2: CLI version command
SHELL "python -m nlp2dsl --version" 5000
ASSERT_EXIT_CODE 0

# Test 3: CLI main workflow (dry-run)
SHELL "python -m nlp2dsl --help" 10000
ASSERT_EXIT_CODE 0
```

#### `testql-scenarios/generated-from-pytests.testql.toon.yaml`

```toon markpact:testql path=testql-scenarios/generated-from-pytests.testql.toon.yaml
# SCENARIO: Auto-generated from Python Tests
# TYPE: integration
# GENERATED: true

CONFIG[2]{key, value}:
  base_url, ${api_url:-http://localhost:8101}
  timeout_ms, 10000

# Converted 118 assertions from pytest
ASSERT[118]{field, operator, expected}:
  client.backend_url, ==, "http://backend.env"
  client.nlp_service_url, ==, "http://nlp.env"
  client.worker_url, ==, "http://worker.env"
  client.timeout, ==, 12.5
  generated.status, ==, "complete"
  execution.status, ==, "completed"
  start.conversation_id, ==, "conv-1"
  message.conversation_id, ==, "conv-1"
  schema.action, ==, "send_invoice"
  schema.fields[0].name, ==, "to"
  session.calls[0][1], ==, "http://backend.test/workflow/from-text"
  session.calls[0][2].json, ==, {"text": "Wyślij fakturę"
  session.calls[1][1], ==, "http://backend.test/workflow/run"
  session.calls[1][2].json.steps[0].config.amount, ==, 1500.0
  session.calls[1][2].json.steps[0].config.to, ==, "klient@firma.pl"
  session.calls[2][1], ==, "http://backend.test/workflow/chat/start"
  session.calls[2][2].json, ==, {"text": "Chcę wysłać fakturę"}
  session.calls[3][1], ==, "http://backend.test/workflow/chat/message"
  session.calls[3][2].json, ==, {"conversation_id": "conv-1"
  session.calls[4][1], ==, "http://backend.test/workflow/actions/schema/send_invoice"
  workflow_step("notify_slack", channel="#ops", message="Deploy done"), ==, {
  crm_result.status, ==, "completed"
  slack_result.status, ==, "completed"
  invoice_result.status, ==, "completed"
  session.calls[0][1], ==, "http://backend.test/workflow/run"
  session.calls[0][2].json.steps[0].action, ==, "crm_update"
  session.calls[0][2].json.steps[0].config.entity, ==, "lead"
  session.calls[1][2].json.steps[0].action, ==, "notify_slack"
  session.calls[1][2].json.steps[0].config.channel, ==, "#ops"
  invoice_payload.name, ==, "invoice_notification_workflow"
  [step.action for step in invoice_payload.steps], ==, [
  invoice_payload.steps[1].config.to, ==, "billing@firma.pl"
  invoice_payload.steps[2].config.channel, ==, "#finance"
  direct.language, ==, "python"
  conversation.conversation_id, ==, "conv-2"
  continuation.conversation_id, ==, "conv-2"
  worker.status, ==, "completed"
  session.calls[0][1], ==, "http://nlp.test/code/generate"
  session.calls[1][1], ==, "http://nlp.test/code/languages"
  session.calls[2][1], ==, "http://nlp.test/chat/start"
  session.calls[2][2].data, ==, {"text": "Chcę napisać program w Javie"}
  session.calls[3][1], ==, "http://nlp.test/chat/message"
  session.calls[3][2].data, ==, {"conversation_id": "conv-2"
  session.calls[4][1], ==, "http://worker.test/execute"
  session.calls[4][2].json.action, ==, "generate_code"
  session.calls[4][2].json.config.language, ==, "cpp"
  health.backend.service, ==, "backend"
  health.nlp_service.service, ==, "nlp-service"
  health.worker.service, ==, "worker"
  session.calls[0][1], ==, "http://backend.test/health"
  session.calls[1][1], ==, "http://nlp.test/health"
  session.calls[2][1], ==, "http://worker.test/health"
  dialog.status, ==, "incomplete"
  s.worker_url, ==, "http://worker:8000"
  s.nlp_service_url, ==, "http://nlp-service:8002"
  s.worker_url, ==, "http://custom-worker:9000"
  s.worker_url, ==, "http://worker:8000"
  s.nlp_service_url, ==, "http://nlp-service:8002"
  s.worker_url, ==, "http://custom-worker:9000"
  client.backend_url, ==, "http://backend.env"
  client.nlp_service_url, ==, "http://nlp.env"
  client.worker_url, ==, "http://worker.env"
  client.timeout, ==, 12.5
  generated.status, ==, "complete"
  execution.status, ==, "completed"
  start.conversation_id, ==, "conv-1"
  message.conversation_id, ==, "conv-1"
  schema.action, ==, "send_invoice"
  schema.fields[0].name, ==, "to"
  session.calls[0][1], ==, "http://backend.test/workflow/from-text"
  session.calls[0][2].json, ==, {"text": "Wyślij fakturę"
  session.calls[1][1], ==, "http://backend.test/workflow/run"
  session.calls[1][2].json.steps[0].config.amount, ==, 1500.0
  session.calls[1][2].json.steps[0].config.to, ==, "klient@firma.pl"
  session.calls[2][1], ==, "http://backend.test/workflow/chat/start"
  session.calls[2][2].json, ==, {"text": "Chcę wysłać fakturę"}
  session.calls[3][1], ==, "http://backend.test/workflow/chat/message"
  session.calls[3][2].json, ==, {"conversation_id": "conv-1"
  session.calls[4][1], ==, "http://backend.test/workflow/actions/schema/send_invoice"
  workflow_step("notify_slack", channel="#ops", message="Deploy done"), ==, {
  crm_result.status, ==, "completed"
  slack_result.status, ==, "completed"
  invoice_result.status, ==, "completed"
  session.calls[0][1], ==, "http://backend.test/workflow/run"
  session.calls[0][2].json.steps[0].action, ==, "crm_update"
  session.calls[0][2].json.steps[0].config.entity, ==, "lead"
  session.calls[1][2].json.steps[0].action, ==, "notify_slack"
  session.calls[1][2].json.steps[0].config.channel, ==, "#ops"
  invoice_payload.name, ==, "invoice_notification_workflow"
  [step.action for step in invoice_payload.steps], ==, [
  invoice_payload.steps[1].config.to, ==, "billing@firma.pl"
  invoice_payload.steps[2].config.channel, ==, "#finance"
  direct.language, ==, "python"
  conversation.conversation_id, ==, "conv-2"
  continuation.conversation_id, ==, "conv-2"
  worker.status, ==, "completed"
  session.calls[0][1], ==, "http://nlp.test/code/generate"
  session.calls[1][1], ==, "http://nlp.test/code/languages"
  session.calls[2][1], ==, "http://nlp.test/chat/start"
  session.calls[2][2].data, ==, {"text": "Chcę napisać program w Javie"}
  session.calls[3][1], ==, "http://nlp.test/chat/message"
  session.calls[3][2].data, ==, {"conversation_id": "conv-2"
  session.calls[4][1], ==, "http://worker.test/execute"
  session.calls[4][2].json.action, ==, "generate_code"
  session.calls[4][2].json.config.language, ==, "cpp"
  health.backend.service, ==, "backend"
  health.nlp_service.service, ==, "nlp-service"
  health.worker.service, ==, "worker"
  session.calls[0][1], ==, "http://backend.test/health"
  session.calls[1][1], ==, "http://nlp.test/health"
  session.calls[2][1], ==, "http://worker.test/health"
  s.worker_url, ==, "http://worker:8000"
  s.nlp_service_url, ==, "http://nlp-service:8002"
  s.worker_url, ==, "http://custom-worker:9000"
  s.worker_url, ==, "http://worker:8000"
  s.nlp_service_url, ==, "http://nlp-service:8002"
  s.worker_url, ==, "http://custom-worker:9000"
  dialog.status, ==, "incomplete"
```

## Quality Pipeline (`pyqual.yaml`)

```yaml markpact:pyqual path=pyqual.yaml
pipeline:
  profile: python-minimal

  # Override metrics (profile defaults: cc_max=15, critical_max=0):
  metrics:
    critical_max: 5

  # Explicit stages matching the python-minimal profile.
  stages:
    - name: analyze
      tool: code2llm-filtered
      optional: true
      timeout: 0

    - name: validate
      tool: vallm-filtered
      optional: true
      timeout: 0

    - name: lint
      tool: ruff
      optional: true

    - name: prefact
      tool: prefact
      optional: true
      timeout: 900

    - name: fix
      tool: llx-fix
      optional: true
      timeout: 1800

    - name: test
      run: bash .pfix-test-wrapper.sh

  # If you want to tighten gates later, add more overrides here.

  # Environment (optional)
  env:
    LLM_MODEL: openrouter/qwen/qwen3-coder-next
```

## Configuration

```yaml
project:
  name: nlp2dsl
  version: 0.0.14
  env: local
```

## Dependencies

### Runtime

```text markpact:deps python
requests>=2.31.0
```

## Deployment

```bash markpact:run
pip install nlp2dsl

# development install
pip install -e .[dev]
```

### Docker Compose (`docker-compose.yml`)

- **backend** image=`./backend` ports: `${NLP2DSL_BACKEND_HOST_PORT:-8010}:8000`
- **nlp-service** image=`./nlp-service` ports: `${NLP2DSL_NLP_HOST_PORT:-8012}:8002`
- **worker** image=`./worker` ports: `${NLP2DSL_WORKER_HOST_PORT:-8004}:8000`
- **postgres** image=`postgres:16-alpine`
- **redis** image=`redis:7-alpine`

## Environment Variables (`.env.example`)

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | `*(not set)*` | ── OpenRouter (domyślny) ──────────────────────────────────── |
| `LLM_MODEL` | `openrouter/openai/gpt-5-mini` |  |
| `LLM_TEMPERATURE` | `0` | ── LLM Settings ───────────────────────────────────────────── |
| `LLM_MAX_TOKENS` | `1024` |  |
| `LLM_FALLBACK_THRESHOLD` | `0.5` |  |
| `NLP2DSL_BACKEND_HOST_PORT` | `8010` | 8002 jest zajęty przez Mullm Projector, gdy oba stacki działają równolegle. |
| `NLP2DSL_NLP_HOST_PORT` | `8012` |  |
| `NLP2DSL_WORKER_HOST_PORT` | `8004` |  |
| `NLP2DSL_CONFIG` | `./nlp2dsl.yaml` |  |
| `NLP2DSL_AGENT_ID` | `user` |  |
| `DEEPGRAM_API_KEY` | `*(not set)*` | Zdobądź klucz: https://console.deepgram.com/ |

## Release Management (`goal.yaml`)

- **versioning**: `semver`
- **commits**: `conventional` scope=`nlp2dsl`
- **changelog**: `keep-a-changelog`
- **build strategies**: `python`, `nodejs`, `rust`
- **version files**: `VERSION`, `pyproject.toml:version`, `venv/lib/python3.13/site-packages/cryptography/__init__.py:__version__`

## Code Analysis

### `project/map.toon.yaml`

```toon markpact:analysis path=project/map.toon.yaml
# nlp2dsl | 135f 13046L | python:116,shell:13,javascript:3,rust:2,less:1 | 2026-06-04
# stats: 353 func | 122 cls | 135 mod | CC̄=3.3 | critical:13 | cycles:0
# alerts[5]: CC test_workflow_and_conversation_endpoints=17; CC test_code_generation_methods_hit_expected_services=16; CC _actions_from_yaml_areas=14; CC test_new_workflow_helpers_are_data_driven=14; CC chat_message=12
# hotspots[5]: _execute_workflow fan=19; websocket_chat fan=16; map_to_dsl fan=14; resolve_intent fan=14; test_code_generation fan=14
# evolution: baseline
# Keys: M=modules, D=details, i=imports, e=exports, c=classes, f=functions, m=methods
M[135]:
  .pfix-test-wrapper.sh,16
  app.doql.less,125
  backend/app/__init__.py,1
  backend/app/config.py,43
  backend/app/db/__init__.py,50
  backend/app/db/memory.py,38
  backend/app/db/postgres.py,173
  backend/app/engine.py,270
  backend/app/logging_setup.py,101
  backend/app/main.py,49
  backend/app/routers/__init__.py,1
  backend/app/routers/chat.py,125
  backend/app/routers/settings.py,82
  backend/app/routers/system.py,30
  backend/app/routers/workflow.py,190
  backend/app/schemas.py,65
  backend/app/workflow.py,23
  backend/app/workflow_events.py,92
  backend/tests/__init__.py,1
  backend/tests/conftest.py,32
  backend/tests/test_config.py,83
  backend/tests/test_logging.py,124
  backend/tests/test_persistence.py,185
  backend/tests/test_workflow_api.py,267
  examples/01-invoice/main.py,24
  examples/01-invoice/run.sh,7
  examples/02-email/main.py,24
  examples/02-email/run.sh,7
  examples/03-report-and-notify/main.py,24
  examples/03-report-and-notify/run.sh,7
  examples/04-scheduled-report/main.py,24
  examples/04-scheduled-report/run.sh,7
  examples/05-conversation-flow/main.py,39
  examples/05-conversation-flow/run.sh,7
  examples/basic/invoice/run.sh,1
  examples/code_generation_examples.py,26
  metrun-profile.sh,49
  nlp-service/app/__init__.py,1
  nlp-service/app/access/__init__.py,16
  nlp-service/app/access/bootstrap.py,4
  nlp-service/app/access/config.py,4
  nlp-service/app/access/native.py,4
  nlp-service/app/access/policy.py,4
  nlp-service/app/access/uri_match.py,4
  nlp-service/app/audio_parser.py,149
  nlp-service/app/code_generator.py,280
  nlp-service/app/config.py,61
  nlp-service/app/conversation/__init__.py,14
  nlp-service/app/conversation/merge.py,26
  nlp-service/app/conversation/orchestrator.py,108
  nlp-service/app/conversation/responses.py,273
  nlp-service/app/dsl/__init__.py,5
  nlp-service/app/dsl/forms.py,84
  nlp-service/app/dsl/mapper.py,190
  nlp-service/app/execution/__init__.py,15
  nlp-service/app/execution/delegate.py,30
  nlp-service/app/execution/system.py,343
  nlp-service/app/governance/__init__.py,15
  nlp-service/app/governance/bootstrap.py,79
  nlp-service/app/governance/config.py,166
  nlp-service/app/governance/policy.py,303
  nlp-service/app/governance/uri_match.py,43
  nlp-service/app/logging_setup.py,101
  nlp-service/app/main.py,584
  nlp-service/app/mapper.py,6
  nlp-service/app/orchestrator.py,22
  nlp-service/app/parser_llm.py,6
  nlp-service/app/parser_rules.py,6
  nlp-service/app/parsing/__init__.py,4
  nlp-service/app/parsing/facade.py,6
  nlp-service/app/registry.py,391
  nlp-service/app/routing/__init__.py,15
  nlp-service/app/routing/intent.py,54
  nlp-service/app/routing/native.py,144
  nlp-service/app/routing/observability.py,58
  nlp-service/app/routing/parser/__init__.py,4
  nlp-service/app/routing/parser/facade.py,40
  nlp-service/app/routing/parser/llm.py,188
  nlp-service/app/routing/parser/rules.py,382
  nlp-service/app/routing/resolve.py,149
  nlp-service/app/schemas.py,132
  nlp-service/app/settings.py,252
  nlp-service/app/store/__init__.py,31
  nlp-service/app/store/factory.py,47
  nlp-service/app/store/memory.py,24
  nlp-service/app/store/redis_store.py,59
  nlp-service/app/system_executor.py,36
  nlp-service/integrations/__init__.py,6
  nlp-service/integrations/loader.py,63
  nlp-service/integrations/mullm/__init__.py,2
  nlp-service/integrations/mullm/registry.py,67
  nlp-service/tests/__init__.py,1
  nlp-service/tests/conftest.py,102
  nlp-service/tests/test_access.py,75
  nlp-service/tests/test_execution_delegate.py,25
  nlp-service/tests/test_mapper.py,252
  nlp-service/tests/test_orchestrator.py,222
  nlp-service/tests/test_parser_rules.py,237
  nlp-service/tests/test_registry.py,169
  nlp-service/tests/test_routing_observability.py,42
  nlp-service/tests/test_routing_resolve.py,66
  nlp-service/tests/test_store.py,193
  nlp-service/tests/test_system_executor.py,422
  nlp2dsl_sdk/__init__.py,34
  nlp2dsl_sdk/__main__.py,42
  nlp2dsl_sdk/client.py,581
  nlp2dsl_sdk/demos.py,688
  project.sh,59
  run-all-tests.sh,45
  tauri-wrapper/desktop.sh,80
  tauri-wrapper/scripts/dev.js,57
  tauri-wrapper/scripts/serve-dist.js,140
  tauri-wrapper/src-tauri/build.rs,4
  tauri-wrapper/src-tauri/src/main.rs,8
  tauri-wrapper/test/mvp-voice-chat-wrapper.test.js,9
  test_code_generation.py,140
  tests/conftest.py,11
  tests/e2e/__init__.py,1
  tests/e2e/conftest.py,129
  tests/e2e/test_backend.py,152
  tests/e2e/test_chat_ui.py,263
  tests/e2e/test_nlp_service.py,216
  tests/e2e/test_websocket.py,112
  tests/run.sh,86
  tests/test_nlp2dsl_sdk.py,259
  tests/test_placeholder.py,12
  tests/test_tests.py,12
  tree.sh,2
  worker/__init__.py,6
  worker/config.py,28
  worker/logging_setup.py,101
  worker/tests/__init__.py,1
  worker/tests/conftest.py,46
  worker/tests/test_worker.py,173
  worker/worker.py,231
D:
  backend/app/__init__.py:
  backend/app/config.py:
    e: BackendSettings
    BackendSettings:
  backend/app/db/__init__.py:
    e: create_workflow_repo,WorkflowRepo
    WorkflowRepo: save_run(4),update_run_status(2),get_run(1),list_runs(2),count_runs(0)  # Abstrakcja persystencji workflow.
    create_workflow_repo()
  backend/app/db/memory.py:
    e: MemoryWorkflowRepo
    MemoryWorkflowRepo: __init__(1),save_run(4),update_run_status(2),get_run(1),list_runs(2),count_runs(0)
  backend/app/db/postgres.py:
    e: Base,WorkflowRunModel,PostgresWorkflowRepo
    Base:
    WorkflowRunModel: to_dict(0)
    PostgresWorkflowRepo: __init__(1),_ensure_engine(0),_get_session_factory(0),_ensure_tables(0),save_run(4),update_run_status(2),get_run(1),list_runs(2),count_runs(0),close(0)
  backend/app/engine.py:
    e: _workflow_steps_payload,_persist_workflow_snapshot,_publish_workflow_event,_execute_workflow,_track_background_task,run_workflow,start_workflow
    _workflow_steps_payload(result)
    _persist_workflow_snapshot(req;result)
    _publish_workflow_event(workflow_id;event_type;status;message)
    _execute_workflow(req;workflow_id)
    _track_background_task(task)
    run_workflow(req)
    start_workflow(req)
  backend/app/logging_setup.py:
    e: get_request_id,setup_logging,JSONFormatter,RequestIDMiddleware
    JSONFormatter: __init__(1),format(1)  # Emit log records as single-line JSON objects.
    RequestIDMiddleware: __init__(2),dispatch(2)  # Generate or forward X-Request-ID for every HTTP request.
    get_request_id()
    setup_logging(service;level)
  backend/app/main.py:
    e: health
    health()
  backend/app/routers/__init__.py:
  backend/app/routers/chat.py:
    e: _proxy_chat_payload,chat_start,chat_message,chat_get_state
    _proxy_chat_payload(request;endpoint)
    chat_start(request)
    chat_message(request)
    chat_get_state(conversation_id)
  backend/app/routers/settings.py:
    e: actions_schema,action_schema,get_settings,get_settings_section,update_settings_section,set_setting,reset_settings
    actions_schema()
    action_schema(action)
    get_settings()
    get_settings_section(section)
    update_settings_section(section;body)
    set_setting(body)
    reset_settings(body)
  backend/app/routers/system.py:
    e: system_execute
    system_execute(body)
  backend/app/routers/workflow.py:
    e: _format_sse,_workflow_snapshot,list_actions,run_workflow_endpoint,start_workflow_endpoint,get_history,get_workflow,stream_workflow,workflow_from_text
    _format_sse(event;data)
    _workflow_snapshot(run)
    list_actions()
    run_workflow_endpoint(req)
    start_workflow_endpoint(req)
    get_history()
    get_workflow(workflow_id)
    stream_workflow(workflow_id;request)
    workflow_from_text(body)
  backend/app/schemas.py:
    e: StepStatus,Step,RunWorkflowRequest,StepResult,WorkflowResult,ActionInfo
    StepStatus:
    Step:  # Pojedynczy krok workflow — deklaratywny opis akcji.
    RunWorkflowRequest:  # Żądanie uruchomienia workflow — DSL biznesowy.
    StepResult:
    WorkflowResult:
    ActionInfo:  # Opis dostępnej akcji (do listowania w GUI / API).
  backend/app/workflow.py:
  backend/app/workflow_events.py:
    e: WorkflowEvent,WorkflowEventHub
    WorkflowEvent: is_terminal(0),to_dict(0)
    WorkflowEventHub: __init__(0),subscribe(1),unsubscribe(2),publish(1),subscriber_count(1)  # In-memory broadcaster dla workflow lifecycle events.
  backend/tests/__init__.py:
  backend/tests/conftest.py:
    e: client
    client()
  backend/tests/test_config.py:
    e: TestBackendSettingsDefaults,TestBackendSettingsEnvOverride,TestBackendSettingsIntegration
    TestBackendSettingsDefaults: test_worker_url_default(1),test_nlp_service_url_default(1),test_postgres_url_default_none(1),test_log_level_default(1)  # BackendSettings reads sane defaults when env vars are absent
    TestBackendSettingsEnvOverride: test_worker_url_from_env(1),test_postgres_url_from_env(1),test_log_level_from_env(1),test_extra_env_vars_ignored(1)  # BackendSettings picks up values from env vars.
    TestBackendSettingsIntegration: test_settings_singleton_importable(0),test_engine_uses_settings(0)  # BackendSettings singleton is importable and functional.
  backend/tests/test_logging.py:
    e: TestJSONFormatter,TestRequestIDMiddleware,TestSetupLogging
    TestJSONFormatter: test_format_produces_json(0),test_format_includes_exception(0),test_format_service_name(0)  # JSONFormatter emits valid JSON with expected fields.
    TestRequestIDMiddleware: test_app(0),test_response_has_request_id_header(1),test_client_request_id_is_forwarded(1),test_new_id_generated_without_header(1)  # RequestIDMiddleware adds X-Request-ID to responses.
    TestSetupLogging: test_setup_logging_installs_json_handler(0),test_setup_logging_respects_log_level(0)  # setup_logging() installs JSONFormatter on root logger.
  backend/tests/test_persistence.py:
    e: TestMemoryRepoCRUD,TestMemoryRepoListOrdering,TestMemoryRepoEviction,TestSerializationRoundtrip,TestWorkflowRepoFactory
    TestMemoryRepoCRUD: repo(0),test_save_and_get(1),test_get_nonexistent(1),test_update_status(1),test_update_nonexistent(1),test_count_empty(1),test_count_after_saves(1)  # Basic CRUD on MemoryWorkflowRepo.
    TestMemoryRepoListOrdering: populated_repo(0),test_list_default(1),test_list_with_limit(1),test_list_with_offset(1)  # list_runs returns items in reverse insertion order (newest f
    TestMemoryRepoEviction: test_eviction_oldest(0)  # MemoryWorkflowRepo enforces max_size.
    TestSerializationRoundtrip: test_steps_json_roundtrip(0)  # Data saved to repo preserves all fields through roundtrip.
    TestWorkflowRepoFactory: test_factory_returns_memory_without_postgres(1),test_factory_returns_postgres_with_url(1)  # create_workflow_repo() factory behavior.
  backend/tests/test_workflow_api.py:
    e: _mock_worker_response,TestHealthEndpoint,TestWorkflowActions,TestRunWorkflow,TestWorkflowHistory,TestFromText
    TestHealthEndpoint: test_health_endpoint(1)  # Backend health check.
    TestWorkflowActions: test_workflow_actions(1),test_workflow_actions_contains_invoice(1)  # GET /workflow/actions endpoint.
    TestRunWorkflow: test_run_workflow(1),test_run_workflow_step_failure(1),test_start_workflow(1),test_stream_workflow(1)  # POST /workflow/run endpoint.
    TestWorkflowHistory: test_workflow_history(1)  # GET /workflow/history endpoint.
    TestFromText: test_from_text_complete(1),test_from_text_incomplete(1),test_from_text_empty(1)  # POST /workflow/from-text endpoint.
    _mock_worker_response(status_code;json_data)
  examples/01-invoice/main.py:
    e: main
    main()
  examples/02-email/main.py:
    e: main
    main()
  examples/03-report-and-notify/main.py:
    e: main
    main()
  examples/04-scheduled-report/main.py:
    e: main
    main()
  examples/05-conversation-flow/main.py:
    e: main
    main()
  examples/code_generation_examples.py:
    e: main
    main()
  nlp-service/app/__init__.py:
  nlp-service/app/access/__init__.py:
  nlp-service/app/access/bootstrap.py:
  nlp-service/app/access/config.py:
  nlp-service/app/access/native.py:
  nlp-service/app/access/policy.py:
  nlp-service/app/access/uri_match.py:
  nlp-service/app/audio_parser.py:
    e: stt_audio,stt_file,is_stt_available,StreamingSTT
    StreamingSTT: __init__(1),start(0),send_audio(1),get_transcript(0),stop(0)  # Real-time streaming STT via Deepgram WebSocket.
    stt_audio(audio_bytes;language)
    stt_file(file_path;language)
    is_stt_available()
  nlp-service/app/code_generator.py:
    e: CodeGenerator
    CodeGenerator: __init__(0),_get_api_key(0),_build_prompt(3),generate_code(4),_extract_class_name(1),_split_code_and_tests(2),get_supported_languages(0),get_language_info(1)  # Generates code in multiple programming languages using LLM.
  nlp-service/app/config.py:
    e: NLPServiceSettings
    NLPServiceSettings:
  nlp-service/app/conversation/__init__.py:
  nlp-service/app/conversation/merge.py:
    e: merge_into_state
    merge_into_state(state;nlp)
  nlp-service/app/conversation/orchestrator.py:
    e: start_conversation,continue_conversation,get_conversation,_attach_routing,_process_message
    start_conversation(text)
    continue_conversation(conversation_id;text)
    get_conversation(conversation_id)
    _attach_routing(resp;decision)
    _process_message(state;text)
  nlp-service/app/conversation/responses.py:
    e: deny_message,_is_execute_or_continue,check_execute_keyword,handle_unknown_intent,handle_system_action,build_and_check_dsl,build_incomplete_response,_nlp_from_state,format_system_result,_format_system_status,_format_settings_get,_format_settings_set,_format_settings_reset,_format_file_read,_format_file_write,_format_file_list,_format_registry_list,_format_registry_update
    deny_message(decision)
    _is_execute_or_continue(text)
    check_execute_keyword(state;text)
    handle_unknown_intent(state)
    handle_system_action(state)
    build_and_check_dsl(state)
    build_incomplete_response(state)
    _nlp_from_state(state)
    format_system_result(intent;result)
    _format_system_status(inner)
    _format_settings_get(inner)
    _format_settings_set(inner)
    _format_settings_reset(inner)
    _format_file_read(inner)
    _format_file_write(inner)
    _format_file_list(inner)
    _format_registry_list(inner)
    _format_registry_update(inner)
  nlp-service/app/dsl/__init__.py:
  nlp-service/app/dsl/forms.py:
    e: get_action_form
    get_action_form(action)
  nlp-service/app/dsl/mapper.py:
    e: map_to_dsl,_resolve_actions,_build_config,_get_field_mapping,_make_name,_build_prompt
    map_to_dsl(nlp)
    _resolve_actions(intent)
    _build_config(action;entities)
    _get_field_mapping(action)
    _make_name(intent;actions)
    _build_prompt(missing)
  nlp-service/app/execution/__init__.py:
  nlp-service/app/execution/delegate.py:
    e: is_delegated_to_mullm,execution_backend_for_intent,mullm_action_names,delegate_payload
    is_delegated_to_mullm(intent)
    execution_backend_for_intent(intent)
    mullm_action_names()
    delegate_payload(action;config)
  nlp-service/app/execution/system.py:
    e: _validate_file_path,_is_read_only,execute_system_action,_exec_settings_get,_exec_settings_set,_exec_settings_reset,_exec_file_read,_exec_file_write,_exec_file_list,_exec_registry_list,_exec_registry_add,_exec_registry_edit,_exec_status
    _validate_file_path(file_path)
    _is_read_only(file_path)
    execute_system_action(action;config)
    _exec_settings_get(config)
    _exec_settings_set(config)
    _exec_settings_reset(config)
    _exec_file_read(config)
    _exec_file_write(config)
    _exec_file_list(config)
    _exec_registry_list(config)
    _exec_registry_add(config)
    _exec_registry_edit(config)
    _exec_status(config)
  nlp-service/app/governance/__init__.py:
  nlp-service/app/governance/bootstrap.py:
    e: _actions_from_yaml_areas,apply_yaml_actions,bootstrap_registry
    _actions_from_yaml_areas()
    apply_yaml_actions(registry)
    bootstrap_registry(registry)
  nlp-service/app/governance/config.py:
    e: _search_paths,_load_yaml_file,_merge_dict,load_access_config,_load_merged_config,_build_access_config,_enabled_integrations,_default_agent,_allowed_uri_schemes,get_access_config,reload_access_config,AccessConfig
    AccessConfig: action_to_area(0),area_by_id(1)
    _search_paths()
    _load_yaml_file(path)
    _merge_dict(base;overlay)
    load_access_config()
    _load_merged_config()
    _build_access_config(merged;loaded_path)
    _enabled_integrations(merged)
    _default_agent(settings;access_control)
    _allowed_uri_schemes(access_control)
    get_access_config()
    reload_access_config()
  nlp-service/app/governance/policy.py:
    e: get_agent_id,_grant_matches,_grant_action_matches,_grant_target_matches,_area_selector_match,_uri_selector_match,authorize_action,_action_context,_scheme_decision,_effect_decision,_unknown_agent_decision,_matched_effect,_decision,AccessDecision,_ActionContext
    AccessDecision: to_dict(0)
    _ActionContext:
    get_agent_id(header_agent)
    _grant_matches(grant)
    _grant_action_matches(grant;permission_action)
    _grant_target_matches(grant)
    _area_selector_match(area_key;resource_area)
    _uri_selector_match(uri_pattern;uri)
    authorize_action(agent_id;action_name)
    _action_context(meta)
    _scheme_decision(context)
    _effect_decision(matched_effect;agent_id;action_name;context)
    _unknown_agent_decision(agent_id;action_name)
    _matched_effect(grants)
    _decision(allowed;effect;reason;agent_id;action_name;resource_area;uri)
  nlp-service/app/governance/uri_match.py:
    e: normalize_uri,uri_matches,scheme_allowed
    normalize_uri(uri)
    uri_matches(pattern;uri)
    scheme_allowed(uri;allowed_schemes)
  nlp-service/app/logging_setup.py:
    e: get_request_id,setup_logging,JSONFormatter,RequestIDMiddleware
    JSONFormatter: __init__(1),format(1)  # Emit log records as single-line JSON objects.
    RequestIDMiddleware: __init__(2),dispatch(2)  # Generate or forward X-Request-ID for every HTTP request.
    get_request_id()
    setup_logging(service;level)
  nlp-service/app/main.py:
    e: parse_text,text_to_dsl,access_config,access_check,access_reload,list_actions,health,chat_start,chat_message,chat_state,actions_schema,action_schema,get_settings,get_settings_section,update_settings_section,set_setting,reset_settings,system_execute,generate_code,get_supported_languages,_run_parser,websocket_chat,chat_ui
    parse_text(req)
    text_to_dsl(req)
    access_config()
    access_check(agent_id;action;resource_area;uri;permission_action)
    access_reload()
    list_actions()
    health()
    chat_start(text;audio)
    chat_message(conversation_id;text;audio)
    chat_state(conversation_id)
    actions_schema()
    action_schema(action)
    get_settings()
    get_settings_section(section)
    update_settings_section(section;body)
    set_setting(body)
    reset_settings(body)
    system_execute(body)
    generate_code(body)
    get_supported_languages()
    _run_parser(req)
    websocket_chat(websocket;conversation_id)
    chat_ui()
  nlp-service/app/mapper.py:
  nlp-service/app/orchestrator.py:
  nlp-service/app/parser_llm.py:
  nlp-service/app/parser_rules.py:
  nlp-service/app/parsing/__init__.py:
  nlp-service/app/parsing/facade.py:
  nlp-service/app/registry.py:
    e: get_action_by_alias,get_trigger,get_required_fields,get_defaults
    get_action_by_alias(text)
    get_trigger(text)
    get_required_fields(action)
    get_defaults(action)
  nlp-service/app/routing/__init__.py:
  nlp-service/app/routing/intent.py:
    e: IntentDecision
    IntentDecision: to_dict(0),to_nlp_result(1)  # Wynik `resolve_intent` — spójny kontrakt dla orchestratora i
  nlp-service/app/routing/native.py:
    e: _match_route,_patterns_match,_pattern_matches,_regex_pattern_matches,_keywords_pattern_matches,_substring_pattern_matches,_aliases_match,resolve_native_intent,_resolve_configured_route,_route_decision,_resolve_action_alias,_best_action_alias,_best_alias_for_action
    _match_route(text;route)
    _patterns_match(text_lower;patterns)
    _pattern_matches(text_lower;pattern)
    _regex_pattern_matches(text_lower;pattern)
    _keywords_pattern_matches(text_lower;pattern)
    _substring_pattern_matches(text_lower;pattern)
    _aliases_match(text_lower;aliases)
    resolve_native_intent(text)
    _resolve_configured_route(text;routes;action_areas)
    _route_decision(action;route;action_areas)
    _resolve_action_alias(text;registry)
    _best_action_alias(text_lower;registry)
    _best_alias_for_action(text_lower;action_name;meta;current)
  nlp-service/app/routing/observability.py:
    e: record_intent_decision,routing_metrics_snapshot,reset_routing_metrics
    record_intent_decision(decision)
    routing_metrics_snapshot()
    reset_routing_metrics()
  nlp-service/app/routing/parser/__init__.py:
  nlp-service/app/routing/parser/facade.py:
    e: parse_text
    parse_text(text;mode)
  nlp-service/app/routing/parser/llm.py:
    e: parse_llm,_detect_provider,_parse_json_response
    parse_llm(text)
    _detect_provider()
    _parse_json_response(raw)
  nlp-service/app/routing/parser/rules.py:
    e: parse_rules,_detect_actions,_action_alias_scores,_longest_alias_match,_actions_by_score,_dominant_overlap_action,_action_category,_top_system_action_wins,_second_system_action_wins,_resolve_intent,_extract_entities,_extract_amount,_extract_email,_extract_report_type,_extract_format,_extract_notification_channels,_extract_param_aliases,_extract_system_entities,_extract_file_path_entity,_extract_setting_path_entity,_extract_model_setting_entity,_extract_numeric_setting_value,_extract_mode_setting_entity,_extract_fallback_recipient,_set_entity
    parse_rules(text)
    _detect_actions(text_lower)
    _action_alias_scores(text_lower)
    _longest_alias_match(text_lower;aliases)
    _actions_by_score(scores)
    _dominant_overlap_action(sorted_actions;scores)
    _action_category(action_name)
    _top_system_action_wins(top_category;second_category;top_score;second_score)
    _second_system_action_wins(top_category;second_category;top_score;second_score)
    _resolve_intent(actions)
    _extract_entities(text;text_lower)
    _extract_amount(entities;text)
    _extract_email(entities;text)
    _extract_report_type(entities;text_lower)
    _extract_format(entities;text_lower)
    _extract_notification_channels(entities;text)
    _extract_param_aliases(entities;text_lower)
    _extract_system_entities(entities;text;text_lower)
    _extract_file_path_entity(entities;text)
    _extract_setting_path_entity(entities;text)
    _extract_model_setting_entity(entities;text_lower)
    _extract_numeric_setting_value(entities;text_lower)
    _extract_mode_setting_entity(entities;text_lower)
    _extract_fallback_recipient(entities;text_lower)
    _set_entity(entities;field;value)
  nlp-service/app/routing/resolve.py:
    e: _parser_source,_intent_from_native,_intent_from_nlp,_apply_auth,resolve_intent
    _parser_source(text)
    _intent_from_native(native)
    _intent_from_nlp(nlp;source)
    _apply_auth(decision;auth)
    resolve_intent(text)
  nlp-service/app/schemas.py:
    e: NLPIntent,NLPEntities,NLPResult,DSLStep,WorkflowDSL,DialogResponse,NLPRequest,ConversationState,FieldSchema,ActionFormSchema,ConversationResponse
    NLPIntent:
    NLPEntities:
    NLPResult:
    DSLStep:
    WorkflowDSL:
    DialogResponse:
    NLPRequest:
    ConversationState:  # Stan rozmowy — akumuluje dane między turami dialogu.
    FieldSchema:
    ActionFormSchema:
    ConversationResponse:
  nlp-service/app/settings.py:
    e: _coerce_type,LLMSettings,NLPSettings,WorkerSettings,FileAccessSettings,SystemSettings,SettingsManager
    LLMSettings:
    NLPSettings:
    WorkerSettings:
    FileAccessSettings:
    SystemSettings:  # Pełny model ustawień systemu.
    SettingsManager: __new__(1),settings(0),get(1),get_section(1),get_all(0),set(2),update_section(2),reset(1),_load(0),_save(0),describe(0)  # Runtime settings z persystencją do JSON.
    _coerce_type(value;target_type)
  nlp-service/app/store/__init__.py:
    e: ConversationStore
    ConversationStore: get(1),save(2),delete(1),count(0)  # Abstrakcja persystencji stanu konwersacji.
  nlp-service/app/store/factory.py:
    e: get_conversation_store
    get_conversation_store()
  nlp-service/app/store/memory.py:
    e: MemoryConversationStore
    MemoryConversationStore: __init__(0),get(1),save(2),delete(1),count(0)
  nlp-service/app/store/redis_store.py:
    e: RedisConversationStore
    RedisConversationStore: __init__(2),_key(1),get(1),save(2),delete(1),count(0),close(0)
  nlp-service/app/system_executor.py:
  nlp-service/integrations/__init__.py:
  nlp-service/integrations/loader.py:
    e: _integration_names,load_integration_registries,apply_integrations
    _integration_names()
    load_integration_registries()
    apply_integrations(registry)
  nlp-service/integrations/mullm/__init__.py:
  nlp-service/integrations/mullm/registry.py:
  nlp-service/tests/__init__.py:
  nlp-service/tests/conftest.py:
    e: sample_texts,expected_intents,sample_entities,mock_conversation_store
    sample_texts()
    expected_intents()
    sample_entities()
    mock_conversation_store()
  nlp-service/tests/test_access.py:
    e: _point_config,test_config_loads_areas,test_uri_match_mullm,test_files_agent_can_list,test_mail_agent_denied_mullm_execute,test_native_lista_plikow,test_registry_has_yaml_action
    _point_config(monkeypatch)
    test_config_loads_areas()
    test_uri_match_mullm()
    test_files_agent_can_list()
    test_mail_agent_denied_mullm_execute()
    test_native_lista_plikow()
    test_registry_has_yaml_action()
  nlp-service/tests/test_execution_delegate.py:
    e: test_mullm_shell_delegated,test_invoice_worker_backend,test_delegate_payload_shape
    test_mullm_shell_delegated()
    test_invoice_worker_backend()
    test_delegate_payload_shape()
  nlp-service/tests/test_mapper.py:
    e: TestMapCompleteDSL,TestMapIncomplete,TestMapComposite,TestMapUnknown,TestMapDefaults,TestMapTrigger,TestMapSystemAction,TestMapAllBusinessActions,TestResolveActions
    TestMapCompleteDSL: test_map_complete_invoice(0),test_map_complete_email(0)  # Cases where all required fields are present → complete DSL.
    TestMapIncomplete: test_map_incomplete_invoice(0)  # Cases where required fields are missing → DialogResponse wit
    TestMapComposite: test_map_composite_report_email(0)  # Composite intent mapping (multi-step workflows).
    TestMapUnknown: test_map_unknown_intent(0),test_map_nonexistent_intent(0)  # Unknown intent → error response.
    TestMapDefaults: test_map_with_defaults(0)  # Optional fields receive default values from registry.
    TestMapTrigger: test_map_trigger_propagation(0)  # Trigger extracted from raw_text propagates to DSL.
    TestMapSystemAction: test_map_system_action_settings(0)  # System intents should not map to DSL (no steps for system ac
    TestMapAllBusinessActions: test_map_all_business_actions(1)  # Ensure mapper handles all registered business actions.
    TestResolveActions: test_resolve_direct_action(0),test_resolve_composite_intent(0),test_resolve_dynamic_composite(0),test_resolve_unknown(0)  # _resolve_actions helper tests.
  nlp-service/tests/test_orchestrator.py:
    e: _patch_store,TestStartConversation,TestContinueConversation,TestSystemCommands,TestGetConversation,TestGetActionForm,TestMergeIntoState
    TestStartConversation: test_start_conversation_complete(0),test_start_conversation_incomplete(0),test_start_conversation_unknown(0)  # Starting a new conversation from initial user text.
    TestContinueConversation: test_continue_conversation(0),test_continue_conversation_lazy_create(0)  # Multi-turn dialog: providing missing data in follow-up messa
    TestSystemCommands: test_system_command_status(0),test_system_command_settings(0),test_format_system_file_list(0),test_format_system_failed_result(0)  # System actions executed directly (no DSL generation).
    TestGetConversation: test_get_conversation_exists(0),test_get_conversation_not_found(0)  # Retrieving stored conversation state.
    TestGetActionForm: test_action_form_send_invoice(0),test_action_form_nonexistent(0)  # Schema-driven UI form generation.
    TestMergeIntoState: test_merge_updates_intent(0),test_merge_preserves_existing(0)  # Internal entity merging logic.
    _patch_store(monkeypatch)
  nlp-service/tests/test_parser_rules.py:
    e: TestParseInvoice,TestParseEmail,TestParseReport,TestParseComposite,TestParseSystem,TestParseUnknown,TestAmountExtraction,TestTriggerDetection,TestResultStructure
    TestParseInvoice: test_parse_invoice_simple(0),test_parse_invoice_missing_data(0),test_parse_invoice_eur(0),test_parse_invoice_usd(0)  # Invoice intent detection and entity extraction.
    TestParseEmail: test_parse_email(0),test_parse_email_english(0)  # Email intent detection.
    TestParseReport: test_parse_report_weekly(0),test_parse_report_finance_csv(0)  # Report intent and entity extraction.
    TestParseComposite: test_parse_composite_invoice_notify(0),test_parse_composite_full_flow(0)  # Multi-action (composite) intent detection.
    TestParseSystem: test_parse_system_settings(0),test_parse_system_file_list(0),test_parse_system_status(0),test_parse_system_help(0),test_parse_system_set_model(0),test_parse_system_set_mode(0)  # System intent detection (settings, files, status).
    TestParseUnknown: test_parse_unknown(0)  # Unknown input handling.
    TestAmountExtraction: test_parse_amount_extraction(3)  # Currency and amount parsing across formats.
    TestTriggerDetection: test_parse_trigger_detection(2)  # Schedule trigger extraction from text.
    TestResultStructure: test_result_is_nlp_result(0),test_raw_text_preserved(0)  # NLPResult output structure validation.
  nlp-service/tests/test_registry.py:
    e: TestRegistryStructure,TestAliasResolution,TestTriggerDetection,TestHelperFunctions,TestCategories,TestCompositeIntents
    TestRegistryStructure: test_registry_entry_has_required_keys(1)  # Validate registry entries have required keys.
    TestAliasResolution: test_alias_invoice_pl(0),test_alias_email_en(0),test_alias_report(0),test_alias_slack(0),test_alias_unknown(0),test_alias_best_match(0)  # get_action_by_alias finds best match.
    TestTriggerDetection: test_trigger_daily(0),test_trigger_weekly(0),test_trigger_monthly(0),test_trigger_manual_default(0)  # get_trigger extracts schedule from text.
    TestHelperFunctions: test_get_required_fields_invoice(0),test_get_required_fields_unknown(0),test_get_defaults_invoice(0),test_get_defaults_unknown(0)  # get_required_fields, get_defaults.
    TestCategories: test_system_actions_nonempty(0),test_business_actions_nonempty(0),test_no_overlap(0),test_union_is_complete(0),test_mullm_actions_loaded(0)  # System vs business action sets.
    TestCompositeIntents: test_composite_actions_exist(1)  # COMPOSITE_INTENTS structure validation.
  nlp-service/tests/test_routing_observability.py:
    e: _reset_metrics,test_record_increments_rules_hit,test_resolve_intent_updates_metrics
    _reset_metrics()
    test_record_increments_rules_hit()
    test_resolve_intent_updates_metrics()
  nlp-service/tests/test_routing_resolve.py:
    e: TestParserSource,TestResolveIntent,TestOrchestratorRoutingField
    TestParserSource: test_rules_mode(1)
    TestResolveIntent: test_invoice_rules_path(0),test_unknown_intent(0),test_native_file_list_route(0),test_decision_serializable(0)
    TestOrchestratorRoutingField: test_start_conversation_includes_routing(1)
  nlp-service/tests/test_store.py:
    e: TestMemoryStoreCRUD,TestSerializationRoundtrip,TestStoreFactory,TestStoreIsolation
    TestMemoryStoreCRUD: store(0),test_save_and_get(1),test_get_nonexistent(1),test_save_overwrites(1),test_delete(1),test_delete_nonexistent(1),test_count_empty(1),test_count_after_saves(1),test_count_after_delete(1)  # Basic CRUD operations on MemoryConversationStore.
    TestSerializationRoundtrip: store(0),test_conversation_state_roundtrip(1),test_complex_entities_roundtrip(1)  # Store must preserve data through save→get cycle.
    TestStoreFactory: test_factory_returns_memory_without_redis(1),test_factory_singleton(1),test_factory_falls_back_on_bad_redis(1)  # get_conversation_store() factory behavior.
    TestStoreIsolation: test_separate_instances_isolated(0)  # Multiple store instances are isolated.
  nlp-service/tests/test_system_executor.py:
    e: _reset_settings,TestSettingsGet,TestSettingsSet,TestSettingsReset,TestFileList,TestRegistryList,TestRegistryAdd,TestStatus,TestRegistryEdit,TestFileRead,TestFileWrite,TestExecuteSystemAction,TestFilePathValidation,TestExecutorMapping
    TestSettingsGet: test_settings_get_all(0),test_settings_get_section(0),test_settings_get_default_is_all(0)  # _exec_settings_get handler.
    TestSettingsSet: test_settings_set_and_verify(0),test_settings_set_missing_path(0),test_settings_set_missing_value(0)  # _exec_settings_set handler.
    TestSettingsReset: test_settings_reset(0),test_settings_reset_section(0)  # _exec_settings_reset handler.
    TestFileList: test_file_list(2),test_file_list_nonexistent(0)  # _exec_file_list handler.
    TestRegistryList: test_registry_list(0),test_registry_list_business(0),test_registry_list_system(0)  # _exec_registry_list handler.
    TestRegistryAdd: test_registry_add(0),test_registry_add_missing_name(0),test_registry_add_duplicate(0)  # _exec_registry_add handler.
    TestStatus: test_status(0)  # _exec_status handler.
    TestRegistryEdit: test_registry_edit_description(0),test_registry_edit_nonexistent(0)  # _exec_registry_edit handler.
    TestFileRead: test_file_read_existing(2),test_file_read_nonexistent(2),test_file_read_no_path(0)  # _exec_file_read handler.
    TestFileWrite: test_file_write_new(2),test_file_write_append(2)  # _exec_file_write handler.
    TestExecuteSystemAction: test_execute_known_action(0),test_execute_unknown_action(0)  # Async dispatch function.
    TestFilePathValidation: test_validate_allowed_path(2),test_validate_disallowed_path(0),test_is_read_only(2)  # _validate_file_path and _is_read_only.
    TestExecutorMapping: test_all_system_actions_have_executor(0),test_executors_count(0)  # SYSTEM_EXECUTORS dict is complete.
    _reset_settings(monkeypatch)
  nlp2dsl_sdk/__init__.py:
  nlp2dsl_sdk/__main__.py:
    e: main
    main()
  nlp2dsl_sdk/client.py:
    e: workflow_step,NLP2DSLClient,ConversationFlow
    NLP2DSLClient: __init__(5),from_env(2),close(0),__enter__(0),__exit__(3),_request(3),_backend(2),_nlp_service(2),_worker(2),backend_health(0),nlp_service_health(0),worker_health(0),health(0),workflow_from_text(3),run_workflow(4),workflow_actions(0),workflow_action_schema(1),settings(0),settings_section(1),update_settings_section(2),set_setting(2),reset_settings(1),chat_start(2),chat_message(3),chat_state(1),nlp_chat_start(2),nlp_chat_message(3),nlp_chat_state(1),generate_code(4),supported_languages(0),worker_execute(3),worker_generate_code(5),send_invoice(5),send_email(5),generate_report(4),generate_report_and_notify(7),create_scheduled_report(7),notify_slack(4),crm_update(4),send_invoice_and_notify(7)  # Small reusable SDK for the NLP2DSL services.
    ConversationFlow: __init__(1),start(2),send_message(2),_handle_response(1),_handle_in_progress_response(2),_handle_ready_response(2),_handle_completed_response(2),_handle_error_response(1),run_demo(0),run_interactive(0)  # Convenience helper for the conversational workflow example.
    workflow_step(action)
  nlp2dsl_sdk/demos.py:
    e: _ensure_services,_print_json,_print_workflow_preview,_print_execution_result,_print_code_generation_preview,_preview_text_examples,run_crm_update_demo,run_action_catalog_demo,run_automation_gallery_demo,_run_workflow_examples,_run_gallery_examples,run_invoice_demo,run_email_demo,run_report_and_notify_demo,run_scheduled_report_demo,run_code_generation_demo,_run_direct_code_generation,_get_supported_languages,_run_workflow_code_examples,_run_conversation_code_example,_run_worker_code_generation,list_available_demos,DemoSpec
    DemoSpec:  # Metadata for a runnable demo exposed by the package CLI.
    _ensure_services(client)
    _print_json(payload)
    _print_workflow_preview(result)
    _print_execution_result(result)
    _print_code_generation_preview(result)
    _preview_text_examples(client;title;examples)
    run_crm_update_demo(client)
    run_action_catalog_demo(client)
    run_automation_gallery_demo(client)
    _run_workflow_examples(client;title;examples)
    _run_gallery_examples(client;title;examples)
    run_invoice_demo(client)
    run_email_demo(client)
    run_report_and_notify_demo(client)
    run_scheduled_report_demo(client)
    run_code_generation_demo(client)
    _run_direct_code_generation(client)
    _get_supported_languages(client)
    _run_workflow_code_examples(client)
    _run_conversation_code_example(client)
    _run_worker_code_generation(client)
    list_available_demos()
  test_code_generation.py:
    e: test_code_generation
    test_code_generation()
  tests/conftest.py:
  tests/e2e/__init__.py:
  tests/e2e/conftest.py:
    e: _resolve_browser_executable,nlp_client,backend_client,browser_instance,browser_context,page,chat_page
    _resolve_browser_executable()
    nlp_client()
    backend_client()
    browser_instance()
    browser_context(browser_instance)
    page(browser_context)
    chat_page(page)
  tests/e2e/test_backend.py:
    e: test_health,test_workflow_actions_list,test_workflow_actions_contains_send_invoice,test_from_text_dsl_only_no_execute,test_from_text_empty_returns_400,test_from_text_unknown_intent_propagates_error,test_workflow_history_returns_list,test_workflow_history_unknown_id_returns_404,test_chat_start_proxied_to_nlp,test_chat_start_empty_returns_error,test_chat_message_proxied_to_nlp,test_workflow_actions_schema,test_workflow_settings_proxied
    test_health(backend_client)
    test_workflow_actions_list(backend_client)
    test_workflow_actions_contains_send_invoice(backend_client)
    test_from_text_dsl_only_no_execute(backend_client)
    test_from_text_empty_returns_400(backend_client)
    test_from_text_unknown_intent_propagates_error(backend_client)
    test_workflow_history_returns_list(backend_client)
    test_workflow_history_unknown_id_returns_404(backend_client)
    test_chat_start_proxied_to_nlp(backend_client)
    test_chat_start_empty_returns_error(backend_client)
    test_chat_message_proxied_to_nlp(backend_client)
    test_workflow_actions_schema(backend_client)
    test_workflow_settings_proxied(backend_client)
  tests/e2e/test_chat_ui.py:
    e: test_page_title,test_page_has_no_js_errors,test_web_app_manifest,test_tts_button_present,test_tts_button_default_state_active,test_tts_toggle_disables,test_tts_toggle_re_enables,test_speak_function_defined,test_speech_synthesis_available,test_speak_calls_speech_synthesis,test_speak_respects_tts_disabled,test_microphone_get_user_media,test_media_recorder_supported,test_voice_button_present,test_voice_button_initial_text,wait_for_voice_recording,test_voice_transcription_autostarts_on_load,test_voice_button_click_stops_recording,test_text_input_present,test_send_button_present,test_text_message_renders_user_bubble,test_text_message_gets_assistant_response,test_speak_called_on_assistant_response,test_text_input_cleared_after_send,test_status_element_present,test_websocket_connects_on_load
    test_page_title(chat_page)
    test_page_has_no_js_errors(page)
    test_web_app_manifest(chat_page)
    test_tts_button_present(chat_page)
    test_tts_button_default_state_active(chat_page)
    test_tts_toggle_disables(chat_page)
    test_tts_toggle_re_enables(chat_page)
    test_speak_function_defined(chat_page)
    test_speech_synthesis_available(chat_page)
    test_speak_calls_speech_synthesis(chat_page)
    test_speak_respects_tts_disabled(chat_page)
    test_microphone_get_user_media(chat_page)
    test_media_recorder_supported(chat_page)
    test_voice_button_present(chat_page)
    test_voice_button_initial_text(chat_page)
    wait_for_voice_recording(chat_page;timeout_s)
    test_voice_transcription_autostarts_on_load(chat_page)
    test_voice_button_click_stops_recording(chat_page)
    test_text_input_present(chat_page)
    test_send_button_present(chat_page)
    test_text_message_renders_user_bubble(chat_page)
    test_text_message_gets_assistant_response(chat_page)
    test_speak_called_on_assistant_response(chat_page)
    test_text_input_cleared_after_send(chat_page)
    test_status_element_present(chat_page)
    test_websocket_connects_on_load(chat_page)
  tests/e2e/test_nlp_service.py:
    e: test_health,test_nlp_actions_registry,test_parse_known_intent_rules,test_parse_unknown_intent_rules,test_parse_send_email_intent,test_to_dsl_complete_invoice,test_to_dsl_unknown_returns_422,test_chat_start_text,test_chat_start_empty_text_returns_400,test_chat_message_continue_conversation,test_chat_state_get,test_chat_state_not_found,test_actions_schema_all,test_action_schema_by_name,test_action_schema_unknown_returns_404,test_settings_get_all,test_settings_get_llm_section,test_settings_unknown_section_returns_404,test_chat_ui_serves_html
    test_health(nlp_client)
    test_nlp_actions_registry(nlp_client)
    test_parse_known_intent_rules(nlp_client)
    test_parse_unknown_intent_rules(nlp_client)
    test_parse_send_email_intent(nlp_client)
    test_to_dsl_complete_invoice(nlp_client)
    test_to_dsl_unknown_returns_422(nlp_client)
    test_chat_start_text(nlp_client)
    test_chat_start_empty_text_returns_400(nlp_client)
    test_chat_message_continue_conversation(nlp_client)
    test_chat_state_get(nlp_client)
    test_chat_state_not_found(nlp_client)
    test_actions_schema_all(nlp_client)
    test_action_schema_by_name(nlp_client)
    test_action_schema_unknown_returns_404(nlp_client)
    test_settings_get_all(nlp_client)
    test_settings_get_llm_section(nlp_client)
    test_settings_unknown_section_returns_404(nlp_client)
    test_chat_ui_serves_html(nlp_client)
  tests/e2e/test_websocket.py:
    e: _uri,_is_open,_is_closed,test_websocket_connects_and_accepts,test_websocket_unique_conversation_id,test_websocket_accepts_binary_audio,test_websocket_accepts_multiple_chunks,test_websocket_clean_disconnect,test_websocket_server_survives_abrupt_close,test_websocket_concurrent_connections
    _uri(conv_id)
    _is_open(ws)
    _is_closed(ws)
    test_websocket_connects_and_accepts()
    test_websocket_unique_conversation_id()
    test_websocket_accepts_binary_audio()
    test_websocket_accepts_multiple_chunks()
    test_websocket_clean_disconnect()
    test_websocket_server_survives_abrupt_close()
    test_websocket_concurrent_connections()
  tests/test_nlp2dsl_sdk.py:
    e: client_factory,test_from_env_prefers_repo_env_names,test_workflow_and_conversation_endpoints,test_report_helpers_use_report_type_and_schedule,test_new_workflow_helpers_are_data_driven,test_code_generation_methods_hit_expected_services,test_health_queries_all_services,DummyResponse,DummySession
    DummyResponse: __init__(2),raise_for_status(0),json(0)
    DummySession: __init__(1),request(2),close(0)
    client_factory()
    test_from_env_prefers_repo_env_names(monkeypatch)
    test_workflow_and_conversation_endpoints(client_factory)
    test_report_helpers_use_report_type_and_schedule(client_factory)
    test_new_workflow_helpers_are_data_driven(client_factory)
    test_code_generation_methods_hit_expected_services(client_factory)
    test_health_queries_all_services(client_factory)
  tests/test_placeholder.py:
    e: test_placeholder,test_import
    test_placeholder()
    test_import()
  tests/test_tests.py:
    e: test_placeholder,test_import
    test_placeholder()
    test_import()
  worker/__init__.py:
  worker/config.py:
    e: WorkerSettings
    WorkerSettings:
  worker/logging_setup.py:
    e: get_request_id,setup_logging,JSONFormatter,RequestIDMiddleware
    JSONFormatter: __init__(1),format(1)  # Emit log records as single-line JSON objects.
    RequestIDMiddleware: __init__(2),dispatch(2)  # Generate or forward X-Request-ID for every HTTP request.
    get_request_id()
    setup_logging(service;level)
  worker/tests/__init__.py:
  worker/tests/conftest.py:
    e: _noop_sleep,mock_asyncio_sleep,client
    _noop_sleep()
    mock_asyncio_sleep()
    client()
  worker/tests/test_worker.py:
    e: client,TestWorkerHealth,TestExecuteActions,TestActionRegistry
    TestWorkerHealth: test_health(1)  # Worker health endpoint.
    TestExecuteActions: test_execute_send_invoice(1),test_execute_send_email(1),test_execute_generate_report(1),test_execute_notify_slack(1),test_execute_notify_telegram(1),test_execute_notify_teams(1),test_execute_unknown_action(1)  # POST /execute — action execution.
    TestActionRegistry: test_handlers_registered(0),test_all_handlers_callable(0)  # ACTION_HANDLERS dict validation.
    client()
  worker/worker.py:
    e: action,_deliver_notification,handle_send_invoice,handle_send_email,handle_generate_report,handle_crm_update,handle_notify_slack,handle_notify_telegram,handle_notify_teams,handle_generate_code,execute_step,health
    action(name)
    _deliver_notification(provider;config;payload;env_var)
    handle_send_invoice(config)
    handle_send_email(config)
    handle_generate_report(config)
    handle_crm_update(config)
    handle_notify_slack(config)
    handle_notify_telegram(config)
    handle_notify_teams(config)
    handle_generate_code(config)
    execute_step(step)
    health()
```

### `project/logic.pl`

```prolog markpact:analysis path=project/logic.pl
% ── Project Metadata ─────────────────────────────────────
project_metadata('nlp2dsl', '0.0.14', 'python').

% ── Project Files ────────────────────────────────────────
project_file('.pfix-test-wrapper.sh', 16, 'shell').
project_file('app.doql.less', 125, 'less').
project_file('backend/app/__init__.py', 1, 'python').
project_file('backend/app/config.py', 43, 'python').
project_file('backend/app/db/__init__.py', 50, 'python').
project_file('backend/app/db/memory.py', 38, 'python').
project_file('backend/app/db/postgres.py', 173, 'python').
project_file('backend/app/engine.py', 270, 'python').
project_file('backend/app/logging_setup.py', 101, 'python').
project_file('backend/app/main.py', 49, 'python').
project_file('backend/app/routers/__init__.py', 1, 'python').
project_file('backend/app/routers/chat.py', 125, 'python').
project_file('backend/app/routers/settings.py', 82, 'python').
project_file('backend/app/routers/system.py', 30, 'python').
project_file('backend/app/routers/workflow.py', 190, 'python').
project_file('backend/app/schemas.py', 65, 'python').
project_file('backend/app/workflow.py', 23, 'python').
project_file('backend/app/workflow_events.py', 92, 'python').
project_file('backend/tests/__init__.py', 1, 'python').
project_file('backend/tests/conftest.py', 32, 'python').
project_file('backend/tests/test_config.py', 83, 'python').
project_file('backend/tests/test_logging.py', 124, 'python').
project_file('backend/tests/test_persistence.py', 185, 'python').
project_file('backend/tests/test_workflow_api.py', 267, 'python').
project_file('examples/01-invoice/main.py', 24, 'python').
project_file('examples/01-invoice/run.sh', 7, 'shell').
project_file('examples/02-email/main.py', 24, 'python').
project_file('examples/02-email/run.sh', 7, 'shell').
project_file('examples/03-report-and-notify/main.py', 24, 'python').
project_file('examples/03-report-and-notify/run.sh', 7, 'shell').
project_file('examples/04-scheduled-report/main.py', 24, 'python').
project_file('examples/04-scheduled-report/run.sh', 7, 'shell').
project_file('examples/05-conversation-flow/main.py', 39, 'python').
project_file('examples/05-conversation-flow/run.sh', 7, 'shell').
project_file('examples/basic/invoice/run.sh', 1, 'shell').
project_file('examples/code_generation_examples.py', 26, 'python').
project_file('metrun-profile.sh', 49, 'shell').
project_file('nlp-service/app/__init__.py', 1, 'python').
project_file('nlp-service/app/access/__init__.py', 16, 'python').
project_file('nlp-service/app/access/bootstrap.py', 4, 'python').
project_file('nlp-service/app/access/config.py', 4, 'python').
project_file('nlp-service/app/access/native.py', 4, 'python').
project_file('nlp-service/app/access/policy.py', 4, 'python').
project_file('nlp-service/app/access/uri_match.py', 4, 'python').
project_file('nlp-service/app/audio_parser.py', 149, 'python').
project_file('nlp-service/app/code_generator.py', 280, 'python').
project_file('nlp-service/app/config.py', 61, 'python').
project_file('nlp-service/app/conversation/__init__.py', 14, 'python').
project_file('nlp-service/app/conversation/merge.py', 26, 'python').
project_file('nlp-service/app/conversation/orchestrator.py', 108, 'python').
project_file('nlp-service/app/conversation/responses.py', 273, 'python').
project_file('nlp-service/app/dsl/__init__.py', 5, 'python').
project_file('nlp-service/app/dsl/forms.py', 84, 'python').
project_file('nlp-service/app/dsl/mapper.py', 190, 'python').
project_file('nlp-service/app/execution/__init__.py', 15, 'python').
project_file('nlp-service/app/execution/delegate.py', 30, 'python').
project_file('nlp-service/app/execution/system.py', 343, 'python').
project_file('nlp-service/app/governance/__init__.py', 15, 'python').
project_file('nlp-service/app/governance/bootstrap.py', 79, 'python').
project_file('nlp-service/app/governance/config.py', 166, 'python').
project_file('nlp-service/app/governance/policy.py', 303, 'python').
project_file('nlp-service/app/governance/uri_match.py', 43, 'python').
project_file('nlp-service/app/logging_setup.py', 101, 'python').
project_file('nlp-service/app/main.py', 584, 'python').
project_file('nlp-service/app/mapper.py', 6, 'python').
project_file('nlp-service/app/orchestrator.py', 22, 'python').
project_file('nlp-service/app/parser_llm.py', 6, 'python').
project_file('nlp-service/app/parser_rules.py', 6, 'python').
project_file('nlp-service/app/parsing/__init__.py', 4, 'python').
project_file('nlp-service/app/parsing/facade.py', 6, 'python').
project_file('nlp-service/app/registry.py', 391, 'python').
project_file('nlp-service/app/routing/__init__.py', 15, 'python').
project_file('nlp-service/app/routing/intent.py', 54, 'python').
project_file('nlp-service/app/routing/native.py', 144, 'python').
project_file('nlp-service/app/routing/observability.py', 58, 'python').
project_file('nlp-service/app/routing/parser/__init__.py', 4, 'python').
project_file('nlp-service/app/routing/parser/facade.py', 40, 'python').
project_file('nlp-service/app/routing/parser/llm.py', 188, 'python').
project_file('nlp-service/app/routing/parser/rules.py', 382, 'python').
project_file('nlp-service/app/routing/resolve.py', 149, 'python').
project_file('nlp-service/app/schemas.py', 132, 'python').
project_file('nlp-service/app/settings.py', 252, 'python').
project_file('nlp-service/app/store/__init__.py', 31, 'python').
project_file('nlp-service/app/store/factory.py', 47, 'python').
project_file('nlp-service/app/store/memory.py', 24, 'python').
project_file('nlp-service/app/store/redis_store.py', 59, 'python').
project_file('nlp-service/app/system_executor.py', 36, 'python').
project_file('nlp-service/integrations/__init__.py', 6, 'python').
project_file('nlp-service/integrations/loader.py', 63, 'python').
project_file('nlp-service/integrations/mullm/__init__.py', 2, 'python').
project_file('nlp-service/integrations/mullm/registry.py', 67, 'python').
project_file('nlp-service/tests/__init__.py', 1, 'python').
project_file('nlp-service/tests/conftest.py', 102, 'python').
project_file('nlp-service/tests/test_access.py', 75, 'python').
project_file('nlp-service/tests/test_execution_delegate.py', 25, 'python').
project_file('nlp-service/tests/test_mapper.py', 252, 'python').
project_file('nlp-service/tests/test_orchestrator.py', 222, 'python').
project_file('nlp-service/tests/test_parser_rules.py', 237, 'python').
project_file('nlp-service/tests/test_registry.py', 169, 'python').
project_file('nlp-service/tests/test_routing_observability.py', 42, 'python').
project_file('nlp-service/tests/test_routing_resolve.py', 66, 'python').
project_file('nlp-service/tests/test_store.py', 193, 'python').
project_file('nlp-service/tests/test_system_executor.py', 422, 'python').
project_file('nlp2dsl_sdk/__init__.py', 34, 'python').
project_file('nlp2dsl_sdk/__main__.py', 42, 'python').
project_file('nlp2dsl_sdk/client.py', 581, 'python').
project_file('nlp2dsl_sdk/demos.py', 688, 'python').
project_file('project.sh', 59, 'shell').
project_file('run-all-tests.sh', 45, 'shell').
project_file('tauri-wrapper/desktop.sh', 80, 'shell').
project_file('tauri-wrapper/scripts/dev.js', 57, 'javascript').
project_file('tauri-wrapper/scripts/serve-dist.js', 140, 'javascript').
project_file('tauri-wrapper/src-tauri/build.rs', 4, 'rust').
project_file('tauri-wrapper/src-tauri/src/main.rs', 8, 'rust').
project_file('tauri-wrapper/test/mvp-voice-chat-wrapper.test.js', 9, 'javascript').
project_file('test_code_generation.py', 140, 'python').
project_file('tests/conftest.py', 11, 'python').
project_file('tests/e2e/__init__.py', 1, 'python').
project_file('tests/e2e/conftest.py', 129, 'python').
project_file('tests/e2e/test_backend.py', 152, 'python').
project_file('tests/e2e/test_chat_ui.py', 263, 'python').
project_file('tests/e2e/test_nlp_service.py', 216, 'python').
project_file('tests/e2e/test_websocket.py', 112, 'python').
project_file('tests/run.sh', 86, 'shell').
project_file('tests/test_nlp2dsl_sdk.py', 259, 'python').
project_file('tests/test_placeholder.py', 12, 'python').
project_file('tests/test_tests.py', 12, 'python').
project_file('tree.sh', 2, 'shell').
project_file('worker/__init__.py', 6, 'python').
project_file('worker/config.py', 28, 'python').
project_file('worker/logging_setup.py', 101, 'python').
project_file('worker/tests/__init__.py', 1, 'python').
project_file('worker/tests/conftest.py', 46, 'python').
project_file('worker/tests/test_worker.py', 173, 'python').
project_file('worker/worker.py', 231, 'python').

% ── Python Functions ─────────────────────────────────────
python_function('backend/app/db/__init__.py', 'create_workflow_repo', 0, 2, 3).
python_function('backend/app/engine.py', '_workflow_steps_payload', 1, 2, 1).
python_function('backend/app/engine.py', '_persist_workflow_snapshot', 2, 2, 2).
python_function('backend/app/engine.py', '_publish_workflow_event', 4, 2, 2).
python_function('backend/app/engine.py', '_execute_workflow', 2, 11, 19).
python_function('backend/app/engine.py', '_track_background_task', 1, 1, 5).
python_function('backend/app/engine.py', 'run_workflow', 1, 1, 2).
python_function('backend/app/engine.py', 'start_workflow', 1, 1, 7).
python_function('backend/app/logging_setup.py', 'get_request_id', 0, 1, 1).
python_function('backend/app/logging_setup.py', 'setup_logging', 2, 3, 9).
python_function('backend/app/main.py', 'health', 0, 1, 1).
python_function('backend/app/routers/chat.py', '_proxy_chat_payload', 2, 9, 12).
python_function('backend/app/routers/chat.py', 'chat_start', 1, 2, 4).
python_function('backend/app/routers/chat.py', 'chat_message', 1, 12, 13).
python_function('backend/app/routers/chat.py', 'chat_get_state', 1, 2, 6).
python_function('backend/app/routers/settings.py', 'actions_schema', 0, 1, 4).
python_function('backend/app/routers/settings.py', 'action_schema', 1, 2, 5).
python_function('backend/app/routers/settings.py', 'get_settings', 0, 1, 4).
python_function('backend/app/routers/settings.py', 'get_settings_section', 1, 2, 5).
python_function('backend/app/routers/settings.py', 'update_settings_section', 2, 2, 5).
python_function('backend/app/routers/settings.py', 'set_setting', 1, 2, 5).
python_function('backend/app/routers/settings.py', 'reset_settings', 1, 1, 4).
python_function('backend/app/routers/system.py', 'system_execute', 1, 2, 5).
python_function('backend/app/routers/workflow.py', '_format_sse', 2, 5, 4).
python_function('backend/app/routers/workflow.py', '_workflow_snapshot', 1, 1, 1).
python_function('backend/app/routers/workflow.py', 'list_actions', 0, 1, 1).
python_function('backend/app/routers/workflow.py', 'run_workflow_endpoint', 1, 1, 2).
python_function('backend/app/routers/workflow.py', 'start_workflow_endpoint', 1, 1, 2).
python_function('backend/app/routers/workflow.py', 'get_history', 0, 1, 2).
python_function('backend/app/routers/workflow.py', 'get_workflow', 1, 2, 3).
python_function('backend/app/routers/workflow.py', 'stream_workflow', 2, 2, 12).
python_function('backend/app/routers/workflow.py', 'workflow_from_text', 1, 8, 12).
python_function('backend/tests/conftest.py', 'client', 0, 1, 2).
python_function('backend/tests/test_workflow_api.py', '_mock_worker_response', 2, 2, 1).
python_function('examples/01-invoice/main.py', 'main', 0, 1, 1).
python_function('examples/02-email/main.py', 'main', 0, 1, 1).
python_function('examples/03-report-and-notify/main.py', 'main', 0, 1, 1).
python_function('examples/04-scheduled-report/main.py', 'main', 0, 1, 1).
python_function('examples/05-conversation-flow/main.py', 'main', 0, 2, 6).
python_function('examples/code_generation_examples.py', 'main', 0, 1, 1).
python_function('nlp-service/app/audio_parser.py', 'stt_audio', 2, 9, 9).
python_function('nlp-service/app/audio_parser.py', 'stt_file', 2, 2, 4).
python_function('nlp-service/app/audio_parser.py', 'is_stt_available', 0, 2, 0).
python_function('nlp-service/app/conversation/merge.py', 'merge_into_state', 2, 9, 4).
python_function('nlp-service/app/conversation/orchestrator.py', 'start_conversation', 1, 1, 6).
python_function('nlp-service/app/conversation/orchestrator.py', 'continue_conversation', 2, 2, 7).
python_function('nlp-service/app/conversation/orchestrator.py', 'get_conversation', 1, 2, 2).
python_function('nlp-service/app/conversation/orchestrator.py', '_attach_routing', 2, 1, 1).
python_function('nlp-service/app/conversation/orchestrator.py', '_process_message', 2, 6, 12).
python_function('nlp-service/app/conversation/responses.py', 'deny_message', 1, 3, 0).
python_function('nlp-service/app/conversation/responses.py', '_is_execute_or_continue', 1, 2, 3).
python_function('nlp-service/app/conversation/responses.py', 'check_execute_keyword', 2, 7, 5).
python_function('nlp-service/app/conversation/responses.py', 'handle_unknown_intent', 1, 5, 4).
python_function('nlp-service/app/conversation/responses.py', 'handle_system_action', 1, 7, 7).
python_function('nlp-service/app/conversation/responses.py', 'build_and_check_dsl', 1, 4, 6).
python_function('nlp-service/app/conversation/responses.py', 'build_incomplete_response', 1, 3, 6).
python_function('nlp-service/app/conversation/responses.py', '_nlp_from_state', 1, 5, 5).
python_function('nlp-service/app/conversation/responses.py', 'format_system_result', 2, 3, 3).
python_function('nlp-service/app/conversation/responses.py', '_format_system_status', 1, 1, 1).
python_function('nlp-service/app/conversation/responses.py', '_format_settings_get', 1, 1, 2).
python_function('nlp-service/app/conversation/responses.py', '_format_settings_set', 1, 1, 1).
python_function('nlp-service/app/conversation/responses.py', '_format_settings_reset', 1, 1, 1).
python_function('nlp-service/app/conversation/responses.py', '_format_file_read', 1, 2, 1).
python_function('nlp-service/app/conversation/responses.py', '_format_file_write', 1, 2, 1).
python_function('nlp-service/app/conversation/responses.py', '_format_file_list', 1, 2, 3).
python_function('nlp-service/app/conversation/responses.py', '_format_registry_list', 1, 3, 4).
python_function('nlp-service/app/conversation/responses.py', '_format_registry_update', 1, 1, 1).
python_function('nlp-service/app/dsl/forms.py', 'get_action_form', 1, 5, 5).
python_function('nlp-service/app/dsl/mapper.py', 'map_to_dsl', 1, 8, 14).
python_function('nlp-service/app/dsl/mapper.py', '_resolve_actions', 1, 7, 4).
python_function('nlp-service/app/dsl/mapper.py', '_build_config', 2, 6, 7).
python_function('nlp-service/app/dsl/mapper.py', '_get_field_mapping', 1, 1, 1).
python_function('nlp-service/app/dsl/mapper.py', '_make_name', 2, 3, 2).
python_function('nlp-service/app/dsl/mapper.py', '_build_prompt', 1, 2, 6).
python_function('nlp-service/app/execution/delegate.py', 'is_delegated_to_mullm', 1, 2, 1).
python_function('nlp-service/app/execution/delegate.py', 'execution_backend_for_intent', 1, 2, 1).
python_function('nlp-service/app/execution/delegate.py', 'mullm_action_names', 0, 1, 1).
python_function('nlp-service/app/execution/delegate.py', 'delegate_payload', 2, 1, 0).
python_function('nlp-service/app/execution/system.py', '_validate_file_path', 1, 5, 7).
python_function('nlp-service/app/execution/system.py', '_is_read_only', 1, 2, 5).
python_function('nlp-service/app/execution/system.py', 'execute_system_action', 2, 3, 5).
python_function('nlp-service/app/execution/system.py', '_exec_settings_get', 1, 2, 4).
python_function('nlp-service/app/execution/system.py', '_exec_settings_set', 1, 3, 2).
python_function('nlp-service/app/execution/system.py', '_exec_settings_reset', 1, 3, 2).
python_function('nlp-service/app/execution/system.py', '_exec_file_read', 1, 9, 13).
python_function('nlp-service/app/execution/system.py', '_exec_file_write', 1, 4, 10).
python_function('nlp-service/app/execution/system.py', '_exec_file_list', 1, 8, 12).
python_function('nlp-service/app/execution/system.py', '_exec_registry_list', 1, 4, 5).
python_function('nlp-service/app/execution/system.py', '_exec_registry_add', 1, 11, 4).
python_function('nlp-service/app/execution/system.py', '_exec_registry_edit', 1, 12, 5).
python_function('nlp-service/app/execution/system.py', '_exec_status', 1, 3, 2).
python_function('nlp-service/app/governance/bootstrap.py', '_actions_from_yaml_areas', 0, 14, 6).
python_function('nlp-service/app/governance/bootstrap.py', 'apply_yaml_actions', 1, 4, 5).
python_function('nlp-service/app/governance/bootstrap.py', 'bootstrap_registry', 1, 1, 6).
python_function('nlp-service/app/governance/config.py', '_search_paths', 0, 6, 10).
python_function('nlp-service/app/governance/config.py', '_load_yaml_file', 1, 3, 4).
python_function('nlp-service/app/governance/config.py', '_merge_dict', 2, 8, 3).
python_function('nlp-service/app/governance/config.py', 'load_access_config', 0, 3, 2).
python_function('nlp-service/app/governance/config.py', '_load_merged_config', 0, 4, 7).
python_function('nlp-service/app/governance/config.py', '_build_access_config', 2, 7, 9).
python_function('nlp-service/app/governance/config.py', '_enabled_integrations', 1, 7, 3).
python_function('nlp-service/app/governance/config.py', '_default_agent', 2, 3, 2).
python_function('nlp-service/app/governance/config.py', '_allowed_uri_schemes', 1, 3, 2).
python_function('nlp-service/app/governance/config.py', 'get_access_config', 0, 1, 1).
python_function('nlp-service/app/governance/config.py', 'reload_access_config', 0, 1, 1).
python_function('nlp-service/app/governance/policy.py', 'get_agent_id', 1, 4, 3).
python_function('nlp-service/app/governance/policy.py', '_grant_matches', 1, 2, 2).
python_function('nlp-service/app/governance/policy.py', '_grant_action_matches', 2, 4, 3).
python_function('nlp-service/app/governance/policy.py', '_grant_target_matches', 1, 5, 3).
python_function('nlp-service/app/governance/policy.py', '_area_selector_match', 2, 3, 0).
python_function('nlp-service/app/governance/policy.py', '_uri_selector_match', 2, 3, 2).
python_function('nlp-service/app/governance/policy.py', 'authorize_action', 2, 5, 7).
python_function('nlp-service/app/governance/policy.py', '_action_context', 1, 5, 3).
python_function('nlp-service/app/governance/policy.py', '_scheme_decision', 1, 3, 2).
python_function('nlp-service/app/governance/policy.py', '_effect_decision', 4, 4, 1).
python_function('nlp-service/app/governance/policy.py', '_unknown_agent_decision', 2, 4, 1).
python_function('nlp-service/app/governance/policy.py', '_matched_effect', 1, 3, 4).
python_function('nlp-service/app/governance/policy.py', '_decision', 7, 1, 1).
python_function('nlp-service/app/governance/uri_match.py', 'normalize_uri', 1, 2, 1).
python_function('nlp-service/app/governance/uri_match.py', 'uri_matches', 2, 8, 7).
python_function('nlp-service/app/governance/uri_match.py', 'scheme_allowed', 2, 5, 2).
python_function('nlp-service/app/logging_setup.py', 'get_request_id', 0, 1, 1).
python_function('nlp-service/app/logging_setup.py', 'setup_logging', 2, 3, 9).
python_function('nlp-service/app/main.py', 'parse_text', 1, 1, 2).
python_function('nlp-service/app/main.py', 'text_to_dsl', 1, 2, 4).
python_function('nlp-service/app/main.py', 'access_config', 0, 3, 5).
python_function('nlp-service/app/main.py', 'access_check', 5, 3, 3).
python_function('nlp-service/app/main.py', 'access_reload', 0, 2, 2).
python_function('nlp-service/app/main.py', 'list_actions', 0, 2, 4).
python_function('nlp-service/app/main.py', 'health', 0, 3, 8).
python_function('nlp-service/app/main.py', 'chat_start', 2, 5, 10).
python_function('nlp-service/app/main.py', 'chat_message', 3, 5, 10).
python_function('nlp-service/app/main.py', 'chat_state', 1, 2, 4).
python_function('nlp-service/app/main.py', 'actions_schema', 0, 3, 3).
python_function('nlp-service/app/main.py', 'action_schema', 1, 2, 3).
python_function('nlp-service/app/main.py', 'get_settings', 0, 1, 3).
python_function('nlp-service/app/main.py', 'get_settings_section', 1, 2, 3).
python_function('nlp-service/app/main.py', 'update_settings_section', 2, 2, 4).
python_function('nlp-service/app/main.py', 'set_setting', 1, 3, 5).
python_function('nlp-service/app/main.py', 'reset_settings', 1, 1, 3).
python_function('nlp-service/app/main.py', 'system_execute', 1, 2, 6).
python_function('nlp-service/app/main.py', 'generate_code', 1, 2, 4).
python_function('nlp-service/app/main.py', 'get_supported_languages', 0, 2, 3).
python_function('nlp-service/app/main.py', '_run_parser', 1, 7, 5).
python_function('nlp-service/app/main.py', 'websocket_chat', 2, 10, 16).
python_function('nlp-service/app/main.py', 'chat_ui', 0, 2, 5).
python_function('nlp-service/app/registry.py', 'get_action_by_alias', 1, 5, 3).
python_function('nlp-service/app/registry.py', 'get_trigger', 1, 3, 2).
python_function('nlp-service/app/registry.py', 'get_required_fields', 1, 1, 1).
python_function('nlp-service/app/registry.py', 'get_defaults', 1, 1, 2).
python_function('nlp-service/app/routing/native.py', '_match_route', 2, 4, 5).
python_function('nlp-service/app/routing/native.py', '_patterns_match', 2, 3, 3).
python_function('nlp-service/app/routing/native.py', '_pattern_matches', 2, 4, 5).
python_function('nlp-service/app/routing/native.py', '_regex_pattern_matches', 2, 4, 3).
python_function('nlp-service/app/routing/native.py', '_keywords_pattern_matches', 2, 4, 5).
python_function('nlp-service/app/routing/native.py', '_substring_pattern_matches', 2, 4, 4).
python_function('nlp-service/app/routing/native.py', '_aliases_match', 2, 2, 3).
python_function('nlp-service/app/routing/native.py', 'resolve_native_intent', 1, 4, 5).
python_function('nlp-service/app/routing/native.py', '_resolve_configured_route', 3, 5, 4).
python_function('nlp-service/app/routing/native.py', '_route_decision', 3, 2, 1).
python_function('nlp-service/app/routing/native.py', '_resolve_action_alias', 2, 2, 3).
python_function('nlp-service/app/routing/native.py', '_best_action_alias', 2, 3, 3).
python_function('nlp-service/app/routing/native.py', '_best_alias_for_action', 4, 6, 4).
python_function('nlp-service/app/routing/observability.py', 'record_intent_decision', 1, 7, 4).
python_function('nlp-service/app/routing/observability.py', 'routing_metrics_snapshot', 0, 1, 1).
python_function('nlp-service/app/routing/observability.py', 'reset_routing_metrics', 0, 1, 1).
python_function('nlp-service/app/routing/parser/facade.py', 'parse_text', 2, 8, 6).
python_function('nlp-service/app/routing/parser/llm.py', 'parse_llm', 1, 3, 11).
python_function('nlp-service/app/routing/parser/llm.py', '_detect_provider', 0, 10, 1).
python_function('nlp-service/app/routing/parser/llm.py', '_parse_json_response', 1, 6, 7).
python_function('nlp-service/app/routing/parser/rules.py', 'parse_rules', 1, 5, 10).
python_function('nlp-service/app/routing/parser/rules.py', '_detect_actions', 1, 3, 3).
python_function('nlp-service/app/routing/parser/rules.py', '_action_alias_scores', 1, 4, 3).
python_function('nlp-service/app/routing/parser/rules.py', '_longest_alias_match', 2, 4, 3).
python_function('nlp-service/app/routing/parser/rules.py', '_actions_by_score', 1, 1, 2).
python_function('nlp-service/app/routing/parser/rules.py', '_dominant_overlap_action', 2, 4, 4).
python_function('nlp-service/app/routing/parser/rules.py', '_action_category', 1, 1, 2).
python_function('nlp-service/app/routing/parser/rules.py', '_top_system_action_wins', 4, 4, 0).
python_function('nlp-service/app/routing/parser/rules.py', '_second_system_action_wins', 4, 3, 0).
python_function('nlp-service/app/routing/parser/rules.py', '_resolve_intent', 1, 5, 5).
python_function('nlp-service/app/routing/parser/rules.py', '_extract_entities', 2, 1, 9).
python_function('nlp-service/app/routing/parser/rules.py', '_extract_amount', 2, 5, 5).
python_function('nlp-service/app/routing/parser/rules.py', '_extract_email', 2, 2, 2).
python_function('nlp-service/app/routing/parser/rules.py', '_extract_report_type', 2, 3, 1).
python_function('nlp-service/app/routing/parser/rules.py', '_extract_format', 2, 3, 1).
python_function('nlp-service/app/routing/parser/rules.py', '_extract_notification_channels', 2, 6, 2).
python_function('nlp-service/app/routing/parser/rules.py', '_extract_param_aliases', 2, 5, 4).
python_function('nlp-service/app/routing/parser/rules.py', '_extract_system_entities', 3, 1, 5).
python_function('nlp-service/app/routing/parser/rules.py', '_extract_file_path_entity', 2, 3, 2).
python_function('nlp-service/app/routing/parser/rules.py', '_extract_setting_path_entity', 2, 3, 2).
python_function('nlp-service/app/routing/parser/rules.py', '_extract_model_setting_entity', 2, 5, 1).
python_function('nlp-service/app/routing/parser/rules.py', '_extract_numeric_setting_value', 2, 3, 2).
python_function('nlp-service/app/routing/parser/rules.py', '_extract_mode_setting_entity', 2, 6, 1).
python_function('nlp-service/app/routing/parser/rules.py', '_extract_fallback_recipient', 2, 7, 2).
python_function('nlp-service/app/routing/parser/rules.py', '_set_entity', 3, 3, 2).
python_function('nlp-service/app/routing/resolve.py', '_parser_source', 1, 5, 4).
python_function('nlp-service/app/routing/resolve.py', '_intent_from_native', 1, 3, 3).
python_function('nlp-service/app/routing/resolve.py', '_intent_from_nlp', 2, 2, 4).
python_function('nlp-service/app/routing/resolve.py', '_apply_auth', 2, 4, 1).
python_function('nlp-service/app/routing/resolve.py', 'resolve_intent', 1, 12, 14).
python_function('nlp-service/app/settings.py', '_coerce_type', 2, 5, 5).
python_function('nlp-service/app/store/factory.py', 'get_conversation_store', 0, 4, 5).
python_function('nlp-service/integrations/loader.py', '_integration_names', 0, 5, 4).
python_function('nlp-service/integrations/loader.py', 'load_integration_registries', 0, 5, 8).
python_function('nlp-service/integrations/loader.py', 'apply_integrations', 1, 5, 6).
python_function('nlp-service/tests/conftest.py', 'sample_texts', 0, 1, 0).
python_function('nlp-service/tests/conftest.py', 'expected_intents', 0, 1, 0).
python_function('nlp-service/tests/conftest.py', 'sample_entities', 0, 1, 0).
python_function('nlp-service/tests/conftest.py', 'mock_conversation_store', 0, 1, 1).
python_function('nlp-service/tests/test_access.py', '_point_config', 1, 1, 3).
python_function('nlp-service/tests/test_access.py', 'test_config_loads_areas', 0, 3, 3).
python_function('nlp-service/tests/test_access.py', 'test_uri_match_mullm', 0, 4, 1).
python_function('nlp-service/tests/test_access.py', 'test_files_agent_can_list', 0, 3, 1).
python_function('nlp-service/tests/test_access.py', 'test_mail_agent_denied_mullm_execute', 0, 2, 1).
python_function('nlp-service/tests/test_access.py', 'test_native_lista_plikow', 0, 3, 1).
python_function('nlp-service/tests/test_access.py', 'test_registry_has_yaml_action', 0, 3, 2).
python_function('nlp-service/tests/test_execution_delegate.py', 'test_mullm_shell_delegated', 0, 3, 2).
python_function('nlp-service/tests/test_execution_delegate.py', 'test_invoice_worker_backend', 0, 2, 1).
python_function('nlp-service/tests/test_execution_delegate.py', 'test_delegate_payload_shape', 0, 3, 1).
python_function('nlp-service/tests/test_orchestrator.py', '_patch_store', 1, 1, 3).
python_function('nlp-service/tests/test_routing_observability.py', '_reset_metrics', 0, 1, 2).
python_function('nlp-service/tests/test_routing_observability.py', 'test_record_increments_rules_hit', 0, 2, 4).
python_function('nlp-service/tests/test_routing_observability.py', 'test_resolve_intent_updates_metrics', 0, 2, 3).
python_function('nlp-service/tests/test_system_executor.py', '_reset_settings', 1, 1, 3).
python_function('nlp2dsl_sdk/__main__.py', 'main', 0, 5, 7).
python_function('nlp2dsl_sdk/client.py', 'workflow_step', 1, 1, 1).
python_function('nlp2dsl_sdk/demos.py', '_ensure_services', 1, 2, 2).
python_function('nlp2dsl_sdk/demos.py', '_print_json', 1, 1, 2).
python_function('nlp2dsl_sdk/demos.py', '_print_workflow_preview', 1, 4, 4).
python_function('nlp2dsl_sdk/demos.py', '_print_execution_result', 1, 5, 5).
python_function('nlp2dsl_sdk/demos.py', '_print_code_generation_preview', 1, 3, 3).
python_function('nlp2dsl_sdk/demos.py', '_preview_text_examples', 3, 3, 4).
python_function('nlp2dsl_sdk/demos.py', 'run_crm_update_demo', 1, 3, 6).
python_function('nlp2dsl_sdk/demos.py', 'run_action_catalog_demo', 1, 6, 10).
python_function('nlp2dsl_sdk/demos.py', 'run_automation_gallery_demo', 1, 3, 4).
python_function('nlp2dsl_sdk/demos.py', '_run_workflow_examples', 3, 3, 3).
python_function('nlp2dsl_sdk/demos.py', '_run_gallery_examples', 3, 5, 9).
python_function('nlp2dsl_sdk/demos.py', 'run_invoice_demo', 1, 5, 7).
python_function('nlp2dsl_sdk/demos.py', 'run_email_demo', 1, 5, 7).
python_function('nlp2dsl_sdk/demos.py', 'run_report_and_notify_demo', 1, 4, 7).
python_function('nlp2dsl_sdk/demos.py', 'run_scheduled_report_demo', 1, 4, 5).
python_function('nlp2dsl_sdk/demos.py', 'run_code_generation_demo', 1, 6, 9).
python_function('nlp2dsl_sdk/demos.py', '_run_direct_code_generation', 1, 5, 6).
python_function('nlp2dsl_sdk/demos.py', '_get_supported_languages', 1, 3, 4).
python_function('nlp2dsl_sdk/demos.py', '_run_workflow_code_examples', 1, 1, 1).
python_function('nlp2dsl_sdk/demos.py', '_run_conversation_code_example', 1, 3, 5).
python_function('nlp2dsl_sdk/demos.py', '_run_worker_code_generation', 1, 6, 6).
python_function('nlp2dsl_sdk/demos.py', 'list_available_demos', 0, 1, 0).
python_function('test_code_generation.py', 'test_code_generation', 0, 11, 14).
python_function('tests/e2e/conftest.py', '_resolve_browser_executable', 0, 3, 1).
python_function('tests/e2e/conftest.py', 'nlp_client', 0, 1, 1).
python_function('tests/e2e/conftest.py', 'backend_client', 0, 1, 1).
python_function('tests/e2e/conftest.py', 'browser_instance', 0, 2, 5).
python_function('tests/e2e/conftest.py', 'browser_context', 1, 1, 3).
python_function('tests/e2e/conftest.py', 'page', 1, 1, 3).
python_function('tests/e2e/conftest.py', 'chat_page', 1, 2, 5).
python_function('tests/e2e/test_backend.py', 'test_health', 1, 4, 2).
python_function('tests/e2e/test_backend.py', 'test_workflow_actions_list', 1, 7, 4).
python_function('tests/e2e/test_backend.py', 'test_workflow_actions_contains_send_invoice', 1, 4, 2).
python_function('tests/e2e/test_backend.py', 'test_from_text_dsl_only_no_execute', 1, 5, 2).
python_function('tests/e2e/test_backend.py', 'test_from_text_empty_returns_400', 1, 2, 1).
python_function('tests/e2e/test_backend.py', 'test_from_text_unknown_intent_propagates_error', 1, 2, 1).
python_function('tests/e2e/test_backend.py', 'test_workflow_history_returns_list', 1, 3, 3).
python_function('tests/e2e/test_backend.py', 'test_workflow_history_unknown_id_returns_404', 1, 2, 1).
python_function('tests/e2e/test_backend.py', 'test_chat_start_proxied_to_nlp', 1, 4, 2).
python_function('tests/e2e/test_backend.py', 'test_chat_start_empty_returns_error', 1, 2, 1).
python_function('tests/e2e/test_backend.py', 'test_chat_message_proxied_to_nlp', 1, 4, 2).
python_function('tests/e2e/test_backend.py', 'test_workflow_actions_schema', 1, 4, 4).
python_function('tests/e2e/test_backend.py', 'test_workflow_settings_proxied', 1, 3, 2).
python_function('tests/e2e/test_chat_ui.py', 'test_page_title', 1, 3, 2).
python_function('tests/e2e/test_chat_ui.py', 'test_page_has_no_js_errors', 1, 2, 4).
python_function('tests/e2e/test_chat_ui.py', 'test_web_app_manifest', 1, 3, 2).
python_function('tests/e2e/test_chat_ui.py', 'test_tts_button_present', 1, 2, 1).
python_function('tests/e2e/test_chat_ui.py', 'test_tts_button_default_state_active', 1, 3, 3).
python_function('tests/e2e/test_chat_ui.py', 'test_tts_toggle_disables', 1, 3, 4).
python_function('tests/e2e/test_chat_ui.py', 'test_tts_toggle_re_enables', 1, 3, 4).
python_function('tests/e2e/test_chat_ui.py', 'test_speak_function_defined', 1, 2, 1).
python_function('tests/e2e/test_chat_ui.py', 'test_speech_synthesis_available', 1, 2, 1).
python_function('tests/e2e/test_chat_ui.py', 'test_speak_calls_speech_synthesis', 1, 2, 1).
python_function('tests/e2e/test_chat_ui.py', 'test_speak_respects_tts_disabled', 1, 2, 1).
python_function('tests/e2e/test_chat_ui.py', 'test_microphone_get_user_media', 1, 2, 1).
python_function('tests/e2e/test_chat_ui.py', 'test_media_recorder_supported', 1, 2, 1).
python_function('tests/e2e/test_chat_ui.py', 'test_voice_button_present', 1, 2, 1).
python_function('tests/e2e/test_chat_ui.py', 'test_voice_button_initial_text', 1, 2, 2).
python_function('tests/e2e/test_chat_ui.py', 'wait_for_voice_recording', 2, 3, 5).
python_function('tests/e2e/test_chat_ui.py', 'test_voice_transcription_autostarts_on_load', 1, 3, 5).
python_function('tests/e2e/test_chat_ui.py', 'test_voice_button_click_stops_recording', 1, 2, 5).
python_function('tests/e2e/test_chat_ui.py', 'test_text_input_present', 1, 2, 1).
python_function('tests/e2e/test_chat_ui.py', 'test_send_button_present', 1, 2, 1).
python_function('tests/e2e/test_chat_ui.py', 'test_text_message_renders_user_bubble', 1, 2, 5).
python_function('tests/e2e/test_chat_ui.py', 'test_text_message_gets_assistant_response', 1, 2, 5).
python_function('tests/e2e/test_chat_ui.py', 'test_speak_called_on_assistant_response', 1, 3, 5).
python_function('tests/e2e/test_chat_ui.py', 'test_text_input_cleared_after_send', 1, 2, 4).
python_function('tests/e2e/test_chat_ui.py', 'test_status_element_present', 1, 2, 1).
python_function('tests/e2e/test_chat_ui.py', 'test_websocket_connects_on_load', 1, 2, 1).
python_function('tests/e2e/test_nlp_service.py', 'test_health', 1, 7, 4).
python_function('tests/e2e/test_nlp_service.py', 'test_nlp_actions_registry', 1, 8, 5).
python_function('tests/e2e/test_nlp_service.py', 'test_parse_known_intent_rules', 1, 6, 2).
python_function('tests/e2e/test_nlp_service.py', 'test_parse_unknown_intent_rules', 1, 3, 2).
python_function('tests/e2e/test_nlp_service.py', 'test_parse_send_email_intent', 1, 3, 2).
python_function('tests/e2e/test_nlp_service.py', 'test_to_dsl_complete_invoice', 1, 5, 2).
python_function('tests/e2e/test_nlp_service.py', 'test_to_dsl_unknown_returns_422', 1, 3, 2).
python_function('tests/e2e/test_nlp_service.py', 'test_chat_start_text', 1, 5, 3).
python_function('tests/e2e/test_nlp_service.py', 'test_chat_start_empty_text_returns_400', 1, 2, 1).
python_function('tests/e2e/test_nlp_service.py', 'test_chat_message_continue_conversation', 1, 6, 2).
python_function('tests/e2e/test_nlp_service.py', 'test_chat_state_get', 1, 4, 3).
python_function('tests/e2e/test_nlp_service.py', 'test_chat_state_not_found', 1, 2, 1).
python_function('tests/e2e/test_nlp_service.py', 'test_actions_schema_all', 1, 4, 4).
python_function('tests/e2e/test_nlp_service.py', 'test_action_schema_by_name', 1, 3, 5).
python_function('tests/e2e/test_nlp_service.py', 'test_action_schema_unknown_returns_404', 1, 2, 1).
python_function('tests/e2e/test_nlp_service.py', 'test_settings_get_all', 1, 4, 2).
python_function('tests/e2e/test_nlp_service.py', 'test_settings_get_llm_section', 1, 5, 2).
python_function('tests/e2e/test_nlp_service.py', 'test_settings_unknown_section_returns_404', 1, 2, 1).
python_function('tests/e2e/test_nlp_service.py', 'test_chat_ui_serves_html', 1, 4, 2).
python_function('tests/e2e/test_websocket.py', '_uri', 1, 1, 0).
python_function('tests/e2e/test_websocket.py', '_is_open', 1, 1, 0).
python_function('tests/e2e/test_websocket.py', '_is_closed', 1, 1, 0).
python_function('tests/e2e/test_websocket.py', 'test_websocket_connects_and_accepts', 0, 2, 3).
python_function('tests/e2e/test_websocket.py', 'test_websocket_unique_conversation_id', 0, 3, 3).
python_function('tests/e2e/test_websocket.py', 'test_websocket_accepts_binary_audio', 0, 4, 8).
python_function('tests/e2e/test_websocket.py', 'test_websocket_accepts_multiple_chunks', 0, 3, 7).
python_function('tests/e2e/test_websocket.py', 'test_websocket_clean_disconnect', 0, 3, 4).
python_function('tests/e2e/test_websocket.py', 'test_websocket_server_survives_abrupt_close', 0, 2, 5).
python_function('tests/e2e/test_websocket.py', 'test_websocket_concurrent_connections', 0, 4, 7).
python_function('tests/test_nlp2dsl_sdk.py', 'client_factory', 0, 1, 3).
python_function('tests/test_nlp2dsl_sdk.py', 'test_from_env_prefers_repo_env_names', 1, 5, 3).
python_function('tests/test_nlp2dsl_sdk.py', 'test_workflow_and_conversation_endpoints', 1, 17, 7).
python_function('tests/test_nlp2dsl_sdk.py', 'test_report_helpers_use_report_type_and_schedule', 1, 10, 4).
python_function('tests/test_nlp2dsl_sdk.py', 'test_new_workflow_helpers_are_data_driven', 1, 14, 6).
python_function('tests/test_nlp2dsl_sdk.py', 'test_code_generation_methods_hit_expected_services', 1, 16, 7).
python_function('tests/test_nlp2dsl_sdk.py', 'test_health_queries_all_services', 1, 7, 3).
python_function('tests/test_placeholder.py', 'test_placeholder', 0, 2, 0).
python_function('tests/test_placeholder.py', 'test_import', 0, 1, 0).
python_function('tests/test_tests.py', 'test_placeholder', 0, 2, 0).
python_function('tests/test_tests.py', 'test_import', 0, 1, 0).
python_function('worker/logging_setup.py', 'get_request_id', 0, 1, 1).
python_function('worker/logging_setup.py', 'setup_logging', 2, 3, 9).
python_function('worker/tests/conftest.py', '_noop_sleep', 0, 1, 0).
python_function('worker/tests/conftest.py', 'mock_asyncio_sleep', 0, 1, 3).
python_function('worker/tests/conftest.py', 'client', 0, 1, 2).
python_function('worker/tests/test_worker.py', 'client', 0, 1, 2).
python_function('worker/worker.py', 'action', 1, 1, 0).
python_function('worker/worker.py', '_deliver_notification', 4, 5, 8).
python_function('worker/worker.py', 'handle_send_invoice', 1, 1, 6).
python_function('worker/worker.py', 'handle_send_email', 1, 1, 4).
python_function('worker/worker.py', 'handle_generate_report', 1, 1, 6).
python_function('worker/worker.py', 'handle_crm_update', 1, 1, 4).
python_function('worker/worker.py', 'handle_notify_slack', 1, 1, 4).
python_function('worker/worker.py', 'handle_notify_telegram', 1, 1, 4).
python_function('worker/worker.py', 'handle_notify_teams', 1, 1, 4).
python_function('worker/worker.py', 'handle_generate_code', 1, 5, 12).
python_function('worker/worker.py', 'execute_step', 1, 2, 7).
python_function('worker/worker.py', 'health', 0, 1, 3).

% ── Python Classes ───────────────────────────────────────
python_class('backend/app/config.py', 'BackendSettings').
python_class('backend/app/db/__init__.py', 'WorkflowRepo').
python_method('WorkflowRepo', 'save_run', 4, 1, 0).
python_method('WorkflowRepo', 'update_run_status', 2, 1, 0).
python_method('WorkflowRepo', 'get_run', 1, 1, 0).
python_method('WorkflowRepo', 'list_runs', 2, 1, 0).
python_method('WorkflowRepo', 'count_runs', 0, 1, 0).
python_class('backend/app/db/memory.py', 'MemoryWorkflowRepo').
python_method('MemoryWorkflowRepo', '__init__', 1, 1, 1).
python_method('MemoryWorkflowRepo', 'save_run', 4, 2, 3).
python_method('MemoryWorkflowRepo', 'update_run_status', 2, 2, 0).
python_method('MemoryWorkflowRepo', 'get_run', 1, 1, 1).
python_method('MemoryWorkflowRepo', 'list_runs', 2, 1, 3).
python_method('MemoryWorkflowRepo', 'count_runs', 0, 1, 1).
python_class('backend/app/db/postgres.py', 'Base').
python_class('backend/app/db/postgres.py', 'WorkflowRunModel').
python_method('WorkflowRunModel', 'to_dict', 0, 4, 1).
python_class('backend/app/db/postgres.py', 'PostgresWorkflowRepo').
python_method('PostgresWorkflowRepo', '__init__', 1, 2, 4).
python_method('PostgresWorkflowRepo', '_ensure_engine', 0, 3, 2).
python_method('PostgresWorkflowRepo', '_get_session_factory', 0, 1, 1).
python_method('PostgresWorkflowRepo', '_ensure_tables', 0, 2, 4).
python_method('PostgresWorkflowRepo', 'save_run', 4, 1, 10).
python_method('PostgresWorkflowRepo', 'update_run_status', 2, 1, 6).
python_method('PostgresWorkflowRepo', 'get_run', 1, 2, 4).
python_method('PostgresWorkflowRepo', 'list_runs', 2, 3, 7).
python_method('PostgresWorkflowRepo', 'count_runs', 0, 2, 5).
python_method('PostgresWorkflowRepo', 'close', 0, 2, 1).
python_class('backend/app/logging_setup.py', 'JSONFormatter').
python_method('JSONFormatter', '__init__', 1, 1, 2).
python_method('JSONFormatter', 'format', 1, 2, 6).
python_class('backend/app/logging_setup.py', 'RequestIDMiddleware').
python_method('RequestIDMiddleware', '__init__', 2, 1, 2).
python_method('RequestIDMiddleware', 'dispatch', 2, 2, 5).
python_class('backend/app/schemas.py', 'StepStatus').
python_class('backend/app/schemas.py', 'Step').
python_class('backend/app/schemas.py', 'RunWorkflowRequest').
python_class('backend/app/schemas.py', 'StepResult').
python_class('backend/app/schemas.py', 'WorkflowResult').
python_class('backend/app/schemas.py', 'ActionInfo').
python_class('backend/app/workflow_events.py', 'WorkflowEvent').
python_method('WorkflowEvent', 'is_terminal', 0, 1, 0).
python_method('WorkflowEvent', 'to_dict', 0, 1, 1).
python_class('backend/app/workflow_events.py', 'WorkflowEventHub').
python_method('WorkflowEventHub', '__init__', 0, 1, 2).
python_method('WorkflowEventHub', 'subscribe', 1, 1, 2).
python_method('WorkflowEventHub', 'unsubscribe', 2, 3, 3).
python_method('WorkflowEventHub', 'publish', 1, 2, 4).
python_method('WorkflowEventHub', 'subscriber_count', 1, 1, 3).
python_class('backend/tests/test_config.py', 'TestBackendSettingsDefaults').
python_method('TestBackendSettingsDefaults', 'test_worker_url_default', 1, 2, 2).
python_method('TestBackendSettingsDefaults', 'test_nlp_service_url_default', 1, 2, 2).
python_method('TestBackendSettingsDefaults', 'test_postgres_url_default_none', 1, 2, 2).
python_method('TestBackendSettingsDefaults', 'test_log_level_default', 1, 2, 2).
python_class('backend/tests/test_config.py', 'TestBackendSettingsEnvOverride').
python_method('TestBackendSettingsEnvOverride', 'test_worker_url_from_env', 1, 2, 2).
python_method('TestBackendSettingsEnvOverride', 'test_postgres_url_from_env', 1, 2, 2).
python_method('TestBackendSettingsEnvOverride', 'test_log_level_from_env', 1, 2, 2).
python_method('TestBackendSettingsEnvOverride', 'test_extra_env_vars_ignored', 1, 2, 3).
python_class('backend/tests/test_config.py', 'TestBackendSettingsIntegration').
python_method('TestBackendSettingsIntegration', 'test_settings_singleton_importable', 0, 6, 1).
python_method('TestBackendSettingsIntegration', 'test_engine_uses_settings', 0, 3, 0).
python_class('backend/tests/test_logging.py', 'TestJSONFormatter').
python_method('TestJSONFormatter', 'test_format_produces_json', 0, 7, 4).
python_method('TestJSONFormatter', 'test_format_includes_exception', 0, 4, 6).
python_method('TestJSONFormatter', 'test_format_service_name', 0, 3, 4).
python_class('backend/tests/test_logging.py', 'TestRequestIDMiddleware').
python_method('TestRequestIDMiddleware', 'test_app', 0, 1, 3).
python_method('TestRequestIDMiddleware', 'test_response_has_request_id_header', 1, 4, 4).
python_method('TestRequestIDMiddleware', 'test_client_request_id_is_forwarded', 1, 2, 3).
python_method('TestRequestIDMiddleware', 'test_new_id_generated_without_header', 1, 2, 3).
python_class('backend/tests/test_logging.py', 'TestSetupLogging').
python_method('TestSetupLogging', 'test_setup_logging_installs_json_handler', 0, 3, 4).
python_method('TestSetupLogging', 'test_setup_logging_respects_log_level', 0, 2, 2).
python_class('backend/tests/test_persistence.py', 'TestMemoryRepoCRUD').
python_method('TestMemoryRepoCRUD', 'repo', 0, 1, 1).
python_method('TestMemoryRepoCRUD', 'test_save_and_get', 1, 6, 2).
python_method('TestMemoryRepoCRUD', 'test_get_nonexistent', 1, 2, 1).
python_method('TestMemoryRepoCRUD', 'test_update_status', 1, 2, 3).
python_method('TestMemoryRepoCRUD', 'test_update_nonexistent', 1, 1, 1).
python_method('TestMemoryRepoCRUD', 'test_count_empty', 1, 2, 1).
python_method('TestMemoryRepoCRUD', 'test_count_after_saves', 1, 3, 3).
python_class('backend/tests/test_persistence.py', 'TestMemoryRepoListOrdering').
python_method('TestMemoryRepoListOrdering', 'populated_repo', 0, 1, 2).
python_method('TestMemoryRepoListOrdering', 'test_list_default', 1, 5, 2).
python_method('TestMemoryRepoListOrdering', 'test_list_with_limit', 1, 3, 2).
python_method('TestMemoryRepoListOrdering', 'test_list_with_offset', 1, 3, 2).
python_class('backend/tests/test_persistence.py', 'TestMemoryRepoEviction').
python_method('TestMemoryRepoEviction', 'test_eviction_oldest', 0, 8, 5).
python_class('backend/tests/test_persistence.py', 'TestSerializationRoundtrip').
python_method('TestSerializationRoundtrip', 'test_steps_json_roundtrip', 0, 4, 3).
python_class('backend/tests/test_persistence.py', 'TestWorkflowRepoFactory').
python_method('TestWorkflowRepoFactory', 'test_factory_returns_memory_without_postgres', 1, 2, 3).
python_method('TestWorkflowRepoFactory', 'test_factory_returns_postgres_with_url', 1, 3, 4).
python_class('backend/tests/test_workflow_api.py', 'TestHealthEndpoint').
python_method('TestHealthEndpoint', 'test_health_endpoint', 1, 4, 2).
python_class('backend/tests/test_workflow_api.py', 'TestWorkflowActions').
python_method('TestWorkflowActions', 'test_workflow_actions', 1, 7, 4).
python_method('TestWorkflowActions', 'test_workflow_actions_contains_invoice', 1, 3, 2).
python_class('backend/tests/test_workflow_api.py', 'TestRunWorkflow').
python_method('TestRunWorkflow', 'test_run_workflow', 1, 4, 6).
python_method('TestRunWorkflow', 'test_run_workflow_step_failure', 1, 2, 4).
python_method('TestRunWorkflow', 'test_start_workflow', 1, 4, 5).
python_method('TestRunWorkflow', 'test_stream_workflow', 1, 4, 7).
python_class('backend/tests/test_workflow_api.py', 'TestWorkflowHistory').
python_method('TestWorkflowHistory', 'test_workflow_history', 1, 3, 3).
python_class('backend/tests/test_workflow_api.py', 'TestFromText').
python_method('TestFromText', 'test_from_text_complete', 1, 4, 5).
python_method('TestFromText', 'test_from_text_incomplete', 1, 4, 5).
python_method('TestFromText', 'test_from_text_empty', 1, 2, 1).
python_class('nlp-service/app/audio_parser.py', 'StreamingSTT').
python_method('StreamingSTT', '__init__', 1, 2, 1).
python_method('StreamingSTT', 'start', 0, 1, 1).
python_method('StreamingSTT', 'send_audio', 1, 2, 2).
python_method('StreamingSTT', 'get_transcript', 0, 1, 1).
python_method('StreamingSTT', 'stop', 0, 1, 1).
python_class('nlp-service/app/code_generator.py', 'CodeGenerator').
python_method('CodeGenerator', '__init__', 0, 1, 3).
python_method('CodeGenerator', '_get_api_key', 0, 5, 1).
python_method('CodeGenerator', '_build_prompt', 3, 2, 1).
python_method('CodeGenerator', 'generate_code', 4, 14, 12).
python_method('CodeGenerator', '_extract_class_name', 1, 2, 2).
python_method('CodeGenerator', '_split_code_and_tests', 2, 3, 2).
python_method('CodeGenerator', 'get_supported_languages', 0, 1, 2).
python_method('CodeGenerator', 'get_language_info', 1, 1, 1).
python_class('nlp-service/app/config.py', 'NLPServiceSettings').
python_class('nlp-service/app/governance/config.py', 'AccessConfig').
python_method('AccessConfig', 'action_to_area', 0, 6, 1).
python_method('AccessConfig', 'area_by_id', 1, 4, 1).
python_class('nlp-service/app/governance/policy.py', 'AccessDecision').
python_method('AccessDecision', 'to_dict', 0, 1, 0).
python_class('nlp-service/app/governance/policy.py', '_ActionContext').
python_class('nlp-service/app/logging_setup.py', 'JSONFormatter').
python_method('JSONFormatter', '__init__', 1, 1, 2).
python_method('JSONFormatter', 'format', 1, 2, 6).
python_class('nlp-service/app/logging_setup.py', 'RequestIDMiddleware').
python_method('RequestIDMiddleware', '__init__', 2, 1, 2).
python_method('RequestIDMiddleware', 'dispatch', 2, 2, 5).
python_class('nlp-service/app/routing/intent.py', 'IntentDecision').
python_method('IntentDecision', 'to_dict', 0, 1, 0).
python_method('IntentDecision', 'to_nlp_result', 1, 3, 3).
python_class('nlp-service/app/schemas.py', 'NLPIntent').
python_class('nlp-service/app/schemas.py', 'NLPEntities').
python_class('nlp-service/app/schemas.py', 'NLPResult').
python_class('nlp-service/app/schemas.py', 'DSLStep').
python_class('nlp-service/app/schemas.py', 'WorkflowDSL').
python_class('nlp-service/app/schemas.py', 'DialogResponse').
python_class('nlp-service/app/schemas.py', 'NLPRequest').
python_class('nlp-service/app/schemas.py', 'ConversationState').
python_class('nlp-service/app/schemas.py', 'FieldSchema').
python_class('nlp-service/app/schemas.py', 'ActionFormSchema').
python_class('nlp-service/app/schemas.py', 'ConversationResponse').
python_class('nlp-service/app/settings.py', 'LLMSettings').
python_class('nlp-service/app/settings.py', 'NLPSettings').
python_class('nlp-service/app/settings.py', 'WorkerSettings').
python_class('nlp-service/app/settings.py', 'FileAccessSettings').
python_class('nlp-service/app/settings.py', 'SystemSettings').
python_class('nlp-service/app/settings.py', 'SettingsManager').
python_method('SettingsManager', '__new__', 1, 2, 4).
python_method('SettingsManager', 'settings', 0, 1, 0).
python_method('SettingsManager', 'get', 1, 5, 4).
python_method('SettingsManager', 'get_section', 1, 3, 3).
python_method('SettingsManager', 'get_all', 0, 1, 1).
python_method('SettingsManager', 'set', 2, 4, 10).
python_method('SettingsManager', 'update_section', 2, 6, 9).
python_method('SettingsManager', 'reset', 1, 3, 6).
python_method('SettingsManager', '_load', 0, 3, 7).
python_method('SettingsManager', '_save', 0, 2, 5).
python_method('SettingsManager', 'describe', 0, 1, 1).
python_class('nlp-service/app/store/__init__.py', 'ConversationStore').
python_method('ConversationStore', 'get', 1, 1, 0).
python_method('ConversationStore', 'save', 2, 1, 0).
python_method('ConversationStore', 'delete', 1, 1, 0).
python_method('ConversationStore', 'count', 0, 1, 0).
python_class('nlp-service/app/store/memory.py', 'MemoryConversationStore').
python_method('MemoryConversationStore', '__init__', 0, 1, 0).
python_method('MemoryConversationStore', 'get', 1, 1, 1).
python_method('MemoryConversationStore', 'save', 2, 1, 0).
python_method('MemoryConversationStore', 'delete', 1, 1, 1).
python_method('MemoryConversationStore', 'count', 0, 1, 1).
python_class('nlp-service/app/store/redis_store.py', 'RedisConversationStore').
python_method('RedisConversationStore', '__init__', 2, 1, 1).
python_method('RedisConversationStore', '_key', 1, 1, 0).
python_method('RedisConversationStore', 'get', 1, 3, 4).
python_method('RedisConversationStore', 'save', 2, 1, 5).
python_method('RedisConversationStore', 'delete', 1, 1, 3).
python_method('RedisConversationStore', 'count', 0, 1, 1).
python_method('RedisConversationStore', 'close', 0, 1, 1).
python_class('nlp-service/tests/test_mapper.py', 'TestMapCompleteDSL').
python_method('TestMapCompleteDSL', 'test_map_complete_invoice', 0, 7, 5).
python_method('TestMapCompleteDSL', 'test_map_complete_email', 0, 4, 4).
python_class('nlp-service/tests/test_mapper.py', 'TestMapIncomplete').
python_method('TestMapIncomplete', 'test_map_incomplete_invoice', 0, 6, 6).
python_class('nlp-service/tests/test_mapper.py', 'TestMapComposite').
python_method('TestMapComposite', 'test_map_composite_report_email', 0, 6, 5).
python_class('nlp-service/tests/test_mapper.py', 'TestMapUnknown').
python_method('TestMapUnknown', 'test_map_unknown_intent', 0, 3, 4).
python_method('TestMapUnknown', 'test_map_nonexistent_intent', 0, 2, 4).
python_class('nlp-service/tests/test_mapper.py', 'TestMapDefaults').
python_method('TestMapDefaults', 'test_map_with_defaults', 0, 3, 5).
python_class('nlp-service/tests/test_mapper.py', 'TestMapTrigger').
python_method('TestMapTrigger', 'test_map_trigger_propagation', 0, 3, 4).
python_class('nlp-service/tests/test_mapper.py', 'TestMapSystemAction').
python_method('TestMapSystemAction', 'test_map_system_action_settings', 0, 2, 4).
python_class('nlp-service/tests/test_mapper.py', 'TestMapAllBusinessActions').
python_method('TestMapAllBusinessActions', 'test_map_all_business_actions', 1, 11, 6).
python_class('nlp-service/tests/test_mapper.py', 'TestResolveActions').
python_method('TestResolveActions', 'test_resolve_direct_action', 0, 2, 1).
python_method('TestResolveActions', 'test_resolve_composite_intent', 0, 3, 1).
python_method('TestResolveActions', 'test_resolve_dynamic_composite', 0, 3, 1).
python_method('TestResolveActions', 'test_resolve_unknown', 0, 2, 1).
python_class('nlp-service/tests/test_orchestrator.py', 'TestStartConversation').
python_method('TestStartConversation', 'test_start_conversation_complete', 0, 6, 2).
python_method('TestStartConversation', 'test_start_conversation_incomplete', 0, 4, 2).
python_method('TestStartConversation', 'test_start_conversation_unknown', 0, 3, 1).
python_class('nlp-service/tests/test_orchestrator.py', 'TestContinueConversation').
python_method('TestContinueConversation', 'test_continue_conversation', 0, 5, 2).
python_method('TestContinueConversation', 'test_continue_conversation_lazy_create', 0, 3, 1).
python_class('nlp-service/tests/test_orchestrator.py', 'TestSystemCommands').
python_method('TestSystemCommands', 'test_system_command_status', 0, 3, 1).
python_method('TestSystemCommands', 'test_system_command_settings', 0, 3, 2).
python_method('TestSystemCommands', 'test_format_system_file_list', 0, 2, 1).
python_method('TestSystemCommands', 'test_format_system_failed_result', 0, 2, 1).
python_class('nlp-service/tests/test_orchestrator.py', 'TestGetConversation').
python_method('TestGetConversation', 'test_get_conversation_exists', 0, 3, 2).
python_method('TestGetConversation', 'test_get_conversation_not_found', 0, 2, 1).
python_class('nlp-service/tests/test_orchestrator.py', 'TestGetActionForm').
python_method('TestGetActionForm', 'test_action_form_send_invoice', 0, 6, 1).
python_method('TestGetActionForm', 'test_action_form_nonexistent', 0, 2, 1).
python_class('nlp-service/tests/test_orchestrator.py', 'TestMergeIntoState').
python_method('TestMergeIntoState', 'test_merge_updates_intent', 0, 3, 5).
python_method('TestMergeIntoState', 'test_merge_preserves_existing', 0, 4, 5).
python_class('nlp-service/tests/test_parser_rules.py', 'TestParseInvoice').
python_method('TestParseInvoice', 'test_parse_invoice_simple', 0, 6, 1).
python_method('TestParseInvoice', 'test_parse_invoice_missing_data', 0, 4, 1).
python_method('TestParseInvoice', 'test_parse_invoice_eur', 0, 5, 1).
python_method('TestParseInvoice', 'test_parse_invoice_usd', 0, 5, 1).
python_class('nlp-service/tests/test_parser_rules.py', 'TestParseEmail').
python_method('TestParseEmail', 'test_parse_email', 0, 3, 1).
python_method('TestParseEmail', 'test_parse_email_english', 0, 3, 1).
python_class('nlp-service/tests/test_parser_rules.py', 'TestParseReport').
python_method('TestParseReport', 'test_parse_report_weekly', 0, 4, 1).
python_method('TestParseReport', 'test_parse_report_finance_csv', 0, 4, 1).
python_class('nlp-service/tests/test_parser_rules.py', 'TestParseComposite').
python_method('TestParseComposite', 'test_parse_composite_invoice_notify', 0, 4, 1).
python_method('TestParseComposite', 'test_parse_composite_full_flow', 0, 3, 1).
python_class('nlp-service/tests/test_parser_rules.py', 'TestParseSystem').
python_method('TestParseSystem', 'test_parse_system_settings', 0, 2, 1).
python_method('TestParseSystem', 'test_parse_system_file_list', 0, 2, 1).
python_method('TestParseSystem', 'test_parse_system_status', 0, 2, 1).
python_method('TestParseSystem', 'test_parse_system_help', 0, 2, 1).
python_method('TestParseSystem', 'test_parse_system_set_model', 0, 4, 1).
python_method('TestParseSystem', 'test_parse_system_set_mode', 0, 4, 1).
python_class('nlp-service/tests/test_parser_rules.py', 'TestParseUnknown').
python_method('TestParseUnknown', 'test_parse_unknown', 0, 3, 1).
python_class('nlp-service/tests/test_parser_rules.py', 'TestAmountExtraction').
python_method('TestAmountExtraction', 'test_parse_amount_extraction', 3, 3, 2).
python_class('nlp-service/tests/test_parser_rules.py', 'TestTriggerDetection').
python_method('TestTriggerDetection', 'test_parse_trigger_detection', 2, 2, 2).
python_class('nlp-service/tests/test_parser_rules.py', 'TestResultStructure').
python_method('TestResultStructure', 'test_result_is_nlp_result', 0, 5, 3).
python_method('TestResultStructure', 'test_raw_text_preserved', 0, 2, 1).
python_class('nlp-service/tests/test_registry.py', 'TestRegistryStructure').
python_method('TestRegistryStructure', 'test_registry_entry_has_required_keys', 1, 7, 4).
python_class('nlp-service/tests/test_registry.py', 'TestAliasResolution').
python_method('TestAliasResolution', 'test_alias_invoice_pl', 0, 2, 1).
python_method('TestAliasResolution', 'test_alias_email_en', 0, 2, 1).
python_method('TestAliasResolution', 'test_alias_report', 0, 2, 1).
python_method('TestAliasResolution', 'test_alias_slack', 0, 2, 1).
python_method('TestAliasResolution', 'test_alias_unknown', 0, 2, 1).
python_method('TestAliasResolution', 'test_alias_best_match', 0, 2, 1).
python_class('nlp-service/tests/test_registry.py', 'TestTriggerDetection').
python_method('TestTriggerDetection', 'test_trigger_daily', 0, 2, 1).
python_method('TestTriggerDetection', 'test_trigger_weekly', 0, 2, 1).
python_method('TestTriggerDetection', 'test_trigger_monthly', 0, 2, 1).
python_method('TestTriggerDetection', 'test_trigger_manual_default', 0, 2, 1).
python_class('nlp-service/tests/test_registry.py', 'TestHelperFunctions').
python_method('TestHelperFunctions', 'test_get_required_fields_invoice', 0, 3, 1).
python_method('TestHelperFunctions', 'test_get_required_fields_unknown', 0, 2, 1).
python_method('TestHelperFunctions', 'test_get_defaults_invoice', 0, 2, 2).
python_method('TestHelperFunctions', 'test_get_defaults_unknown', 0, 2, 1).
python_class('nlp-service/tests/test_registry.py', 'TestCategories').
python_method('TestCategories', 'test_system_actions_nonempty', 0, 2, 1).
python_method('TestCategories', 'test_business_actions_nonempty', 0, 2, 1).
python_method('TestCategories', 'test_no_overlap', 0, 5, 1).
python_method('TestCategories', 'test_union_is_complete', 0, 2, 2).
python_method('TestCategories', 'test_mullm_actions_loaded', 0, 3, 0).
python_class('nlp-service/tests/test_registry.py', 'TestCompositeIntents').
python_method('TestCompositeIntents', 'test_composite_actions_exist', 1, 3, 2).
python_class('nlp-service/tests/test_routing_resolve.py', 'TestParserSource').
python_method('TestParserSource', 'test_rules_mode', 1, 2, 2).
python_class('nlp-service/tests/test_routing_resolve.py', 'TestResolveIntent').
python_method('TestResolveIntent', 'test_invoice_rules_path', 0, 6, 2).
python_method('TestResolveIntent', 'test_unknown_intent', 0, 4, 1).
python_method('TestResolveIntent', 'test_native_file_list_route', 0, 4, 2).
python_method('TestResolveIntent', 'test_decision_serializable', 0, 4, 2).
python_class('nlp-service/tests/test_routing_resolve.py', 'TestOrchestratorRoutingField').
python_method('TestOrchestratorRoutingField', 'test_start_conversation_includes_routing', 1, 4, 4).
python_class('nlp-service/tests/test_store.py', 'TestMemoryStoreCRUD').
python_method('TestMemoryStoreCRUD', 'store', 0, 1, 1).
python_method('TestMemoryStoreCRUD', 'test_save_and_get', 1, 2, 2).
python_method('TestMemoryStoreCRUD', 'test_get_nonexistent', 1, 2, 1).
python_method('TestMemoryStoreCRUD', 'test_save_overwrites', 1, 2, 2).
python_method('TestMemoryStoreCRUD', 'test_delete', 1, 2, 3).
python_method('TestMemoryStoreCRUD', 'test_delete_nonexistent', 1, 1, 1).
python_method('TestMemoryStoreCRUD', 'test_count_empty', 1, 2, 1).
python_method('TestMemoryStoreCRUD', 'test_count_after_saves', 1, 2, 2).
python_method('TestMemoryStoreCRUD', 'test_count_after_delete', 1, 2, 3).
python_class('nlp-service/tests/test_store.py', 'TestSerializationRoundtrip').
python_method('TestSerializationRoundtrip', 'store', 0, 1, 1).
python_method('TestSerializationRoundtrip', 'test_conversation_state_roundtrip', 1, 7, 5).
python_method('TestSerializationRoundtrip', 'test_complex_entities_roundtrip', 1, 3, 2).
python_class('nlp-service/tests/test_store.py', 'TestStoreFactory').
python_method('TestStoreFactory', 'test_factory_returns_memory_without_redis', 1, 2, 3).
python_method('TestStoreFactory', 'test_factory_singleton', 1, 2, 2).
python_method('TestStoreFactory', 'test_factory_falls_back_on_bad_redis', 1, 2, 2).
python_class('nlp-service/tests/test_store.py', 'TestStoreIsolation').
python_method('TestStoreIsolation', 'test_separate_instances_isolated', 0, 4, 4).
python_class('nlp-service/tests/test_system_executor.py', 'TestSettingsGet').
python_method('TestSettingsGet', 'test_settings_get_all', 0, 5, 1).
python_method('TestSettingsGet', 'test_settings_get_section', 0, 3, 1).
python_method('TestSettingsGet', 'test_settings_get_default_is_all', 0, 2, 1).
python_class('nlp-service/tests/test_system_executor.py', 'TestSettingsSet').
python_method('TestSettingsSet', 'test_settings_set_and_verify', 0, 4, 2).
python_method('TestSettingsSet', 'test_settings_set_missing_path', 0, 2, 1).
python_method('TestSettingsSet', 'test_settings_set_missing_value', 0, 2, 1).
python_class('nlp-service/tests/test_system_executor.py', 'TestSettingsReset').
python_method('TestSettingsReset', 'test_settings_reset', 0, 4, 3).
python_method('TestSettingsReset', 'test_settings_reset_section', 0, 3, 3).
python_class('nlp-service/tests/test_system_executor.py', 'TestFileList').
python_method('TestFileList', 'test_file_list', 2, 5, 5).
python_method('TestFileList', 'test_file_list_nonexistent', 0, 2, 1).
python_class('nlp-service/tests/test_system_executor.py', 'TestRegistryList').
python_method('TestRegistryList', 'test_registry_list', 0, 5, 1).
python_method('TestRegistryList', 'test_registry_list_business', 0, 3, 2).
python_method('TestRegistryList', 'test_registry_list_system', 0, 3, 2).
python_class('nlp-service/tests/test_system_executor.py', 'TestRegistryAdd').
python_method('TestRegistryAdd', 'test_registry_add', 0, 3, 3).
python_method('TestRegistryAdd', 'test_registry_add_missing_name', 0, 2, 1).
python_method('TestRegistryAdd', 'test_registry_add_duplicate', 0, 2, 1).
python_class('nlp-service/tests/test_system_executor.py', 'TestStatus').
python_method('TestStatus', 'test_status', 0, 7, 1).
python_class('nlp-service/tests/test_system_executor.py', 'TestRegistryEdit').
python_method('TestRegistryEdit', 'test_registry_edit_description', 0, 3, 3).
python_method('TestRegistryEdit', 'test_registry_edit_nonexistent', 0, 2, 1).
python_class('nlp-service/tests/test_system_executor.py', 'TestFileRead').
python_method('TestFileRead', 'test_file_read_existing', 2, 4, 4).
python_method('TestFileRead', 'test_file_read_nonexistent', 2, 2, 3).
python_method('TestFileRead', 'test_file_read_no_path', 0, 2, 1).
python_class('nlp-service/tests/test_system_executor.py', 'TestFileWrite').
python_method('TestFileWrite', 'test_file_write_new', 2, 3, 5).
python_method('TestFileWrite', 'test_file_write_append', 2, 3, 6).
python_class('nlp-service/tests/test_system_executor.py', 'TestExecuteSystemAction').
python_method('TestExecuteSystemAction', 'test_execute_known_action', 0, 3, 1).
python_method('TestExecuteSystemAction', 'test_execute_unknown_action', 0, 2, 1).
python_class('nlp-service/tests/test_system_executor.py', 'TestFilePathValidation').
python_method('TestFilePathValidation', 'test_validate_allowed_path', 2, 2, 5).
python_method('TestFilePathValidation', 'test_validate_disallowed_path', 0, 1, 2).
python_method('TestFilePathValidation', 'test_is_read_only', 2, 3, 3).
python_class('nlp-service/tests/test_system_executor.py', 'TestExecutorMapping').
python_method('TestExecutorMapping', 'test_all_system_actions_have_executor', 0, 3, 2).
python_method('TestExecutorMapping', 'test_executors_count', 0, 2, 1).
python_class('nlp2dsl_sdk/client.py', 'NLP2DSLClient').
python_method('NLP2DSLClient', '__init__', 5, 2, 3).
python_method('NLP2DSLClient', 'from_env', 2, 1, 4).
python_method('NLP2DSLClient', 'close', 0, 2, 1).
python_method('NLP2DSLClient', '__enter__', 0, 1, 0).
python_method('NLP2DSLClient', '__exit__', 3, 1, 1).
python_method('NLP2DSLClient', '_request', 3, 1, 4).
python_method('NLP2DSLClient', '_backend', 2, 1, 1).
python_method('NLP2DSLClient', '_nlp_service', 2, 1, 1).
python_method('NLP2DSLClient', '_worker', 2, 1, 1).
python_method('NLP2DSLClient', 'backend_health', 0, 1, 2).
python_method('NLP2DSLClient', 'nlp_service_health', 0, 1, 2).
python_method('NLP2DSLClient', 'worker_health', 0, 1, 2).
python_method('NLP2DSLClient', 'health', 0, 1, 3).
python_method('NLP2DSLClient', 'workflow_from_text', 3, 1, 2).
python_method('NLP2DSLClient', 'run_workflow', 4, 3, 3).
python_method('NLP2DSLClient', 'workflow_actions', 0, 1, 2).
python_method('NLP2DSLClient', 'workflow_action_schema', 1, 2, 2).
python_method('NLP2DSLClient', 'settings', 0, 1, 2).
python_method('NLP2DSLClient', 'settings_section', 1, 1, 2).
python_method('NLP2DSLClient', 'update_settings_section', 2, 1, 3).
python_method('NLP2DSLClient', 'set_setting', 2, 1, 2).
python_method('NLP2DSLClient', 'reset_settings', 1, 2, 3).
python_method('NLP2DSLClient', 'chat_start', 2, 2, 4).
python_method('NLP2DSLClient', 'chat_message', 3, 2, 4).
python_method('NLP2DSLClient', 'chat_state', 1, 1, 2).
python_method('NLP2DSLClient', 'nlp_chat_start', 2, 2, 4).
python_method('NLP2DSLClient', 'nlp_chat_message', 3, 2, 4).
python_method('NLP2DSLClient', 'nlp_chat_state', 1, 1, 2).
python_method('NLP2DSLClient', 'generate_code', 4, 1, 2).
python_method('NLP2DSLClient', 'supported_languages', 0, 1, 2).
python_method('NLP2DSLClient', 'worker_execute', 3, 1, 3).
python_method('NLP2DSLClient', 'worker_generate_code', 5, 1, 1).
python_method('NLP2DSLClient', 'send_invoice', 5, 1, 2).
python_method('NLP2DSLClient', 'send_email', 5, 3, 2).
python_method('NLP2DSLClient', 'generate_report', 4, 1, 2).
python_method('NLP2DSLClient', 'generate_report_and_notify', 7, 4, 3).
python_method('NLP2DSLClient', 'create_scheduled_report', 7, 1, 1).
python_method('NLP2DSLClient', 'notify_slack', 4, 2, 2).
python_method('NLP2DSLClient', 'crm_update', 4, 2, 3).
python_method('NLP2DSLClient', 'send_invoice_and_notify', 7, 4, 3).
python_class('nlp2dsl_sdk/client.py', 'ConversationFlow').
python_method('ConversationFlow', '__init__', 1, 2, 1).
python_method('ConversationFlow', 'start', 2, 1, 4).
python_method('ConversationFlow', 'send_message', 2, 2, 5).
python_method('ConversationFlow', '_handle_response', 1, 5, 6).
python_method('ConversationFlow', '_handle_in_progress_response', 2, 6, 3).
python_method('ConversationFlow', '_handle_ready_response', 2, 4, 5).
python_method('ConversationFlow', '_handle_completed_response', 2, 4, 2).
python_method('ConversationFlow', '_handle_error_response', 1, 1, 1).
python_method('ConversationFlow', 'run_demo', 0, 2, 5).
python_method('ConversationFlow', 'run_interactive', 0, 6, 6).
python_class('nlp2dsl_sdk/demos.py', 'DemoSpec').
python_class('tests/test_nlp2dsl_sdk.py', 'DummyResponse').
python_method('DummyResponse', '__init__', 2, 1, 1).
python_method('DummyResponse', 'raise_for_status', 0, 2, 1).
python_method('DummyResponse', 'json', 0, 1, 0).
python_class('tests/test_nlp2dsl_sdk.py', 'DummySession').
python_method('DummySession', '__init__', 1, 1, 1).
python_method('DummySession', 'request', 2, 2, 3).
python_method('DummySession', 'close', 0, 1, 0).
python_class('worker/config.py', 'WorkerSettings').
python_class('worker/logging_setup.py', 'JSONFormatter').
python_method('JSONFormatter', '__init__', 1, 1, 2).
python_method('JSONFormatter', 'format', 1, 2, 6).
python_class('worker/logging_setup.py', 'RequestIDMiddleware').
python_method('RequestIDMiddleware', '__init__', 2, 1, 2).
python_method('RequestIDMiddleware', 'dispatch', 2, 2, 5).
python_class('worker/tests/test_worker.py', 'TestWorkerHealth').
python_method('TestWorkerHealth', 'test_health', 1, 6, 3).
python_class('worker/tests/test_worker.py', 'TestExecuteActions').
python_method('TestExecuteActions', 'test_execute_send_invoice', 1, 5, 2).
python_method('TestExecuteActions', 'test_execute_send_email', 1, 4, 2).
python_method('TestExecuteActions', 'test_execute_generate_report', 1, 4, 2).
python_method('TestExecuteActions', 'test_execute_notify_slack', 1, 4, 2).
python_method('TestExecuteActions', 'test_execute_notify_telegram', 1, 4, 2).
python_method('TestExecuteActions', 'test_execute_notify_teams', 1, 4, 2).
python_method('TestExecuteActions', 'test_execute_unknown_action', 1, 3, 2).
python_class('worker/tests/test_worker.py', 'TestActionRegistry').
python_method('TestActionRegistry', 'test_handlers_registered', 0, 2, 1).
python_method('TestActionRegistry', 'test_all_handlers_callable', 0, 3, 2).

% ── Dependencies ─────────────────────────────────────────

% ── Makefile Targets ─────────────────────────────────────

% ── Taskfile Tasks ───────────────────────────────────────

% ── Environment Variables ────────────────────────────────
env_variable('OPENROUTER_API_KEY', '*(not set)*', '── OpenRouter (domyślny) ────────────────────────────────────').
env_variable('LLM_MODEL', 'openrouter/openai/gpt-5-mini', '').
env_variable('LLM_TEMPERATURE', '0', '── LLM Settings ─────────────────────────────────────────────').
env_variable('LLM_MAX_TOKENS', '1024', '').
env_variable('LLM_FALLBACK_THRESHOLD', '0.5', '').
env_variable('NLP2DSL_BACKEND_HOST_PORT', '8010', '8002 jest zajęty przez Mullm Projector, gdy oba stacki działają równolegle.').
env_variable('NLP2DSL_NLP_HOST_PORT', '8012', '').
env_variable('NLP2DSL_WORKER_HOST_PORT', '8004', '').
env_variable('NLP2DSL_CONFIG', './nlp2dsl.yaml', '').
env_variable('NLP2DSL_AGENT_ID', 'user', '').
env_variable('DEEPGRAM_API_KEY', '*(not set)*', 'Zdobądź klucz: https://console.deepgram.com/').

% ── TestQL Scenarios ─────────────────────────────────────
testql_scenario('generated-api-smoke.testql.toon.yaml', 'api').
testql_scenario('generated-cli-tests.testql.toon.yaml', 'cli').
testql_scenario('generated-from-pytests.testql.toon.yaml', 'integration').

% ── Semantic Facts from SUMD.md ──────────────────────────
sumd_declared_file('app.doql.less', 'doql').
sumd_declared_file('testql-scenarios/generated-api-smoke.testql.toon.yaml', 'testql').
sumd_declared_file('testql-scenarios/generated-cli-tests.testql.toon.yaml', 'testql').
sumd_declared_file('testql-scenarios/generated-from-pytests.testql.toon.yaml', 'testql').
sumd_declared_file('pyqual.yaml', 'pyqual').
sumd_declared_file('project/map.toon.yaml', 'analysis').
sumd_declared_file('project/logic.pl', 'analysis').
sumd_declared_file('project/calls.toon.yaml', 'analysis').
sumd_interface('api', '').
sumd_interface('cli', 'argparse').
sumd_interface('cli', '').
sumd_deploy_target('docker_compose').
sumd_deploy_compose_file('docker-compose.yml').
```

## Call Graph

*217 nodes · 234 edges · 41 modules · CC̄=2.9*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `_execute_workflow` *(in backend.app.engine)* | 11 ⚠ | 2 | 42 | **44** |
| `_actions_from_yaml_areas` *(in nlp-service.app.governance.bootstrap)* | 14 ⚠ | 1 | 26 | **27** |
| `websocket_chat` *(in nlp-service.app.main)* | 10 ⚠ | 0 | 23 | **23** |
| `resolve_intent` *(in nlp-service.app.routing.resolve)* | 12 ⚠ | 1 | 22 | **23** |
| `stream_workflow` *(in backend.app.routers.workflow)* | 2 | 0 | 22 | **22** |
| `chat_message` *(in backend.app.routers.chat)* | 12 ⚠ | 0 | 21 | **21** |
| `map_to_dsl` *(in nlp-service.app.mapper)* | 8 | 3 | 17 | **20** |
| `parse_llm` *(in nlp-service.app.parser_llm)* | 3 | 4 | 16 | **20** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/wronai/nlp2dsl
# generated in 0.15s
# nodes: 217 | edges: 234 | modules: 41
# CC̄=2.9

HUBS[20]:
  backend.app.engine._execute_workflow
    CC=11  in:2  out:42  total:44
  nlp-service.app.governance.bootstrap._actions_from_yaml_areas
    CC=14  in:1  out:26  total:27
  nlp-service.app.main.websocket_chat
    CC=10  in:0  out:23  total:23
  nlp-service.app.routing.resolve.resolve_intent
    CC=12  in:1  out:22  total:23
  backend.app.routers.workflow.stream_workflow
    CC=2  in:0  out:22  total:22
  backend.app.routers.chat.chat_message
    CC=12  in:0  out:21  total:21
  nlp-service.app.mapper.map_to_dsl
    CC=8  in:3  out:17  total:20
  nlp-service.app.parser_llm.parse_llm
    CC=3  in:4  out:16  total:20
  nlp2dsl_sdk.demos._print_workflow_preview
    CC=4  in:3  out:16  total:19
  nlp2dsl_sdk.demos.run_action_catalog_demo
    CC=6  in:0  out:19  total:19
  nlp-service.app.governance.config._build_access_config
    CC=7  in:1  out:18  total:19
  worker.worker._deliver_notification
    CC=5  in:3  out:16  total:19
  nlp-service.app.audio_parser.stt_audio
    CC=9  in:5  out:14  total:19
  nlp-service.app.settings.SettingsManager.set
    CC=4  in:7  out:11  total:18
  nlp-service.app.conversation.orchestrator._process_message
    CC=6  in:2  out:16  total:18
  backend.app.routers.chat._proxy_chat_payload
    CC=9  in:2  out:16  total:18
  nlp-service.app.governance.config._search_paths
    CC=6  in:1  out:17  total:18
  nlp-service.app.system_executor._exec_file_read
    CC=9  in:0  out:18  total:18
  nlp2dsl_sdk.demos._print_execution_result
    CC=5  in:7  out:11  total:18
  worker.worker.handle_generate_code
    CC=5  in:0  out:17  total:17

MODULES:
  backend.app.engine  [7 funcs]
    _execute_workflow  CC=11  out:42
    _persist_workflow_snapshot  CC=2  out:2
    _publish_workflow_event  CC=2  out:2
    _track_background_task  CC=1  out:5
    _workflow_steps_payload  CC=2  out:1
    run_workflow  CC=1  out:2
    start_workflow  CC=1  out:7
  backend.app.logging_setup  [1 funcs]
    get_request_id  CC=1  out:1
  backend.app.routers.chat  [4 funcs]
    _proxy_chat_payload  CC=9  out:16
    chat_get_state  CC=2  out:7
    chat_message  CC=12  out:21
    chat_start  CC=2  out:4
  backend.app.routers.settings  [7 funcs]
    action_schema  CC=2  out:6
    actions_schema  CC=1  out:5
    get_settings  CC=1  out:5
    get_settings_section  CC=2  out:6
    reset_settings  CC=1  out:5
    set_setting  CC=2  out:6
    update_settings_section  CC=2  out:6
  backend.app.routers.system  [1 funcs]
    system_execute  CC=2  out:6
  backend.app.routers.workflow  [5 funcs]
    _format_sse  CC=5  out:6
    _workflow_snapshot  CC=1  out:7
    run_workflow_endpoint  CC=1  out:2
    start_workflow_endpoint  CC=1  out:2
    stream_workflow  CC=2  out:22
  backend.app.workflow_events  [2 funcs]
    publish  CC=2  out:4
    subscriber_count  CC=1  out:3
  examples.01-invoice.main  [1 funcs]
    main  CC=1  out:1
  examples.02-email.main  [1 funcs]
    main  CC=1  out:1
  examples.03-report-and-notify.main  [1 funcs]
    main  CC=1  out:1
  examples.04-scheduled-report.main  [1 funcs]
    main  CC=1  out:1
  examples.code_generation_examples  [1 funcs]
    main  CC=1  out:1
  nlp-service.app.access.uri_match  [3 funcs]
    normalize_uri  CC=2  out:1
    scheme_allowed  CC=5  out:2
    uri_matches  CC=8  out:11
  nlp-service.app.audio_parser  [4 funcs]
    send_audio  CC=2  out:2
    is_stt_available  CC=2  out:0
    stt_audio  CC=9  out:14
    stt_file  CC=2  out:4
  nlp-service.app.conversation.merge  [1 funcs]
    merge_into_state  CC=9  out:4
  nlp-service.app.conversation.orchestrator  [5 funcs]
    _attach_routing  CC=1  out:1
    _process_message  CC=6  out:16
    continue_conversation  CC=2  out:8
    get_conversation  CC=2  out:2
    start_conversation  CC=1  out:6
  nlp-service.app.conversation.responses  [9 funcs]
    _is_execute_or_continue  CC=2  out:3
    _nlp_from_state  CC=5  out:5
    build_and_check_dsl  CC=4  out:6
    build_incomplete_response  CC=3  out:6
    check_execute_keyword  CC=7  out:5
    deny_message  CC=3  out:0
    format_system_result  CC=3  out:6
    handle_system_action  CC=7  out:7
    handle_unknown_intent  CC=5  out:6
  nlp-service.app.dsl.forms  [1 funcs]
    get_action_form  CC=5  out:12
  nlp-service.app.execution.delegate  [2 funcs]
    execution_backend_for_intent  CC=2  out:1
    is_delegated_to_mullm  CC=2  out:1
  nlp-service.app.governance.bootstrap  [3 funcs]
    _actions_from_yaml_areas  CC=14  out:26
    apply_yaml_actions  CC=4  out:6
    bootstrap_registry  CC=1  out:7
  nlp-service.app.governance.config  [11 funcs]
    _allowed_uri_schemes  CC=3  out:2
    _build_access_config  CC=7  out:18
    _default_agent  CC=3  out:3
    _enabled_integrations  CC=7  out:5
    _load_merged_config  CC=4  out:7
    _load_yaml_file  CC=3  out:4
    _merge_dict  CC=8  out:6
    _search_paths  CC=6  out:17
    get_access_config  CC=1  out:1
    load_access_config  CC=3  out:2
  nlp-service.app.governance.policy  [13 funcs]
    _action_context  CC=5  out:5
    _area_selector_match  CC=3  out:0
    _decision  CC=1  out:1
    _effect_decision  CC=4  out:4
    _grant_action_matches  CC=4  out:4
    _grant_matches  CC=2  out:2
    _grant_target_matches  CC=5  out:6
    _matched_effect  CC=3  out:4
    _scheme_decision  CC=3  out:2
    _unknown_agent_decision  CC=4  out:3
  nlp-service.app.main  [14 funcs]
    _run_parser  CC=7  out:9
    access_check  CC=3  out:6
    access_config  CC=3  out:12
    access_reload  CC=2  out:2
    action_schema  CC=2  out:3
    actions_schema  CC=3  out:3
    chat_message  CC=5  out:13
    chat_start  CC=5  out:12
    chat_state  CC=2  out:4
    health  CC=3  out:8
  nlp-service.app.mapper  [5 funcs]
    _build_config  CC=6  out:10
    _get_field_mapping  CC=1  out:1
    _make_name  CC=3  out:2
    _resolve_actions  CC=7  out:4
    map_to_dsl  CC=8  out:17
  nlp-service.app.parser_llm  [3 funcs]
    _detect_provider  CC=10  out:8
    _parse_json_response  CC=6  out:10
    parse_llm  CC=3  out:16
  nlp-service.app.registry  [3 funcs]
    get_defaults  CC=1  out:3
    get_required_fields  CC=1  out:2
    get_trigger  CC=3  out:2
  nlp-service.app.routing.native  [13 funcs]
    _aliases_match  CC=2  out:3
    _best_action_alias  CC=3  out:3
    _best_alias_for_action  CC=6  out:5
    _keywords_pattern_matches  CC=4  out:5
    _match_route  CC=4  out:6
    _pattern_matches  CC=4  out:5
    _patterns_match  CC=3  out:3
    _regex_pattern_matches  CC=4  out:4
    _resolve_action_alias  CC=2  out:6
    _resolve_configured_route  CC=5  out:5
  nlp-service.app.routing.observability  [2 funcs]
    record_intent_decision  CC=7  out:4
    routing_metrics_snapshot  CC=1  out:1
  nlp-service.app.routing.parser.facade  [1 funcs]
    parse_text  CC=8  out:8
  nlp-service.app.routing.parser.rules  [25 funcs]
    _action_alias_scores  CC=4  out:3
    _action_category  CC=1  out:2
    _actions_by_score  CC=1  out:2
    _detect_actions  CC=3  out:3
    _dominant_overlap_action  CC=4  out:5
    _extract_amount  CC=5  out:7
    _extract_email  CC=2  out:2
    _extract_entities  CC=1  out:9
    _extract_fallback_recipient  CC=7  out:5
    _extract_file_path_entity  CC=3  out:2
  nlp-service.app.routing.resolve  [4 funcs]
    _intent_from_native  CC=3  out:8
    _intent_from_nlp  CC=2  out:7
    _parser_source  CC=5  out:4
    resolve_intent  CC=12  out:22
  nlp-service.app.settings  [2 funcs]
    set  CC=4  out:11
    _coerce_type  CC=5  out:6
  nlp-service.app.store.factory  [1 funcs]
    get_conversation_store  CC=4  out:7
  nlp-service.app.system_executor  [5 funcs]
    _exec_file_read  CC=9  out:18
    _exec_file_write  CC=4  out:12
    _is_read_only  CC=2  out:5
    _validate_file_path  CC=5  out:9
    execute_system_action  CC=3  out:5
  nlp-service.integrations.loader  [3 funcs]
    _integration_names  CC=5  out:6
    apply_integrations  CC=5  out:7
    load_integration_registries  CC=5  out:10
  nlp2dsl_sdk.__main__  [1 funcs]
    main  CC=5  out:9
  nlp2dsl_sdk.client  [8 funcs]
    crm_update  CC=2  out:3
    generate_report  CC=1  out:2
    generate_report_and_notify  CC=4  out:6
    notify_slack  CC=2  out:2
    send_email  CC=3  out:2
    send_invoice  CC=1  out:2
    send_invoice_and_notify  CC=4  out:6
    workflow_step  CC=1  out:1
  nlp2dsl_sdk.demos  [21 funcs]
    _ensure_services  CC=2  out:2
    _get_supported_languages  CC=3  out:6
    _preview_text_examples  CC=3  out:6
    _print_code_generation_preview  CC=3  out:11
    _print_execution_result  CC=5  out:11
    _print_json  CC=1  out:2
    _print_workflow_preview  CC=4  out:16
    _run_conversation_code_example  CC=3  out:14
    _run_direct_code_generation  CC=5  out:9
    _run_gallery_examples  CC=5  out:14
  tauri-wrapper.scripts.dev  [3 funcs]
    exitCode  CC=2  out:1
    main  CC=11  out:10
    shutdown  CC=5  out:5
  tauri-wrapper.scripts.serve-dist  [9 funcs]
    contentType  CC=2  out:3
    fileContents  CC=1  out:2
    handleRequest  CC=6  out:6
    isInsideRoot  CC=3  out:3
    resolveRequestPath  CC=8  out:8
    sendFile  CC=1  out:4
    server  CC=4  out:5
    startServer  CC=4  out:10
    stat  CC=2  out:2
  worker.worker  [10 funcs]
    _deliver_notification  CC=5  out:16
    action  CC=1  out:0
    handle_crm_update  CC=1  out:5
    handle_generate_code  CC=5  out:17
    handle_generate_report  CC=1  out:9
    handle_notify_slack  CC=1  out:5
    handle_notify_teams  CC=1  out:6
    handle_notify_telegram  CC=1  out:5
    handle_send_email  CC=1  out:8
    handle_send_invoice  CC=1  out:9

EDGES:
  tauri-wrapper.scripts.dev.main → tauri-wrapper.scripts.dev.shutdown
  tauri-wrapper.scripts.dev.exitCode → tauri-wrapper.scripts.dev.main
  tauri-wrapper.scripts.serve-dist.resolveRequestPath → tauri-wrapper.scripts.serve-dist.isInsideRoot
  tauri-wrapper.scripts.serve-dist.resolveRequestPath → tauri-wrapper.scripts.serve-dist.stat
  tauri-wrapper.scripts.serve-dist.sendFile → tauri-wrapper.scripts.serve-dist.contentType
  tauri-wrapper.scripts.serve-dist.fileContents → tauri-wrapper.scripts.serve-dist.contentType
  tauri-wrapper.scripts.serve-dist.handleRequest → tauri-wrapper.scripts.serve-dist.resolveRequestPath
  tauri-wrapper.scripts.serve-dist.handleRequest → tauri-wrapper.scripts.serve-dist.contentType
  tauri-wrapper.scripts.serve-dist.handleRequest → tauri-wrapper.scripts.serve-dist.sendFile
  tauri-wrapper.scripts.serve-dist.startServer → tauri-wrapper.scripts.serve-dist.handleRequest
  tauri-wrapper.scripts.serve-dist.server → tauri-wrapper.scripts.serve-dist.handleRequest
  backend.app.engine._persist_workflow_snapshot → backend.app.engine._workflow_steps_payload
  backend.app.engine._execute_workflow → backend.app.engine._publish_workflow_event
  backend.app.engine._execute_workflow → backend.app.logging_setup.get_request_id
  backend.app.engine._execute_workflow → backend.app.engine._persist_workflow_snapshot
  backend.app.engine.run_workflow → backend.app.engine._execute_workflow
  backend.app.engine.start_workflow → backend.app.engine._track_background_task
  backend.app.engine.start_workflow → backend.app.engine._persist_workflow_snapshot
  backend.app.engine.start_workflow → backend.app.engine._execute_workflow
  backend.app.workflow_events.WorkflowEventHub.publish → nlp-service.app.settings.SettingsManager.set
  backend.app.workflow_events.WorkflowEventHub.subscriber_count → nlp-service.app.settings.SettingsManager.set
  backend.app.routers.system.system_execute → backend.app.logging_setup.get_request_id
  backend.app.routers.chat.chat_start → backend.app.routers.chat._proxy_chat_payload
  backend.app.routers.chat.chat_message → backend.app.routers.chat._proxy_chat_payload
  backend.app.routers.chat.chat_get_state → backend.app.logging_setup.get_request_id
  backend.app.routers.workflow.run_workflow_endpoint → backend.app.engine.run_workflow
  backend.app.routers.workflow.start_workflow_endpoint → backend.app.engine.start_workflow
  backend.app.routers.workflow.stream_workflow → backend.app.routers.workflow._workflow_snapshot
  backend.app.routers.workflow.stream_workflow → backend.app.routers.workflow._format_sse
  backend.app.routers.settings.actions_schema → backend.app.logging_setup.get_request_id
  backend.app.routers.settings.action_schema → backend.app.logging_setup.get_request_id
  backend.app.routers.settings.get_settings → backend.app.logging_setup.get_request_id
  backend.app.routers.settings.get_settings_section → backend.app.logging_setup.get_request_id
  backend.app.routers.settings.update_settings_section → backend.app.logging_setup.get_request_id
  backend.app.routers.settings.set_setting → backend.app.logging_setup.get_request_id
  backend.app.routers.settings.reset_settings → backend.app.logging_setup.get_request_id
  nlp2dsl_sdk.demos._print_workflow_preview → nlp2dsl_sdk.demos._print_json
  nlp2dsl_sdk.demos._print_execution_result → nlp2dsl_sdk.demos._print_json
  nlp2dsl_sdk.demos._preview_text_examples → nlp2dsl_sdk.demos._print_workflow_preview
  nlp2dsl_sdk.demos.run_crm_update_demo → nlp2dsl_sdk.demos._preview_text_examples
  nlp2dsl_sdk.demos.run_crm_update_demo → nlp2dsl_sdk.demos._print_execution_result
  nlp2dsl_sdk.demos.run_crm_update_demo → nlp2dsl_sdk.demos._ensure_services
  nlp2dsl_sdk.demos.run_action_catalog_demo → nlp2dsl_sdk.demos._ensure_services
  nlp2dsl_sdk.demos.run_automation_gallery_demo → nlp2dsl_sdk.demos._run_gallery_examples
  nlp2dsl_sdk.demos.run_automation_gallery_demo → nlp2dsl_sdk.demos._ensure_services
  nlp2dsl_sdk.demos._run_workflow_examples → nlp2dsl_sdk.demos._print_execution_result
  nlp2dsl_sdk.demos._run_gallery_examples → nlp2dsl_sdk.demos._print_workflow_preview
  nlp2dsl_sdk.demos.run_invoice_demo → nlp2dsl_sdk.demos._preview_text_examples
  nlp2dsl_sdk.demos.run_invoice_demo → nlp2dsl_sdk.demos._print_execution_result
  nlp2dsl_sdk.demos.run_invoice_demo → nlp2dsl_sdk.demos._ensure_services
```

## Test Contracts

*Scenarios as contract signatures — what the system guarantees.*

### Api (1)

**`Auto-generated API Smoke Tests`**
- assert `_status < 500`
- assert `_status >= 200`
- detectors: FastAPIDetector, WebSocketDetector, ConfigEndpointDetector

### Cli (1)

**`CLI Command Tests`**

### Integration (1)

**`Auto-generated from Python Tests`**

## Intent

Reusable Python SDK for the NLP2DSL platform
