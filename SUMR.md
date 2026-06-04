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
- **version**: `0.0.12`
- **python_requires**: `>=3.10`
- **license**: Apache-2.0
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
  version: 0.0.12;
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

*132 nodes · 138 edges · 28 modules · CC̄=2.8*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `_execute_workflow` *(in backend.app.engine)* | 11 ⚠ | 2 | 42 | **44** |
| `_format_system_result` *(in nlp-service.app.orchestrator)* | 16 ⚠ | 1 | 38 | **39** |
| `stream_workflow` *(in backend.app.routers.workflow)* | 2 | 0 | 22 | **22** |
| `chat_message` *(in backend.app.routers.chat)* | 12 ⚠ | 0 | 21 | **21** |
| `map_to_dsl` *(in nlp-service.app.mapper)* | 8 | 2 | 17 | **19** |
| `_deliver_notification` *(in worker.worker)* | 5 | 3 | 16 | **19** |
| `_print_workflow_preview` *(in nlp2dsl_sdk.demos)* | 4 | 3 | 16 | **19** |
| `run_action_catalog_demo` *(in nlp2dsl_sdk.demos)* | 6 | 0 | 19 | **19** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/wronai/nlp2dsl
# generated in 0.06s
# nodes: 132 | edges: 138 | modules: 28
# CC̄=2.8

HUBS[20]:
  backend.app.engine._execute_workflow
    CC=11  in:2  out:42  total:44
  nlp-service.app.orchestrator._format_system_result
    CC=16  in:1  out:38  total:39
  backend.app.routers.workflow.stream_workflow
    CC=2  in:0  out:22  total:22
  backend.app.routers.chat.chat_message
    CC=12  in:0  out:21  total:21
  nlp-service.app.mapper.map_to_dsl
    CC=8  in:2  out:17  total:19
  worker.worker._deliver_notification
    CC=5  in:3  out:16  total:19
  nlp2dsl_sdk.demos._print_workflow_preview
    CC=4  in:3  out:16  total:19
  nlp2dsl_sdk.demos.run_action_catalog_demo
    CC=6  in:0  out:19  total:19
  nlp-service.app.system_executor._exec_file_read
    CC=9  in:0  out:18  total:18
  backend.app.routers.chat._proxy_chat_payload
    CC=9  in:2  out:16  total:18
  nlp2dsl_sdk.demos._print_execution_result
    CC=5  in:7  out:11  total:18
  nlp-service.app.parser_llm.parse_llm
    CC=3  in:2  out:16  total:18
  worker.worker.handle_generate_code
    CC=5  in:0  out:17  total:17
  nlp-service.app.settings.SettingsManager.set
    CC=4  in:5  out:11  total:16
  nlp-service.app.audio_parser.stt_audio
    CC=9  in:2  out:14  total:16
  nlp2dsl_sdk.demos.run_invoice_demo
    CC=5  in:1  out:14  total:15
  nlp2dsl_sdk.demos.run_code_generation_demo
    CC=6  in:1  out:14  total:15
  nlp2dsl_sdk.demos.run_email_demo
    CC=5  in:1  out:14  total:15
  nlp2dsl_sdk.demos._run_gallery_examples
    CC=5  in:1  out:14  total:15
  nlp2dsl_sdk.demos._run_conversation_code_example
    CC=3  in:1  out:14  total:15

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
  nlp-service.app.audio_parser  [3 funcs]
    send_audio  CC=2  out:2
    stt_audio  CC=9  out:14
    stt_file  CC=2  out:4
  nlp-service.app.mapper  [5 funcs]
    _build_config  CC=6  out:10
    _get_field_mapping  CC=1  out:1
    _make_name  CC=3  out:2
    _resolve_actions  CC=7  out:4
    map_to_dsl  CC=8  out:17
  nlp-service.app.orchestrator  [11 funcs]
    _build_and_check_dsl  CC=9  out:9
    _build_incomplete_response  CC=7  out:10
    _check_execute_keyword  CC=5  out:5
    _format_system_result  CC=16  out:38
    _handle_system_action  CC=7  out:7
    _handle_unknown_intent  CC=3  out:2
    _merge_into_state  CC=9  out:4
    _process_message  CC=5  out:8
    continue_conversation  CC=2  out:8
    get_action_form  CC=5  out:12
  nlp-service.app.parser_llm  [3 funcs]
    _detect_provider  CC=10  out:8
    _parse_json_response  CC=6  out:10
    parse_llm  CC=3  out:16
  nlp-service.app.parser_rules  [13 funcs]
    _detect_actions  CC=15  out:9
    _extract_amount  CC=5  out:7
    _extract_email  CC=2  out:2
    _extract_entities  CC=1  out:9
    _extract_fallback_recipient  CC=7  out:5
    _extract_format  CC=3  out:1
    _extract_notification_channels  CC=6  out:6
    _extract_param_aliases  CC=5  out:5
    _extract_report_type  CC=3  out:1
    _extract_system_entities  CC=16  out:8
  nlp-service.app.parsing.facade  [1 funcs]
    parse_text  CC=8  out:8
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
  nlp2dsl_sdk.__main__.main → nlp2dsl_sdk.demos.list_available_demos
  examples.code_generation_examples.main → nlp2dsl_sdk.demos.run_code_generation_demo
  examples.04-scheduled-report.main.main → nlp2dsl_sdk.demos.run_scheduled_report_demo
  examples.01-invoice.main.main → nlp2dsl_sdk.demos.run_invoice_demo
  examples.03-report-and-notify.main.main → nlp2dsl_sdk.demos.run_report_and_notify_demo
  examples.02-email.main.main → nlp2dsl_sdk.demos.run_email_demo
  nlp-service.app.audio_parser.stt_file → nlp-service.app.audio_parser.stt_audio
  nlp-service.app.audio_parser.StreamingSTT.send_audio → nlp-service.app.audio_parser.stt_audio
  nlp-service.app.parser_llm.parse_llm → nlp-service.app.parser_llm._detect_provider
  nlp-service.app.parser_llm.parse_llm → nlp-service.app.parser_llm._parse_json_response
  nlp-service.app.mapper.map_to_dsl → nlp-service.app.mapper._resolve_actions
  nlp-service.app.mapper.map_to_dsl → nlp-service.app.mapper._make_name
  nlp-service.app.mapper.map_to_dsl → nlp-service.app.mapper._build_config
  nlp-service.app.mapper.map_to_dsl → nlp-service.app.registry.get_trigger
  nlp-service.app.mapper._build_config → nlp-service.app.registry.get_required_fields
  nlp-service.app.mapper._build_config → nlp-service.app.registry.get_defaults
  nlp-service.app.mapper._build_config → nlp-service.app.mapper._get_field_mapping
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
# generated in 0.06s
# nodes: 132 | edges: 138 | modules: 28
# CC̄=2.8

