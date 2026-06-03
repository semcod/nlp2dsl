# MVP Automation Platform

SUMD - Structured Unified Markdown Descriptor for AI-aware project refactorization

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Quality Pipeline (`pyqual.yaml`)](#quality-pipeline-pyqualyaml)
- [Dependencies](#dependencies)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Refactoring Analysis](#refactoring-analysis)
- [Intent](#intent)

## Metadata

- **name**: `nlp2dsl`
- **version**: `0.0.7`
- **python_requires**: `>=3.10`
- **ai_model**: `openrouter/qwen/qwen3-coder-next`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, testql(3), app.doql.less, pyqual.yaml, goal.yaml, .env.example, docker-compose.yml, project/(6 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.less`)

```less markpact:doql path=app.doql.less
// LESS format — define @variables here as needed

app {
  name: nlp2dsl;
  version: 0.0.7;
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

## Dependencies

### Runtime

```text markpact:deps python
requests>=2.31.0
```

## Call Graph

*108 nodes · 110 edges · 26 modules · CC̄=2.9*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `run_code_generation_demo` *(in nlp2dsl_sdk.demos)* | 20 ⚠ | 1 | 51 | **52** |
| `_execute_workflow` *(in backend.app.engine)* | 11 ⚠ | 2 | 42 | **44** |
| `_extract_entities` *(in nlp-service.app.parser_rules)* | 40 ⚠ | 1 | 36 | **37** |
| `_process_message` *(in nlp-service.app.orchestrator)* | 21 ⚠ | 2 | 30 | **32** |
| `stream_workflow` *(in backend.app.routers.workflow)* | 2 | 0 | 22 | **22** |
| `run_action_catalog_demo` *(in nlp2dsl_sdk.demos)* | 6 | 0 | 19 | **19** |
| `_deliver_notification` *(in worker.worker)* | 5 | 3 | 16 | **19** |
| `_print_workflow_preview` *(in nlp2dsl_sdk.demos)* | 4 | 3 | 16 | **19** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/wronai/nlp2dsl
# generated in 0.07s
# nodes: 108 | edges: 110 | modules: 26
# CC̄=2.9

HUBS[20]:
  nlp2dsl_sdk.demos.run_code_generation_demo
    CC=20  in:1  out:51  total:52
  backend.app.engine._execute_workflow
    CC=11  in:2  out:42  total:44
  nlp-service.app.parser_rules._extract_entities
    CC=40  in:1  out:36  total:37
  nlp-service.app.orchestrator._process_message
    CC=21  in:2  out:30  total:32
  backend.app.routers.workflow.stream_workflow
    CC=2  in:0  out:22  total:22
  nlp2dsl_sdk.demos.run_action_catalog_demo
    CC=6  in:0  out:19  total:19
  worker.worker._deliver_notification
    CC=5  in:3  out:16  total:19
  nlp2dsl_sdk.demos._print_workflow_preview
    CC=4  in:3  out:16  total:19
  backend.app.routers.chat._proxy_chat_payload
    CC=9  in:2  out:16  total:18
  nlp2dsl_sdk.demos._print_execution_result
    CC=5  in:7  out:11  total:18
  nlp-service.app.mapper.map_to_dsl
    CC=8  in:1  out:17  total:18
  nlp-service.app.system_executor._exec_file_read
    CC=9  in:0  out:18  total:18
  worker.worker.handle_generate_code
    CC=5  in:0  out:17  total:17
  backend.app.routers.chat.chat_message
    CC=7  in:0  out:17  total:17
  nlp-service.app.parser_llm.parse_llm
    CC=3  in:0  out:16  total:16
  nlp-service.app.audio_parser.stt_audio
    CC=9  in:2  out:14  total:16
  nlp2dsl_sdk.demos._run_gallery_examples
    CC=5  in:1  out:14  total:15
  nlp2dsl_sdk.demos.run_email_demo
    CC=5  in:1  out:14  total:15
  nlp-service.app.settings.SettingsManager.set
    CC=4  in:4  out:11  total:15
  nlp2dsl_sdk.demos.run_invoice_demo
    CC=5  in:1  out:14  total:15

MODULES:
  backend.app.engine  [7 funcs]
    _execute_workflow  CC=11  out:42
    _persist_workflow_snapshot  CC=2  out:2
    _publish_workflow_event  CC=2  out:2
    _track_background_task  CC=1  out:5
    _workflow_steps_payload  CC=2  out:1
    run_workflow  CC=1  out:2
    start_workflow  CC=1  out:7
  backend.app.routers.chat  [4 funcs]
    _proxy_chat_payload  CC=9  out:16
    chat_get_state  CC=2  out:7
    chat_message  CC=7  out:17
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
  nlp-service.app.audio_parser  [3 funcs]
    send_audio  CC=2  out:2
    stt_audio  CC=9  out:14
    stt_file  CC=2  out:4
  nlp-service.app.logging_setup  [1 funcs]
    get_request_id  CC=1  out:1
  nlp-service.app.mapper  [5 funcs]
    _build_config  CC=6  out:10
    _get_field_mapping  CC=1  out:1
    _make_name  CC=3  out:2
    _resolve_actions  CC=7  out:4
    map_to_dsl  CC=8  out:17
  nlp-service.app.orchestrator  [4 funcs]
    _merge_into_state  CC=9  out:4
    _process_message  CC=21  out:30
    continue_conversation  CC=2  out:8
    start_conversation  CC=1  out:6
  nlp-service.app.parser_llm  [3 funcs]
    _detect_provider  CC=10  out:8
    _parse_json_response  CC=6  out:10
    parse_llm  CC=3  out:16
  nlp-service.app.parser_rules  [4 funcs]
    _detect_actions  CC=10  out:9
    _extract_entities  CC=40  out:36
    _resolve_intent  CC=5  out:6
    parse_rules  CC=5  out:10
  nlp-service.app.registry  [3 funcs]
    get_defaults  CC=1  out:3
    get_required_fields  CC=1  out:2
    get_trigger  CC=3  out:2
  nlp-service.app.settings  [2 funcs]
    set  CC=4  out:11
    _coerce_type  CC=5  out:6
  nlp-service.app.system_executor  [4 funcs]
    _exec_file_read  CC=9  out:18
    _exec_file_write  CC=4  out:12
    _is_read_only  CC=2  out:5
    _validate_file_path  CC=5  out:9
  nlp2dsl_sdk.__main__  [1 funcs]
    main  CC=5  out:9
  nlp2dsl_sdk.client  [9 funcs]
    crm_update  CC=2  out:3
    generate_report  CC=1  out:2
    generate_report_and_notify  CC=4  out:6
    notify_slack  CC=2  out:2
    run_workflow  CC=3  out:3
    send_email  CC=3  out:2
    send_invoice  CC=1  out:2
    send_invoice_and_notify  CC=4  out:6
    workflow_step  CC=1  out:1
  nlp2dsl_sdk.demos  [16 funcs]
    _ensure_services  CC=2  out:2
    _preview_text_examples  CC=3  out:6
    _print_execution_result  CC=5  out:11
    _print_json  CC=1  out:2
    _print_workflow_preview  CC=4  out:16
    _run_gallery_examples  CC=5  out:14
    _run_workflow_examples  CC=3  out:4
    list_available_demos  CC=1  out:0
    run_action_catalog_demo  CC=6  out:19
    run_automation_gallery_demo  CC=3  out:4
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
  backend.app.routers.settings.actions_schema → nlp-service.app.logging_setup.get_request_id
  backend.app.routers.settings.action_schema → nlp-service.app.logging_setup.get_request_id
  backend.app.routers.settings.get_settings → nlp-service.app.logging_setup.get_request_id
  backend.app.routers.settings.get_settings_section → nlp-service.app.logging_setup.get_request_id
  backend.app.routers.settings.update_settings_section → nlp-service.app.logging_setup.get_request_id
  backend.app.routers.settings.set_setting → nlp-service.app.logging_setup.get_request_id
  backend.app.routers.settings.reset_settings → nlp-service.app.logging_setup.get_request_id
  nlp2dsl_sdk.__main__.main → nlp2dsl_sdk.demos.list_available_demos
  nlp2dsl_sdk.client.NLP2DSLClient.send_invoice → nlp2dsl_sdk.client.workflow_step
  nlp2dsl_sdk.client.NLP2DSLClient.send_email → nlp2dsl_sdk.client.workflow_step
  nlp2dsl_sdk.client.NLP2DSLClient.generate_report → nlp2dsl_sdk.client.workflow_step
  nlp2dsl_sdk.client.NLP2DSLClient.generate_report_and_notify → nlp2dsl_sdk.client.workflow_step
  nlp2dsl_sdk.client.NLP2DSLClient.notify_slack → nlp2dsl_sdk.client.workflow_step
  nlp2dsl_sdk.client.NLP2DSLClient.crm_update → nlp2dsl_sdk.client.workflow_step
  nlp2dsl_sdk.client.NLP2DSLClient.send_invoice_and_notify → nlp2dsl_sdk.client.workflow_step
  backend.app.routers.system.system_execute → nlp-service.app.logging_setup.get_request_id
  backend.app.routers.workflow.run_workflow_endpoint → nlp2dsl_sdk.client.NLP2DSLClient.run_workflow
  backend.app.routers.workflow.start_workflow_endpoint → backend.app.engine.start_workflow
  backend.app.routers.workflow.stream_workflow → backend.app.routers.workflow._workflow_snapshot
  backend.app.routers.workflow.stream_workflow → backend.app.routers.workflow._format_sse
  nlp-service.app.audio_parser.stt_file → nlp-service.app.audio_parser.stt_audio
  nlp-service.app.audio_parser.StreamingSTT.send_audio → nlp-service.app.audio_parser.stt_audio
  examples.code_generation_examples.main → nlp2dsl_sdk.demos.run_code_generation_demo
  examples.01-invoice.main.main → nlp2dsl_sdk.demos.run_invoice_demo
  nlp-service.app.parser_rules.parse_rules → nlp-service.app.parser_rules._detect_actions
  nlp-service.app.parser_rules.parse_rules → nlp-service.app.parser_rules._resolve_intent
  nlp-service.app.parser_rules.parse_rules → nlp-service.app.parser_rules._extract_entities
  nlp-service.app.parser_rules.parse_rules → nlp-service.app.registry.get_trigger
  nlp-service.app.parser_rules._resolve_intent → nlp-service.app.settings.SettingsManager.set
  examples.02-email.main.main → nlp2dsl_sdk.demos.run_email_demo
  nlp-service.app.mapper.map_to_dsl → nlp-service.app.mapper._resolve_actions
  nlp-service.app.mapper.map_to_dsl → nlp-service.app.mapper._make_name
  nlp-service.app.mapper.map_to_dsl → nlp-service.app.mapper._build_config
  nlp-service.app.mapper.map_to_dsl → nlp-service.app.registry.get_trigger
  nlp-service.app.mapper._build_config → nlp-service.app.registry.get_required_fields
  nlp-service.app.mapper._build_config → nlp-service.app.registry.get_defaults
  nlp-service.app.mapper._build_config → nlp-service.app.mapper._get_field_mapping
  nlp-service.app.orchestrator.start_conversation → nlp-service.app.orchestrator._process_message
  nlp-service.app.orchestrator.continue_conversation → nlp-service.app.orchestrator._process_message
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

## Refactoring Analysis

*Pre-refactoring snapshot — use this section to identify targets. Generated from `project/` toon files.*

### Call Graph & Complexity (`project/calls.toon.yaml`)

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/wronai/nlp2dsl
# generated in 0.07s
# nodes: 108 | edges: 110 | modules: 26
# CC̄=2.9

HUBS[20]:
  nlp2dsl_sdk.demos.run_code_generation_demo
    CC=20  in:1  out:51  total:52
  backend.app.engine._execute_workflow
    CC=11  in:2  out:42  total:44
  nlp-service.app.parser_rules._extract_entities
    CC=40  in:1  out:36  total:37
  nlp-service.app.orchestrator._process_message
    CC=21  in:2  out:30  total:32
  backend.app.routers.workflow.stream_workflow
    CC=2  in:0  out:22  total:22
  nlp2dsl_sdk.demos.run_action_catalog_demo
    CC=6  in:0  out:19  total:19
  worker.worker._deliver_notification
    CC=5  in:3  out:16  total:19
  nlp2dsl_sdk.demos._print_workflow_preview
    CC=4  in:3  out:16  total:19
  backend.app.routers.chat._proxy_chat_payload
    CC=9  in:2  out:16  total:18
  nlp2dsl_sdk.demos._print_execution_result
    CC=5  in:7  out:11  total:18
  nlp-service.app.mapper.map_to_dsl
    CC=8  in:1  out:17  total:18
  nlp-service.app.system_executor._exec_file_read
    CC=9  in:0  out:18  total:18
  worker.worker.handle_generate_code
    CC=5  in:0  out:17  total:17
  backend.app.routers.chat.chat_message
    CC=7  in:0  out:17  total:17
  nlp-service.app.parser_llm.parse_llm
    CC=3  in:0  out:16  total:16
  nlp-service.app.audio_parser.stt_audio
    CC=9  in:2  out:14  total:16
  nlp2dsl_sdk.demos._run_gallery_examples
    CC=5  in:1  out:14  total:15
  nlp2dsl_sdk.demos.run_email_demo
    CC=5  in:1  out:14  total:15
  nlp-service.app.settings.SettingsManager.set
    CC=4  in:4  out:11  total:15
  nlp2dsl_sdk.demos.run_invoice_demo
    CC=5  in:1  out:14  total:15

MODULES:
  backend.app.engine  [7 funcs]
    _execute_workflow  CC=11  out:42
    _persist_workflow_snapshot  CC=2  out:2
    _publish_workflow_event  CC=2  out:2
    _track_background_task  CC=1  out:5
    _workflow_steps_payload  CC=2  out:1
    run_workflow  CC=1  out:2
    start_workflow  CC=1  out:7
  backend.app.routers.chat  [4 funcs]
    _proxy_chat_payload  CC=9  out:16
    chat_get_state  CC=2  out:7
    chat_message  CC=7  out:17
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
  nlp-service.app.audio_parser  [3 funcs]
    send_audio  CC=2  out:2
    stt_audio  CC=9  out:14
    stt_file  CC=2  out:4
  nlp-service.app.logging_setup  [1 funcs]
    get_request_id  CC=1  out:1
  nlp-service.app.mapper  [5 funcs]
    _build_config  CC=6  out:10
    _get_field_mapping  CC=1  out:1
    _make_name  CC=3  out:2
    _resolve_actions  CC=7  out:4
    map_to_dsl  CC=8  out:17
  nlp-service.app.orchestrator  [4 funcs]
    _merge_into_state  CC=9  out:4
    _process_message  CC=21  out:30
    continue_conversation  CC=2  out:8
    start_conversation  CC=1  out:6
  nlp-service.app.parser_llm  [3 funcs]
    _detect_provider  CC=10  out:8
    _parse_json_response  CC=6  out:10
    parse_llm  CC=3  out:16
  nlp-service.app.parser_rules  [4 funcs]
    _detect_actions  CC=10  out:9
    _extract_entities  CC=40  out:36
    _resolve_intent  CC=5  out:6
    parse_rules  CC=5  out:10
  nlp-service.app.registry  [3 funcs]
    get_defaults  CC=1  out:3
    get_required_fields  CC=1  out:2
    get_trigger  CC=3  out:2
  nlp-service.app.settings  [2 funcs]
    set  CC=4  out:11
    _coerce_type  CC=5  out:6
  nlp-service.app.system_executor  [4 funcs]
    _exec_file_read  CC=9  out:18
    _exec_file_write  CC=4  out:12
    _is_read_only  CC=2  out:5
    _validate_file_path  CC=5  out:9
  nlp2dsl_sdk.__main__  [1 funcs]
    main  CC=5  out:9
  nlp2dsl_sdk.client  [9 funcs]
    crm_update  CC=2  out:3
    generate_report  CC=1  out:2
    generate_report_and_notify  CC=4  out:6
    notify_slack  CC=2  out:2
    run_workflow  CC=3  out:3
    send_email  CC=3  out:2
    send_invoice  CC=1  out:2
    send_invoice_and_notify  CC=4  out:6
    workflow_step  CC=1  out:1
  nlp2dsl_sdk.demos  [16 funcs]
    _ensure_services  CC=2  out:2
    _preview_text_examples  CC=3  out:6
    _print_execution_result  CC=5  out:11
    _print_json  CC=1  out:2
    _print_workflow_preview  CC=4  out:16
    _run_gallery_examples  CC=5  out:14
    _run_workflow_examples  CC=3  out:4
    list_available_demos  CC=1  out:0
    run_action_catalog_demo  CC=6  out:19
    run_automation_gallery_demo  CC=3  out:4
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
  backend.app.routers.settings.actions_schema → nlp-service.app.logging_setup.get_request_id
  backend.app.routers.settings.action_schema → nlp-service.app.logging_setup.get_request_id
  backend.app.routers.settings.get_settings → nlp-service.app.logging_setup.get_request_id
  backend.app.routers.settings.get_settings_section → nlp-service.app.logging_setup.get_request_id
  backend.app.routers.settings.update_settings_section → nlp-service.app.logging_setup.get_request_id
  backend.app.routers.settings.set_setting → nlp-service.app.logging_setup.get_request_id
  backend.app.routers.settings.reset_settings → nlp-service.app.logging_setup.get_request_id
  nlp2dsl_sdk.__main__.main → nlp2dsl_sdk.demos.list_available_demos
  nlp2dsl_sdk.client.NLP2DSLClient.send_invoice → nlp2dsl_sdk.client.workflow_step
  nlp2dsl_sdk.client.NLP2DSLClient.send_email → nlp2dsl_sdk.client.workflow_step
  nlp2dsl_sdk.client.NLP2DSLClient.generate_report → nlp2dsl_sdk.client.workflow_step
  nlp2dsl_sdk.client.NLP2DSLClient.generate_report_and_notify → nlp2dsl_sdk.client.workflow_step
  nlp2dsl_sdk.client.NLP2DSLClient.notify_slack → nlp2dsl_sdk.client.workflow_step
  nlp2dsl_sdk.client.NLP2DSLClient.crm_update → nlp2dsl_sdk.client.workflow_step
  nlp2dsl_sdk.client.NLP2DSLClient.send_invoice_and_notify → nlp2dsl_sdk.client.workflow_step
  backend.app.routers.system.system_execute → nlp-service.app.logging_setup.get_request_id
  backend.app.routers.workflow.run_workflow_endpoint → nlp2dsl_sdk.client.NLP2DSLClient.run_workflow
  backend.app.routers.workflow.start_workflow_endpoint → backend.app.engine.start_workflow
  backend.app.routers.workflow.stream_workflow → backend.app.routers.workflow._workflow_snapshot
  backend.app.routers.workflow.stream_workflow → backend.app.routers.workflow._format_sse
  nlp-service.app.audio_parser.stt_file → nlp-service.app.audio_parser.stt_audio
  nlp-service.app.audio_parser.StreamingSTT.send_audio → nlp-service.app.audio_parser.stt_audio
  examples.code_generation_examples.main → nlp2dsl_sdk.demos.run_code_generation_demo
  examples.01-invoice.main.main → nlp2dsl_sdk.demos.run_invoice_demo
  nlp-service.app.parser_rules.parse_rules → nlp-service.app.parser_rules._detect_actions
  nlp-service.app.parser_rules.parse_rules → nlp-service.app.parser_rules._resolve_intent
  nlp-service.app.parser_rules.parse_rules → nlp-service.app.parser_rules._extract_entities
  nlp-service.app.parser_rules.parse_rules → nlp-service.app.registry.get_trigger
  nlp-service.app.parser_rules._resolve_intent → nlp-service.app.settings.SettingsManager.set
  examples.02-email.main.main → nlp2dsl_sdk.demos.run_email_demo
  nlp-service.app.mapper.map_to_dsl → nlp-service.app.mapper._resolve_actions
  nlp-service.app.mapper.map_to_dsl → nlp-service.app.mapper._make_name
  nlp-service.app.mapper.map_to_dsl → nlp-service.app.mapper._build_config
  nlp-service.app.mapper.map_to_dsl → nlp-service.app.registry.get_trigger
  nlp-service.app.mapper._build_config → nlp-service.app.registry.get_required_fields
  nlp-service.app.mapper._build_config → nlp-service.app.registry.get_defaults
  nlp-service.app.mapper._build_config → nlp-service.app.mapper._get_field_mapping
  nlp-service.app.orchestrator.start_conversation → nlp-service.app.orchestrator._process_message
  nlp-service.app.orchestrator.continue_conversation → nlp-service.app.orchestrator._process_message
```

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 96f 8515L | python:47,shell:12,txt:8,toml:5,yaml:4,json:3,ini:3,yml:2,rust:2,javascript:2 | 2026-06-03
# generated in 0.03s
# CC̅=2.9 | critical:5/272 | dups:0 | cycles:0

HEALTH[5]:
  🟡 CC    _handle_response CC=16 (limit:15)
  🟡 CC    _extract_entities CC=40 (limit:15)
  🟡 CC    _process_message CC=21 (limit:15)
  🟡 CC    _format_system_result CC=16 (limit:15)
  🟡 CC    run_code_generation_demo CC=20 (limit:15)

REFACTOR[1]:
  1. split 5 high-CC methods  (CC>15)

PIPELINES[194]:
  [1] Src [main]: main
      PURITY: 100% pure
  [2] Src [main]: main
      PURITY: 100% pure
  [3] Src [server]: server
      PURITY: 100% pure
  [4] Src [npmCommand]: npmCommand
      PURITY: 100% pure
  [5] Src [child]: child
      PURITY: 100% pure
  [6] Src [shuttingDown]: shuttingDown
      PURITY: 100% pure
  [7] Src [exitCode]: exitCode → main → shutdown
      PURITY: 100% pure
  [8] Src [http]: http
      PURITY: 100% pure
  [9] Src [fs]: fs
      PURITY: 100% pure
  [10] Src [path]: path
      PURITY: 100% pure
  [11] Src [HOST]: HOST
      PURITY: 100% pure
  [12] Src [PORT]: PORT
      PURITY: 100% pure
  [13] Src [ROOT_DIR]: ROOT_DIR
      PURITY: 100% pure
  [14] Src [MIME_TYPES]: MIME_TYPES
      PURITY: 100% pure
  [15] Src [safePath]: safePath
      PURITY: 100% pure
  [16] Src [candidate]: candidate
      PURITY: 100% pure
  [17] Src [fileContents]: fileContents → contentType
      PURITY: 100% pure
  [18] Src [pathname]: pathname
      PURITY: 100% pure
  [19] Src [targetPath]: targetPath
      PURITY: 100% pure
  [20] Src [startServer]: startServer → handleRequest → resolveRequestPath → isInsideRoot
      PURITY: 100% pure
  [21] Src [server]: server → handleRequest → resolveRequestPath → isInsideRoot
      PURITY: 100% pure
  [22] Src [actions_schema]: actions_schema → get_request_id
      PURITY: 100% pure
  [23] Src [action_schema]: action_schema → get_request_id
      PURITY: 100% pure
  [24] Src [get_settings]: get_settings → get_request_id
      PURITY: 100% pure
  [25] Src [get_settings_section]: get_settings_section → get_request_id
      PURITY: 100% pure
  [26] Src [update_settings_section]: update_settings_section → get_request_id
      PURITY: 100% pure
  [27] Src [set_setting]: set_setting → get_request_id
      PURITY: 100% pure
  [28] Src [reset_settings]: reset_settings → get_request_id
      PURITY: 100% pure
  [29] Src [main]: main → list_available_demos
      PURITY: 100% pure
  [30] Src [to_dict]: to_dict
      PURITY: 100% pure
  [31] Src [__init__]: __init__
      PURITY: 100% pure
  [32] Src [_ensure_engine]: _ensure_engine
      PURITY: 100% pure
  [33] Src [_get_session_factory]: _get_session_factory
      PURITY: 100% pure
  [34] Src [_ensure_tables]: _ensure_tables
      PURITY: 100% pure
  [35] Src [save_run]: save_run
      PURITY: 100% pure
  [36] Src [update_run_status]: update_run_status
      PURITY: 100% pure
  [37] Src [get_run]: get_run
      PURITY: 100% pure
  [38] Src [list_runs]: list_runs
      PURITY: 100% pure
  [39] Src [count_runs]: count_runs
      PURITY: 100% pure
  [40] Src [close]: close
      PURITY: 100% pure
  [41] Src [health]: health
      PURITY: 100% pure
  [42] Src [__init__]: __init__
      PURITY: 100% pure
  [43] Src [from_env]: from_env
      PURITY: 100% pure
  [44] Src [close]: close
      PURITY: 100% pure
  [45] Src [__exit__]: __exit__
      PURITY: 100% pure
  [46] Src [_request]: _request
      PURITY: 100% pure
  [47] Src [_backend]: _backend
      PURITY: 100% pure
  [48] Src [_nlp_service]: _nlp_service
      PURITY: 100% pure
  [49] Src [_worker]: _worker
      PURITY: 100% pure
  [50] Src [backend_health]: backend_health
      PURITY: 100% pure

LAYERS:
  nlp-service/                    CC̄=4.1    ←in:0  →out:0
  │ registry                   384L  0C    4m  CC=5      ←3
  │ !! orchestrator               344L  0C    7m  CC=21     ←0
  │ system_executor            342L  0C   13m  CC=12     ←0
  │ !! parser_rules               290L  0C    5m  CC=40     ←1
  │ code_generator             279L  1C    8m  CC=14     ←0
  │ settings                   251L  6C   11m  CC=6      ←2
  │ mapper                     189L  0C    6m  CC=8      ←1
  │ parser_llm                 187L  0C    3m  CC=10     ←0
  │ audio_parser               148L  1C    8m  CC=9      ←0
  │ schemas                    127L  11C    0m  CC=0.0    ←0
  │ logging_setup              100L  2C    6m  CC=3      ←5
  │ config                      60L  1C    0m  CC=0.0    ←0
  │ redis_store                 58L  1C    7m  CC=3      ←0
  │ pyproject.toml              52L  0C    0m  CC=0.0    ←0
  │ factory                     46L  0C    1m  CC=4      ←0
  │ __init__                    30L  1C    4m  CC=1      ←0
  │ manifest.json               30L  0C    0m  CC=0.0    ←0
  │ memory                      23L  1C    5m  CC=1      ←0
  │ Dockerfile                  11L  0C    0m  CC=0.0    ←0
  │ requirements.txt             9L  0C    0m  CC=0.0    ←0
  │ pytest.ini                   5L  0C    0m  CC=0.0    ←0
  │ __init__                     0L  0C    0m  CC=0.0    ←0
  │
  tauri-wrapper/                  CC̄=2.7    ←in:0  →out:0
  │ serve-dist.js              139L  0C   21m  CC=8      ←0
  │ desktop.sh                  79L  0C    0m  CC=0.0    ←0
  │ dev.js                      56L  0C    7m  CC=11     ←0
  │ tauri.conf.json             43L  0C    0m  CC=0.0    ←0
  │ package.json                18L  0C    0m  CC=0.0    ←0
  │ Cargo.toml                  17L  0C    0m  CC=0.0    ←0
  │ main.rs                      7L  0C    1m  CC=2      ←0
  │ build.rs                     3L  0C    1m  CC=1      ←0
  │
  nlp2dsl_sdk/                    CC̄=2.6    ←in:8  →out:0
  │ !! demos                      659L  1C   17m  CC=20     ←6
  │ !! client                     567L  2C   47m  CC=16     ←2
  │ __main__                    41L  0C    1m  CC=5      ←0
  │ __init__                    33L  0C    0m  CC=0.0    ←0
  │
  backend/                        CC̄=2.1    ←in:0  →out:0
  │ engine                     269L  0C    7m  CC=11     ←1
  │ workflow                   189L  0C    9m  CC=8      ←0
  │ postgres                   172L  3C   11m  CC=4      ←0
  │ chat                       107L  0C    4m  CC=9      ←0
  │ logging_setup              100L  2C    6m  CC=3      ←0
  │ workflow_events             91L  2C    6m  CC=3      ←0
  │ settings                    81L  0C    7m  CC=2      ←0
  │ schemas                     64L  6C    0m  CC=0.0    ←0
  │ pyproject.toml              52L  0C    0m  CC=0.0    ←0
  │ __init__                    49L  1C    6m  CC=2      ←0
  │ main                        48L  0C    1m  CC=1      ←0
  │ config                      42L  1C    0m  CC=0.0    ←0
  │ memory                      37L  1C    6m  CC=2      ←0
  │ system                      29L  0C    1m  CC=2      ←0
  │ workflow                    22L  0C    0m  CC=0.0    ←0
  │ Dockerfile                  11L  0C    0m  CC=0.0    ←0
  │ requirements.txt             8L  0C    0m  CC=0.0    ←0
  │ pytest.ini                   5L  0C    0m  CC=0.0    ←0
  │ __init__                     0L  0C    0m  CC=0.0    ←0
  │ __init__                     0L  0C    0m  CC=0.0    ←0
  │
  worker/                         CC̄=1.7    ←in:0  →out:0
  │ worker                     230L  0C   12m  CC=5      ←0
  │ logging_setup              100L  2C    6m  CC=3      ←0
  │ pyproject.toml              46L  0C    0m  CC=0.0    ←0
  │ config                      27L  1C    0m  CC=0.0    ←0
  │ Dockerfile                  11L  0C    0m  CC=0.0    ←0
  │ __init__                     5L  0C    0m  CC=0.0    ←0
  │ pytest.ini                   5L  0C    0m  CC=0.0    ←0
  │ requirements.txt             3L  0C    0m  CC=0.0    ←0
  │
  examples/                       CC̄=1.2    ←in:0  →out:1
  │ docker-compose.yml          60L  0C    0m  CC=0.0    ←0
  │ main                        38L  0C    1m  CC=2      ←0
  │ code_generation_examples    25L  0C    1m  CC=1      ←0
  │ main                        23L  0C    1m  CC=1      ←0
  │ main                        23L  0C    1m  CC=1      ←0
  │ main                        23L  0C    1m  CC=1      ←0
  │ main                        23L  0C    1m  CC=1      ←0
  │ Dockerfile                  23L  0C    0m  CC=0.0    ←0
  │ Dockerfile                  23L  0C    0m  CC=0.0    ←0
  │ Dockerfile                  23L  0C    0m  CC=0.0    ←0
  │ Dockerfile                  23L  0C    0m  CC=0.0    ←0
  │ Dockerfile                  23L  0C    0m  CC=0.0    ←0
  │ run.sh                       6L  0C    0m  CC=0.0    ←0
  │ run.sh                       6L  0C    0m  CC=0.0    ←0
  │ run.sh                       6L  0C    0m  CC=0.0    ←0
  │ run.sh                       6L  0C    0m  CC=0.0    ←0
  │ run.sh                       6L  0C    0m  CC=0.0    ←0
  │ requirements.txt             1L  0C    0m  CC=0.0    ←0
  │ requirements.txt             1L  0C    0m  CC=0.0    ←0
  │ requirements.txt             1L  0C    0m  CC=0.0    ←0
  │ requirements.txt             1L  0C    0m  CC=0.0    ←0
  │ requirements.txt             1L  0C    0m  CC=0.0    ←0
  │ run.sh                       0L  0C    0m  CC=0.0    ←0
  │
  ./                              CC̄=0.0    ←in:0  →out:0
  │ !! planfile.yaml              747L  0C    0m  CC=0.0    ←0
  │ !! goal.yaml                  512L  0C    0m  CC=0.0    ←0
  │ docker-compose.yml         110L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                82L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              60L  0C    0m  CC=0.0    ←0
  │ project.sh                  59L  0C    0m  CC=0.0    ←0
  │ metrun-profile.sh           48L  0C    0m  CC=0.0    ←0
  │ run-all-tests.sh            44L  0C    1m  CC=0.0    ←0
  │ pyqual.yaml                 41L  0C    0m  CC=0.0    ←0
  │ .pfix-test-wrapper.sh       16L  0C    0m  CC=0.0    ←0
  │ tree.sh                      1L  0C    0m  CC=0.0    ←0
  │
  ── zero ──
     backend/app/__init__.py                   0L
     backend/app/routers/__init__.py           0L
     examples/basic/invoice/run.sh             0L
     nlp-service/app/__init__.py               0L

COUPLING:
                                                   backend.app                nlp-service.app                    nlp2dsl_sdk                       examples            examples.01-invoice              examples.02-email  examples.03-report-and-notify   examples.04-scheduled-report
                    backend.app                             ──                             15                              3                                                                                                                                                             !! fan-out
                nlp-service.app                            ←15                             ──                                                                                                                                                                                            hub
                    nlp2dsl_sdk                             ←3                                                            ──                             ←1                             ←1                             ←1                             ←1                             ←1  hub
                       examples                                                                                            1                             ──                                                                                                                            
            examples.01-invoice                                                                                            1                                                            ──                                                                                             
              examples.02-email                                                                                            1                                                                                           ──                                                              
  examples.03-report-and-notify                                                                                            1                                                                                                                          ──                               
   examples.04-scheduled-report                                                                                            1                                                                                                                                                         ──
  CYCLES: none
  HUB: nlp-service.app/ (fan-in=15)
  HUB: nlp2dsl_sdk/ (fan-in=8)
  SMELL: backend.app/ fan-out=18 → split needed

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 10 groups | 48f 6496L | 2026-06-03

SUMMARY:
  files_scanned: 48
  total_lines:   6496
  dup_groups:    10
  dup_fragments: 28
  saved_lines:   140
  scan_ms:       2115

HOTSPOTS[7] (files with most duplication):
  backend/app/logging_setup.py  dup=49L  groups=5  frags=5  (0.8%)
  nlp-service/app/logging_setup.py  dup=49L  groups=5  frags=5  (0.8%)
  worker/logging_setup.py  dup=49L  groups=5  frags=5  (0.8%)
  backend/app/routers/settings.py  dup=24L  groups=2  frags=4  (0.4%)
  worker/worker.py  dup=22L  groups=1  frags=2  (0.3%)
  backend/app/routers/workflow.py  dup=6L  groups=1  frags=2  (0.1%)
  examples/01-invoice/main.py  dup=4L  groups=1  frags=1  (0.1%)

DUPLICATES[10] (ranked by impact):
  [5980042b45ef9ea3] ! STRU  setup_logging  L=22 N=3 saved=44 sim=1.00
      backend/app/logging_setup.py:79-100  (setup_logging)
      nlp-service/app/logging_setup.py:79-100  (setup_logging)
      worker/logging_setup.py:79-100  (setup_logging)
  [a58ac04d8adce867]   EXAC  format  L=12 N=3 saved=24 sim=1.00
      backend/app/logging_setup.py:40-51  (format)
      nlp-service/app/logging_setup.py:40-51  (format)
      worker/logging_setup.py:40-51  (format)
  [ffd95d6b2707ba43]   EXAC  dispatch  L=9 N=3 saved=18 sim=1.00
      backend/app/logging_setup.py:68-76  (dispatch)
      nlp-service/app/logging_setup.py:68-76  (dispatch)
      worker/logging_setup.py:68-76  (dispatch)
  [8e6677ea0d5059a7]   STRU  main  L=4 N=5 saved=16 sim=1.00
      examples/01-invoice/main.py:16-19  (main)
      examples/02-email/main.py:16-19  (main)
      examples/03-report-and-notify/main.py:16-19  (main)
      examples/04-scheduled-report/main.py:16-19  (main)
      examples/code_generation_examples.py:18-21  (main)
  [fe1a465464777068]   STRU  handle_notify_slack  L=11 N=2 saved=11 sim=1.00
      worker/worker.py:119-129  (handle_notify_slack)
      worker/worker.py:133-143  (handle_notify_telegram)
  [8e33482aef8974e1]   STRU  action_schema  L=7 N=2 saved=7 sim=1.00
      backend/app/routers/settings.py:29-35  (action_schema)
      backend/app/routers/settings.py:47-53  (get_settings_section)
  [e2bd3c5d1f7d650b]   EXAC  __init__  L=3 N=3 saved=6 sim=1.00
      backend/app/logging_setup.py:36-38  (__init__)
      nlp-service/app/logging_setup.py:36-38  (__init__)
      worker/logging_setup.py:36-38  (__init__)
  [2283cb9d4d16ec25]   EXAC  __init__  L=3 N=3 saved=6 sim=1.00
      backend/app/logging_setup.py:64-66  (__init__)
      nlp-service/app/logging_setup.py:64-66  (__init__)
      worker/logging_setup.py:64-66  (__init__)
  [2ce1096adac6d1a4]   STRU  actions_schema  L=5 N=2 saved=5 sim=1.00
      backend/app/routers/settings.py:21-25  (actions_schema)
      backend/app/routers/settings.py:39-43  (get_settings)
  [8af82767bfb2b892]   STRU  run_workflow_endpoint  L=3 N=2 saved=3 sim=1.00
      backend/app/routers/workflow.py:67-69  (run_workflow_endpoint)
      backend/app/routers/workflow.py:73-75  (start_workflow_endpoint)

REFACTOR[10] (ranked by priority):
  [1] ● extract_function   → utils/setup_logging.py
      WHY: 3 occurrences of 22-line block across 3 files — saves 44 lines
      FILES: backend/app/logging_setup.py, nlp-service/app/logging_setup.py, worker/logging_setup.py
  [2] ● extract_class      → utils/format.py
      WHY: 3 occurrences of 12-line block across 3 files — saves 24 lines
      FILES: backend/app/logging_setup.py, nlp-service/app/logging_setup.py, worker/logging_setup.py
  [3] ● extract_class      → utils/dispatch.py
      WHY: 3 occurrences of 9-line block across 3 files — saves 18 lines
      FILES: backend/app/logging_setup.py, nlp-service/app/logging_setup.py, worker/logging_setup.py
  [4] ○ extract_function   → examples/utils/main.py
      WHY: 5 occurrences of 4-line block across 5 files — saves 16 lines
      FILES: examples/01-invoice/main.py, examples/02-email/main.py, examples/03-report-and-notify/main.py, examples/04-scheduled-report/main.py, examples/code_generation_examples.py
  [5] ○ extract_function   → worker/utils/handle_notify_slack.py
      WHY: 2 occurrences of 11-line block across 1 files — saves 11 lines
      FILES: worker/worker.py
  [6] ○ extract_function   → backend/app/routers/utils/action_schema.py
      WHY: 2 occurrences of 7-line block across 1 files — saves 7 lines
      FILES: backend/app/routers/settings.py
  [7] ● extract_class      → utils/__init__.py
      WHY: 3 occurrences of 3-line block across 3 files — saves 6 lines
      FILES: backend/app/logging_setup.py, nlp-service/app/logging_setup.py, worker/logging_setup.py
  [8] ● extract_class      → utils/__init__.py
      WHY: 3 occurrences of 3-line block across 3 files — saves 6 lines
      FILES: backend/app/logging_setup.py, nlp-service/app/logging_setup.py, worker/logging_setup.py
  [9] ○ extract_function   → backend/app/routers/utils/actions_schema.py
      WHY: 2 occurrences of 5-line block across 1 files — saves 5 lines
      FILES: backend/app/routers/settings.py
  [10] ○ extract_function   → backend/app/routers/utils/run_workflow_endpoint.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: backend/app/routers/workflow.py

QUICK_WINS[3] (low risk, high savings — do first):
  [4] extract_function   saved=16L  → examples/utils/main.py
      FILES: main.py, main.py, main.py +2
  [5] extract_function   saved=11L  → worker/utils/handle_notify_slack.py
      FILES: worker.py
  [6] extract_function   saved=7L  → backend/app/routers/utils/action_schema.py
      FILES: settings.py

DEPENDENCY_RISK[5] (duplicates spanning multiple packages):
  setup_logging  packages=3  files=3
      backend/app/logging_setup.py
      nlp-service/app/logging_setup.py
      worker/logging_setup.py
  format  packages=3  files=3
      backend/app/logging_setup.py
      nlp-service/app/logging_setup.py
      worker/logging_setup.py
  dispatch  packages=3  files=3
      backend/app/logging_setup.py
      nlp-service/app/logging_setup.py
      worker/logging_setup.py
  __init__  packages=3  files=3
      backend/app/logging_setup.py
      nlp-service/app/logging_setup.py
      worker/logging_setup.py
  __init__  packages=3  files=3
      backend/app/logging_setup.py
      nlp-service/app/logging_setup.py
      worker/logging_setup.py

EFFORT_ESTIMATE (total ≈ 7.9h):
  hard   setup_logging                       saved=44L  ~176min
  hard   format                              saved=24L  ~96min
  medium dispatch                            saved=18L  ~72min
  medium main                                saved=16L  ~32min
  easy   handle_notify_slack                 saved=11L  ~22min
  easy   action_schema                       saved=7L  ~14min
  easy   __init__                            saved=6L  ~24min
  easy   __init__                            saved=6L  ~24min
  easy   actions_schema                      saved=5L  ~10min
  easy   run_workflow_endpoint               saved=3L  ~6min

METRICS-TARGET:
  dup_groups:  10 → 0
  saved_lines: 140 lines recoverable
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 238 func | 33f | 2026-06-03
# generated in 0.00s

NEXT[8] (ranked by impact):
  [1] !! SPLIT           nlp2dsl_sdk/demos.py
      WHY: 659L, 1 classes, max CC=20
      EFFORT: ~4h  IMPACT: 13180

  [2] !! SPLIT           nlp2dsl_sdk/client.py
      WHY: 567L, 2 classes, max CC=16
      EFFORT: ~4h  IMPACT: 9072

  [3] !! SPLIT-FUNC      _extract_entities  CC=40  fan=30
      WHY: CC=40 exceeds 15
      EFFORT: ~1h  IMPACT: 1200

  [4] !  SPLIT-FUNC      _process_message  CC=21  fan=20
      WHY: CC=21 exceeds 15
      EFFORT: ~1h  IMPACT: 420

  [5] !  SPLIT-FUNC      run_code_generation_demo  CC=20  fan=21
      WHY: CC=20 exceeds 15
      EFFORT: ~1h  IMPACT: 420

  [6] !  SPLIT-FUNC      ConversationFlow._handle_response  CC=16  fan=11
      WHY: CC=16 exceeds 15
      EFFORT: ~1h  IMPACT: 176

  [7] !  SPLIT-FUNC      _format_system_result  CC=16  fan=7
      WHY: CC=16 exceeds 15
      EFFORT: ~1h  IMPACT: 112

  [8] !! SPLIT           planfile.yaml
      WHY: 747L, 0 classes, max CC=0
      EFFORT: ~4h  IMPACT: 0


RISKS[3]:
  ⚠ Splitting planfile.yaml may break 0 import paths
  ⚠ Splitting nlp2dsl_sdk/demos.py may break 17 import paths
  ⚠ Splitting nlp2dsl_sdk/client.py may break 47 import paths

METRICS-TARGET:
  CC̄:          2.9 → ≤2.0
  max-CC:      40 → ≤20
  god-modules: 4 → 0
  high-CC(≥15): 5 → ≤2
  hub-types:   0 → ≤0

PATTERNS (language parser shared logic):
  _extract_declarations() in base.py — unified extraction for:
    - TypeScript: interfaces, types, classes, functions, arrow funcs
    - PHP: namespaces, traits, classes, functions, includes
    - Ruby: modules, classes, methods, requires
    - C++: classes, structs, functions, #includes
    - C#: classes, interfaces, methods, usings
    - Java: classes, interfaces, methods, imports
    - Go: packages, functions, structs
    - Rust: modules, functions, traits, use statements

  Shared regex patterns per language:
    - import: language-specific import/require/using patterns
    - class: class/struct/trait declarations with inheritance
    - function: function/method signatures with visibility
    - brace_tracking: for C-family languages ({ })
    - end_keyword_tracking: for Ruby (module/class/def...end)

  Benefits:
    - Consistent extraction logic across all languages
    - Reduced code duplication (~70% reduction in parser LOC)
    - Easier maintenance: fix once, apply everywhere
    - Standardized FunctionInfo/ClassInfo models

HISTORY:
  prev CC̄=3.0 → now CC̄=2.9
```

### Validation (`project/validation.toon.yaml`)

```toon markpact:analysis path=project/validation.toon.yaml
# vallm batch | 170f | 69✓ 3⚠ 38✗ | 2026-04-08

SUMMARY:
  scanned: 170  passed: 69 (40.6%)  warnings: 3  errors: 38  unsupported: 63

WARNINGS[3]{path,score}:
  nlp2dsl_sdk/client.py,0.96
    issues[3]{rule,severity,message,line}:
      complexity.cyclomatic,warning,_handle_response has cyclomatic complexity 16 (max: 15),475
      complexity.maintainability,warning,Low maintainability index: 17.6 (threshold: 20),
      complexity.lizard_cc,warning,_handle_response: CC=16 exceeds limit 15,475
  nlp2dsl_sdk/demos.py,0.96
    issues[3]{rule,severity,message,line}:
      complexity.cyclomatic,warning,run_code_generation_demo has cyclomatic complexity 20 (max: 15),540
      complexity.maintainability,warning,Low maintainability index: 17.4 (threshold: 20),
      complexity.lizard_cc,warning,run_code_generation_demo: CC=20 exceeds limit 15,540
  tests/test_nlp2dsl_sdk.py,0.96
    issues[2]{rule,severity,message,line}:
      complexity.cyclomatic,warning,test_workflow_and_conversation_endpoints has cyclomatic complexity 17 (max: 15),74
      complexity.cyclomatic,warning,test_code_generation_methods_hit_expected_services has cyclomatic complexity 16 (max: 15),205

ERRORS[38]{path,score}:
  backend/app/workflow.py,0.57
    issues[5]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'app.engine' not found,12
      python.import.resolvable,error,Module 'app.engine' not found,13
      python.import.resolvable,error,Module 'app.engine' not found,14
      python.import.resolvable,error,Module 'app.engine' not found,15
      python.import.resolvable,error,Module 'app.routers.workflow' not found,16
  nlp-service/app/store/memory.py,0.57
    issues[1]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'app.store' not found,5
  tests/tests/test_tests.py,0.57
    issues[1]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'tests' not found,11
  backend/tests/test_config.py,0.61
    issues[10]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'app.config' not found,16
      python.import.resolvable,error,Module 'app.config' not found,22
      python.import.resolvable,error,Module 'app.config' not found,28
      python.import.resolvable,error,Module 'app.config' not found,34
      python.import.resolvable,error,Module 'app.config' not found,44
      python.import.resolvable,error,Module 'app.config' not found,50
      python.import.resolvable,error,Module 'app.config' not found,56
      python.import.resolvable,error,Module 'app.config' not found,62
      python.import.resolvable,error,Module 'app.config' not found,71
      python.import.resolvable,error,Module 'app.engine' not found,80
  nlp-service/tests/test_system_executor.py,0.62
    issues[15]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'app.registry' not found,11
      python.import.resolvable,error,Module 'app.settings' not found,12
      python.import.resolvable,error,Module 'app.system_executor' not found,13
      python.import.resolvable,error,Module 'app.system_executor' not found,231
      python.import.resolvable,error,Module 'app.system_executor' not found,248
      python.import.resolvable,error,Module 'app.system_executor' not found,262
      python.import.resolvable,error,Module 'app.system_executor' not found,279
      python.import.resolvable,error,Module 'app.system_executor' not found,291
      python.import.resolvable,error,Module 'app.system_executor' not found,305
      python.import.resolvable,error,Module 'app.system_executor' not found,324
      python.import.resolvable,error,Module 'app.system_executor' not found,352
      python.import.resolvable,error,Module 'app.system_executor' not found,361
      python.import.resolvable,error,Module 'app.system_executor' not found,375
      python.import.resolvable,error,Module 'app.system_executor' not found,389
      python.import.resolvable,error,Module 'app.system_executor' not found,396
  nlp-service/app/store/factory.py,0.66
    issues[4]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'app.store' not found,14
      python.import.resolvable,error,Module 'app.store.memory' not found,15
      python.import.resolvable,error,Module 'app.config' not found,28
      python.import.resolvable,error,Module 'app.store.redis_store' not found,36
  backend/app/db/__init__.py,0.68
    issues[3]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'app.config' not found,42
      python.import.resolvable,error,Module 'app.db.memory' not found,48
      python.import.resolvable,error,Module 'app.db.postgres' not found,46
  backend/app/db/postgres.py,0.68
    issues[6]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'sqlalchemy' not found,11
      python.import.resolvable,error,Module 'sqlalchemy.dialects.postgresql' not found,12
      python.import.resolvable,error,Module 'sqlalchemy.dialects.postgresql' not found,13
      python.import.resolvable,error,Module 'sqlalchemy.ext.asyncio' not found,14
      python.import.resolvable,error,Module 'sqlalchemy.orm' not found,15
      python.import.resolvable,error,Module 'app.db' not found,17
  nlp-service/tests/test_store.py,0.69
    issues[5]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'app.schemas' not found,11
      python.import.resolvable,error,Module 'app.store.memory' not found,12
      python.import.resolvable,error,Module 'app.store.factory' not found,137
      python.import.resolvable,error,Module 'app.store.factory' not found,150
      python.import.resolvable,error,Module 'app.store.factory' not found,164
  nlp-service/app/mapper.py,0.71
    issues[2]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'app.registry' not found,13
      python.import.resolvable,error,Module 'app.schemas' not found,20
  nlp-service/app/orchestrator.py,0.71
    issues[6]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'app.mapper' not found,17
      python.import.resolvable,error,Module 'app.parser_rules' not found,18
      python.import.resolvable,error,Module 'app.registry' not found,19
      python.import.resolvable,error,Module 'app.schemas' not found,20
      python.import.resolvable,error,Module 'app.store.factory' not found,29
      python.import.resolvable,error,Module 'app.system_executor' not found,190
  nlp-service/tests/test_orchestrator.py,0.71
    issues[4]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'app.orchestrator' not found,11
      python.import.resolvable,error,Module 'app.schemas' not found,18
      python.import.resolvable,error,Module 'app.store.memory' not found,25
      python.import.resolvable,error,Module 'app.orchestrator' not found,31
  nlp-service/app/main.py,0.72
    issues[13]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'app.audio_parser' not found,32
      python.import.resolvable,error,Module 'app.code_generator' not found,33
      python.import.resolvable,error,Module 'app.config' not found,34
      python.import.resolvable,error,Module 'app.logging_setup' not found,35
      python.import.resolvable,error,Module 'app.mapper' not found,36
      python.import.resolvable,error,Module 'app.orchestrator' not found,37
      python.import.resolvable,error,Module 'app.parser_llm' not found,43
      python.import.resolvable,error,Module 'app.parser_rules' not found,44
      python.import.resolvable,error,Module 'app.registry' not found,45
      python.import.resolvable,error,Module 'app.schemas' not found,46
      python.import.resolvable,error,Module 'app.settings' not found,53
      python.import.resolvable,error,Module 'app.store.factory' not found,54
      python.import.resolvable,error,Module 'app.system_executor' not found,55
  backend/app/main.py,0.73
    issues[5]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'app.logging_setup' not found,14
      python.import.resolvable,error,Module 'app.routers.chat' not found,15
      python.import.resolvable,error,Module 'app.routers.settings' not found,16
      python.import.resolvable,error,Module 'app.routers.system' not found,17
      python.import.resolvable,error,Module 'app.routers.workflow' not found,18
  backend/tests/test_persistence.py,0.74
    issues[3]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'app.db.memory' not found,11
      python.import.resolvable,error,Module 'app.db' not found,169
      python.import.resolvable,error,Module 'app.db' not found,182
  nlp-service/tests/test_mapper.py,0.74
    issues[3]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'app.mapper' not found,10
      python.import.resolvable,error,Module 'app.registry' not found,11
      python.import.resolvable,error,Module 'app.schemas' not found,12
  nlp-service/tests/test_parser_rules.py,0.74
    issues[3]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'app.parser_rules' not found,10
      python.import.resolvable,error,Module 'app.schemas' not found,11
      python.import.resolvable,error,Module 'app.registry' not found,198
  backend/app/db/memory.py,0.79
    issues[1]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'app.db' not found,7
  nlp-service/app/parser_rules.py,0.79
    issues[2]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'app.registry' not found,15
      python.import.resolvable,error,Module 'app.schemas' not found,20
  backend/tests/test_logging.py,0.80
    issues[6]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'app.logging_setup' not found,18
      python.import.resolvable,error,Module 'app.logging_setup' not found,36
      python.import.resolvable,error,Module 'app.logging_setup' not found,55
      python.import.resolvable,error,Module 'app.logging_setup' not found,72
      python.import.resolvable,error,Module 'app.logging_setup' not found,110
      python.import.resolvable,error,Module 'app.logging_setup' not found,119
  backend/app/engine.py,0.82
    issues[5]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'app.config' not found,16
      python.import.resolvable,error,Module 'app.db' not found,17
      python.import.resolvable,error,Module 'app.logging_setup' not found,18
      python.import.resolvable,error,Module 'app.workflow_events' not found,19
      python.import.resolvable,error,Module 'app.schemas' not found,20
  backend/app/routers/chat.py,0.82
    issues[3]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'app.engine' not found,13
      python.import.resolvable,error,Module 'app.logging_setup' not found,14
      python.import.resolvable,error,Module 'app.schemas' not found,15
  nlp-service/app/store/redis_store.py,0.83
    issues[2]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'redis.asyncio' not found,13
      python.import.resolvable,error,Module 'app.store' not found,15
  nlp-service/app/system_executor.py,0.83
    issues[2]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'app.registry' not found,16
      python.import.resolvable,error,Module 'app.settings' not found,17
  backend/app/routers/settings.py,0.86
    issues[2]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'app.engine' not found,13
      python.import.resolvable,error,Module 'app.logging_setup' not found,14
  backend/app/routers/system.py,0.86
    issues[2]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'app.engine' not found,13
      python.import.resolvable,error,Module 'app.logging_setup' not found,14
  backend/app/routers/workflow.py,0.86
    issues[4]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'app.engine' not found,15
      python.import.resolvable,error,Module 'app.logging_setup' not found,16
      python.import.resolvable,error,Module 'app.workflow_events' not found,17
      python.import.resolvable,error,Module 'app.schemas' not found,18
  nlp-service/app/audio_parser.py,0.86
    issues[1]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'app.config' not found,19
  nlp-service/tests/test_registry.py,0.86
    issues[1]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'app.registry' not found,10
  test_code_generation.py,0.86
    issues[1]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'code_generator' not found,14
  tests/e2e/test_websocket.py,0.88
    issues[2]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'websockets' not found,17
      python.import.resolvable,error,Module 'websockets.connection' not found,18
  tests/e2e/test_chat_ui.py,0.89
    issues[1]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'playwright.async_api' not found,24
  nlp-service/app/parser_llm.py,0.93
    issues[1]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'app.schemas' not found,31
  nlp-service/app/settings.py,0.94
    issues[1]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'app.config' not found,20
  backend/app/logging_setup.py,0.96
    issues[1]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'app.config' not found,87
  nlp-service/app/logging_setup.py,0.96
    issues[1]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'app.config' not found,87
  worker/logging_setup.py,0.96
    issues[1]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'config' not found,87
  worker/worker.py,0.96
    issues[1]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'logging_setup' not found,25

UNSUPPORTED[6]{bucket,count}:
  *.md,25
  Dockerfile*,8
  *.txt,10
  *.yml,2
  *.example,6
  other,12
```

## Intent

Reusable Python SDK for the NLP2DSL platform