HUBS[20]:
  backend.app.engine._execute_workflow
    CC=11  in:2  out:42  total:44
  nlp-service.app.orchestrator._format_system_result
    CC=16  in:1  out:38  total:39
  backend.app.routers.workflow.stream_workflow
    CC=2  in:0  out:22  total:22
  backend.app.routers.chat.chat_message
    CC=12  in:0  out:21  total:21
  nlp-service.app.mapper.map_to_dsl
    CC=8  in:2  out:17  total:19
  worker.worker._deliver_notification
    CC=5  in:3  out:16  total:19
  nlp2dsl_sdk.demos._print_workflow_preview
    CC=4  in:3  out:16  total:19
  nlp2dsl_sdk.demos.run_action_catalog_demo
    CC=6  in:0  out:19  total:19
  nlp-service.app.system_executor._exec_file_read
    CC=9  in:0  out:18  total:18
  backend.app.routers.chat._proxy_chat_payload
    CC=9  in:2  out:16  total:18
  nlp2dsl_sdk.demos._print_execution_result
    CC=5  in:7  out:11  total:18
  nlp-service.app.parser_llm.parse_llm
    CC=3  in:2  out:16  total:18
  worker.worker.handle_generate_code
    CC=5  in:0  out:17  total:17
  nlp-service.app.settings.SettingsManager.set
    CC=4  in:5  out:11  total:16
  nlp-service.app.audio_parser.stt_audio
    CC=9  in:2  out:14  total:16
  nlp2dsl_sdk.demos.run_invoice_demo
    CC=5  in:1  out:14  total:15
  nlp2dsl_sdk.demos.run_code_generation_demo
    CC=6  in:1  out:14  total:15
  nlp2dsl_sdk.demos.run_email_demo
    CC=5  in:1  out:14  total:15
  nlp2dsl_sdk.demos._run_gallery_examples
    CC=5  in:1  out:14  total:15
  nlp2dsl_sdk.demos._run_conversation_code_example
    CC=3  in:1  out:14  total:15

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
  nlp-service.app.audio_parser  [3 funcs]
    send_audio  CC=2  out:2
    stt_audio  CC=9  out:14
    stt_file  CC=2  out:4
  nlp-service.app.mapper  [5 funcs]
    _build_config  CC=6  out:10
    _get_field_mapping  CC=1  out:1
    _make_name  CC=3  out:2
    _resolve_actions  CC=7  out:4
    map_to_dsl  CC=8  out:17
  nlp-service.app.orchestrator  [11 funcs]
    _build_and_check_dsl  CC=9  out:9
    _build_incomplete_response  CC=7  out:10
    _check_execute_keyword  CC=5  out:5
    _format_system_result  CC=16  out:38
    _handle_system_action  CC=7  out:7
    _handle_unknown_intent  CC=3  out:2
    _merge_into_state  CC=9  out:4
    _process_message  CC=5  out:8
    continue_conversation  CC=2  out:8
    get_action_form  CC=5  out:12
  nlp-service.app.parser_llm  [3 funcs]
    _detect_provider  CC=10  out:8
    _parse_json_response  CC=6  out:10
    parse_llm  CC=3  out:16
  nlp-service.app.parser_rules  [13 funcs]
    _detect_actions  CC=15  out:9
    _extract_amount  CC=5  out:7
    _extract_email  CC=2  out:2
    _extract_entities  CC=1  out:9
    _extract_fallback_recipient  CC=7  out:5
    _extract_format  CC=3  out:1
    _extract_notification_channels  CC=6  out:6
    _extract_param_aliases  CC=5  out:5
    _extract_report_type  CC=3  out:1
    _extract_system_entities  CC=16  out:8
  nlp-service.app.parsing.facade  [1 funcs]
    parse_text  CC=8  out:8
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
  nlp2dsl_sdk.__main__.main → nlp2dsl_sdk.demos.list_available_demos
  examples.code_generation_examples.main → nlp2dsl_sdk.demos.run_code_generation_demo
  examples.04-scheduled-report.main.main → nlp2dsl_sdk.demos.run_scheduled_report_demo
  examples.01-invoice.main.main → nlp2dsl_sdk.demos.run_invoice_demo
  examples.03-report-and-notify.main.main → nlp2dsl_sdk.demos.run_report_and_notify_demo
  examples.02-email.main.main → nlp2dsl_sdk.demos.run_email_demo
  nlp-service.app.audio_parser.stt_file → nlp-service.app.audio_parser.stt_audio
  nlp-service.app.audio_parser.StreamingSTT.send_audio → nlp-service.app.audio_parser.stt_audio
  nlp-service.app.parser_llm.parse_llm → nlp-service.app.parser_llm._detect_provider
  nlp-service.app.parser_llm.parse_llm → nlp-service.app.parser_llm._parse_json_response
  nlp-service.app.mapper.map_to_dsl → nlp-service.app.mapper._resolve_actions
  nlp-service.app.mapper.map_to_dsl → nlp-service.app.mapper._make_name
  nlp-service.app.mapper.map_to_dsl → nlp-service.app.mapper._build_config
  nlp-service.app.mapper.map_to_dsl → nlp-service.app.registry.get_trigger
  nlp-service.app.mapper._build_config → nlp-service.app.registry.get_required_fields
  nlp-service.app.mapper._build_config → nlp-service.app.registry.get_defaults
  nlp-service.app.mapper._build_config → nlp-service.app.mapper._get_field_mapping
```

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 92f 8693L | python:51,yaml:7,shell:7,toml:5,txt:4,json:3,rust:2,javascript:2,yml:2,ini:1 | 2026-06-04
# generated in 0.02s
# CC̅=2.8 | critical:3/298 | dups:0 | cycles:0

HEALTH[3]:
  🟡 CC    _detect_actions CC=15 (limit:15)
  🟡 CC    _extract_system_entities CC=16 (limit:15)
  🟡 CC    _format_system_result CC=16 (limit:15)

REFACTOR[1]:
  1. split 3 high-CC methods  (CC>15)

PIPELINES[198]:
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
  [22] Src [__init__]: __init__
      PURITY: 100% pure
  [23] Src [format]: format
      PURITY: 100% pure
  [24] Src [__init__]: __init__
      PURITY: 100% pure
  [25] Src [dispatch]: dispatch
      PURITY: 100% pure
  [26] Src [setup_logging]: setup_logging
      PURITY: 100% pure
  [27] Src [to_dict]: to_dict
      PURITY: 100% pure
  [28] Src [__init__]: __init__
      PURITY: 100% pure
  [29] Src [subscribe]: subscribe
      PURITY: 100% pure
  [30] Src [unsubscribe]: unsubscribe
      PURITY: 100% pure
  [31] Src [publish]: publish → set → _coerce_type
      PURITY: 100% pure
  [32] Src [subscriber_count]: subscriber_count → set → _coerce_type
      PURITY: 100% pure
  [33] Src [health]: health
      PURITY: 100% pure
  [34] Src [__init__]: __init__
      PURITY: 100% pure
  [35] Src [save_run]: save_run
      PURITY: 100% pure
  [36] Src [get_run]: get_run
      PURITY: 100% pure
  [37] Src [list_runs]: list_runs
      PURITY: 100% pure
  [38] Src [count_runs]: count_runs
      PURITY: 100% pure
  [39] Src [create_workflow_repo]: create_workflow_repo
      PURITY: 100% pure
  [40] Src [to_dict]: to_dict
      PURITY: 100% pure
  [41] Src [__init__]: __init__
      PURITY: 100% pure
  [42] Src [_ensure_engine]: _ensure_engine
      PURITY: 100% pure
  [43] Src [_get_session_factory]: _get_session_factory
      PURITY: 100% pure
  [44] Src [_ensure_tables]: _ensure_tables
      PURITY: 100% pure
  [45] Src [save_run]: save_run
      PURITY: 100% pure
  [46] Src [update_run_status]: update_run_status
      PURITY: 100% pure
  [47] Src [get_run]: get_run
      PURITY: 100% pure
  [48] Src [list_runs]: list_runs
      PURITY: 100% pure
  [49] Src [count_runs]: count_runs
      PURITY: 100% pure
  [50] Src [close]: close
      PURITY: 100% pure

LAYERS:
  nlp-service/                    CC̄=3.9    ←in:0  →out:0
  │ !! orchestrator               397L  0C   12m  CC=16     ←0
  │ registry                   390L  0C    4m  CC=5      ←3
  │ system_executor            342L  0C   13m  CC=12     ←0
  │ !! parser_rules               320L  0C   13m  CC=16     ←1
  │ code_generator             279L  1C    8m  CC=14     ←0
  │ settings                   251L  6C   11m  CC=6      ←3
  │ mapper                     189L  0C    6m  CC=8      ←1
  │ parser_llm                 187L  0C    3m  CC=10     ←1
  │ audio_parser               148L  1C    8m  CC=9      ←0
  │ schemas                    130L  11C    0m  CC=0.0    ←0
  │ logging_setup              100L  2C    6m  CC=3      ←0
  │ registry                    66L  0C    0m  CC=0.0    ←0
  │ loader                      62L  0C    3m  CC=5      ←0
  │ config                      60L  1C    0m  CC=0.0    ←0
  │ redis_store                 58L  1C    7m  CC=3      ←0
  │ pyproject.toml              52L  0C    0m  CC=0.0    ←0
  │ factory                     46L  0C    1m  CC=4      ←0
  │ facade                      39L  0C    1m  CC=8      ←1
  │ __init__                    30L  1C    4m  CC=1      ←0
  │ manifest.json               30L  0C    0m  CC=0.0    ←0
  │ memory                      23L  1C    5m  CC=1      ←0
  │ Dockerfile                  14L  0C    0m  CC=0.0    ←0
  │ requirements.txt             9L  0C    0m  CC=0.0    ←0
  │ __init__                     5L  0C    0m  CC=0.0    ←0
  │ __init__                     3L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
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
  nlp2dsl_sdk/                    CC̄=2.4    ←in:5  →out:0
  │ !! demos                      687L  1C   22m  CC=6      ←6
  │ !! client                     580L  2C   51m  CC=6      ←0
  │ __main__                    41L  0C    1m  CC=5      ←0
  │ __init__                    33L  0C    0m  CC=0.0    ←0
  │
  backend/                        CC̄=2.2    ←in:0  →out:0
  │ engine                     269L  0C    7m  CC=11     ←2
  │ workflow                   189L  0C    9m  CC=8      ←0
  │ postgres                   172L  3C   11m  CC=4      ←0
  │ chat                       124L  0C    4m  CC=12     ←0
  │ logging_setup              100L  2C    6m  CC=3      ←5
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
  │
  worker/                         CC̄=1.7    ←in:0  →out:0
  │ worker                     230L  0C   12m  CC=5      ←0
  │ logging_setup              100L  2C    6m  CC=3      ←0
  │ pyproject.toml              46L  0C    0m  CC=0.0    ←0
  │ config                      27L  1C    0m  CC=0.0    ←0
  │ Dockerfile                  11L  0C    0m  CC=0.0    ←0
  │ __init__                     5L  0C    0m  CC=0.0    ←0
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
  │ requirements.txt             1L  0C    0m  CC=0.0    ←0
  │
  ./                              CC̄=0.0    ←in:0  →out:0
  │ !! goal.yaml                  512L  0C    0m  CC=0.0    ←0
  │ planfile.yaml              448L  0C    0m  CC=0.0    ←0
  │ docker-compose.yml         108L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                82L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              61L  0C    0m  CC=0.0    ←0
  │ project.sh                  59L  0C    0m  CC=0.0    ←0
  │ metrun-profile.sh           48L  0C    0m  CC=0.0    ←0
  │ run-all-tests.sh            44L  0C    1m  CC=0.0    ←0
  │ pyqual.yaml                 41L  0C    0m  CC=0.0    ←0
  │ .pfix-test-wrapper.sh       16L  0C    0m  CC=0.0    ←0
  │ tree.sh                      1L  0C    0m  CC=0.0    ←0
  │
  testql-scenarios/               CC̄=0.0    ←in:0  →out:0
  │ generated-from-pytests.testql.toon.yaml   128L  0C    0m  CC=0.0    ←0
  │ generated-api-smoke.testql.toon.yaml    39L  0C    0m  CC=0.0    ←0
  │ generated-cli-tests.testql.toon.yaml    20L  0C    0m  CC=0.0    ←0
  │
  ── zero ──
     backend/app/__init__.py                   0L

COUPLING:
                                                   nlp2dsl_sdk                nlp-service.app                    backend.app                       examples            examples.01-invoice              examples.02-email  examples.03-report-and-notify   examples.04-scheduled-report       nlp-service.integrations
                    nlp2dsl_sdk                             ──                                                                                           ←1                             ←1                             ←1                             ←1                             ←1                                 hub
                nlp-service.app                                                            ──                             ←2                                                                                                                                                                                        ←1
                    backend.app                                                             2                             ──                                                                                                                                                                                          
                       examples                              1                                                                                           ──                                                                                                                                                           
            examples.01-invoice                              1                                                                                                                          ──                                                                                                                            
              examples.02-email                              1                                                                                                                                                         ──                                                                                             
  examples.03-report-and-notify                              1                                                                                                                                                                                        ──                                                              
   examples.04-scheduled-report                              1                                                                                                                                                                                                                       ──                               
       nlp-service.integrations                                                             1                                                                                                                                                                                                                       ──
  CYCLES: none
  HUB: nlp2dsl_sdk/ (fan-in=5)

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 11 groups | 54f 6822L | 2026-06-04

SUMMARY:
  files_scanned: 54
  total_lines:   6822
  dup_groups:    11
  dup_fragments: 30
  saved_lines:   146
  scan_ms:       2194

HOTSPOTS[7] (files with most duplication):
  backend/app/logging_setup.py  dup=49L  groups=5  frags=5  (0.7%)
  nlp-service/app/logging_setup.py  dup=49L  groups=5  frags=5  (0.7%)
  worker/logging_setup.py  dup=49L  groups=5  frags=5  (0.7%)
  backend/app/routers/settings.py  dup=24L  groups=2  frags=4  (0.4%)
  worker/worker.py  dup=22L  groups=1  frags=2  (0.3%)
  nlp-service/app/parser_rules.py  dup=12L  groups=1  frags=2  (0.2%)
  backend/app/routers/workflow.py  dup=6L  groups=1  frags=2  (0.1%)

DUPLICATES[11] (ranked by impact):
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
  [d8abcb97f9e3aea3]   STRU  _extract_report_type  L=6 N=2 saved=6 sim=1.00
      nlp-service/app/parser_rules.py:216-221  (_extract_report_type)
      nlp-service/app/parser_rules.py:224-229  (_extract_format)
  [2ce1096adac6d1a4]   STRU  actions_schema  L=5 N=2 saved=5 sim=1.00
      backend/app/routers/settings.py:21-25  (actions_schema)
      backend/app/routers/settings.py:39-43  (get_settings)
  [8af82767bfb2b892]   STRU  run_workflow_endpoint  L=3 N=2 saved=3 sim=1.00
      backend/app/routers/workflow.py:67-69  (run_workflow_endpoint)
      backend/app/routers/workflow.py:73-75  (start_workflow_endpoint)

REFACTOR[11] (ranked by priority):
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
  [9] ○ extract_function   → nlp-service/app/utils/_extract_report_type.py
      WHY: 2 occurrences of 6-line block across 1 files — saves 6 lines
      FILES: nlp-service/app/parser_rules.py
  [10] ○ extract_function   → backend/app/routers/utils/actions_schema.py
      WHY: 2 occurrences of 5-line block across 1 files — saves 5 lines
      FILES: backend/app/routers/settings.py
  [11] ○ extract_function   → backend/app/routers/utils/run_workflow_endpoint.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: backend/app/routers/workflow.py

QUICK_WINS[4] (low risk, high savings — do first):
  [4] extract_function   saved=16L  → examples/utils/main.py
      FILES: main.py, main.py, main.py +2
  [5] extract_function   saved=11L  → worker/utils/handle_notify_slack.py
      FILES: worker.py
  [6] extract_function   saved=7L  → backend/app/routers/utils/action_schema.py
      FILES: settings.py
  [9] extract_function   saved=6L  → nlp-service/app/utils/_extract_report_type.py
      FILES: parser_rules.py

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

EFFORT_ESTIMATE (total ≈ 8.1h):
  hard   setup_logging                       saved=44L  ~176min
  hard   format                              saved=24L  ~96min
  medium dispatch                            saved=18L  ~72min
  medium main                                saved=16L  ~32min
  easy   handle_notify_slack                 saved=11L  ~22min
  easy   action_schema                       saved=7L  ~14min
  easy   __init__                            saved=6L  ~24min
  easy   __init__                            saved=6L  ~24min
  easy   _extract_report_type                saved=6L  ~12min
  easy   actions_schema                      saved=5L  ~10min
  ... +1 more (~6min)

METRICS-TARGET:
  dup_groups:  11 → 0
  saved_lines: 146 lines recoverable
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 264 func | 35f | 2026-06-04
# generated in 0.00s

NEXT[6] (ranked by impact):
  [1] !! SPLIT           nlp2dsl_sdk/demos.py
      WHY: 687L, 1 classes, max CC=6
      EFFORT: ~4h  IMPACT: 4122

  [2] !! SPLIT           nlp2dsl_sdk/client.py
      WHY: 580L, 2 classes, max CC=6
      EFFORT: ~4h  IMPACT: 3480

  [3] !  SPLIT-FUNC      _extract_system_entities  CC=16  fan=8
      WHY: CC=16 exceeds 15
      EFFORT: ~1h  IMPACT: 128

  [4] !  SPLIT-FUNC      _format_system_result  CC=16  fan=7
      WHY: CC=16 exceeds 15
      EFFORT: ~1h  IMPACT: 112

  [5] !  SPLIT-FUNC      _detect_actions  CC=15  fan=6
      WHY: CC=15 exceeds 15
      EFFORT: ~1h  IMPACT: 90

  [6] !! SPLIT           goal.yaml
      WHY: 512L, 0 classes, max CC=0
      EFFORT: ~4h  IMPACT: 0


RISKS[3]:
  ⚠ Splitting nlp2dsl_sdk/demos.py may break 22 import paths
  ⚠ Splitting nlp2dsl_sdk/client.py may break 51 import paths
  ⚠ Splitting goal.yaml may break 0 import paths

METRICS-TARGET:
  CC̄:          2.9 → ≤2.0
  max-CC:      16 → ≤8
  god-modules: 3 → 0
  high-CC(≥15): 3 → ≤1
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
  prev CC̄=2.9 → now CC̄=2.9
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
