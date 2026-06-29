#!/usr/bin/env python3
"""Generate nlp2dsl_sdk compatibility shims after the package split."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SDK = ROOT / "nlp2dsl_sdk"

SHIMS: dict[str, str] = {
    "artifact_layout.py": "env2llm.layout",
    "artifacts.py": "nlp2dsl_artifacts",
    "compose_generator.py": "nlp2dsl_stack",
    "conversation_artifacts.py": "testql_conversations.artifacts",
    "conversation_testql.py": "testql_conversations.validate",
    "doql_context.py": "env2llm.doql_context",
    "doql_registry.py": "env2llm.registry",
    "example_bootstrap.py": "env2llm.bootstrap",
    "invoice_policy.py": "env2llm.policy.invoice",
    "path_resolve.py": "dsl_validate.path_resolve",
    "process_policy.py": "env2llm.policy.process",
    "system_map_bridge.py": "env2llm.bridge",
    "system_map_generator.py": "env2llm.generate",
    "system_map_ir.py": "env2llm.ir",
    "system_map_models.py": "env2llm.system_map_models",
    "system_map_runtimes.py": "env2llm.runtimes",
    "contracts/__init__.py": "dsl_contracts",
    "contracts/action.py": "dsl_contracts.action",
    "contracts/draft.py": "dsl_contracts.draft",
    "contracts/registry.py": "dsl_contracts.registry",
    "doql/__init__.py": "env2llm.doql",
    "doql/context_blocks.py": "env2llm.doql.context_blocks",
    "doql/models.py": "env2llm.doql.models",
    "doql/parse.py": "env2llm.doql.parse",
    "doql/render.py": "env2llm.doql.render",
    "doql/runtime.py": "env2llm.doql.runtime",
    "export/__init__.py": "workflow_export",
    "export/markpact.py": "workflow_export.markpact",
    "export/pactown.py": "workflow_export.pactown",
    "export/publish.py": "workflow_export.publish",
    "system_map_render/__init__.py": "env2llm.render.doql",
    "system_map_render/blocks.py": "env2llm.render.doql.blocks",
    "system_map_render/helpers.py": "env2llm.render.doql.helpers",
    "system_map_render/render.py": "env2llm.render.doql.render",
    "validation/__init__.py": "dsl_validate",
    "validation/capability_policy.py": "dsl_validate.capability_policy",
    "validation/context.py": "dsl_validate.context",
    "validation/contract_drift.py": "dsl_validate.contract_drift",
    "validation/helpers.py": "dsl_validate.helpers",
    "validation/issue.py": "dsl_validate.issue",
    "validation/messages.py": "dsl_validate.messages",
    "validation/pipeline.py": "dsl_validate.pipeline",
    "validation/profile_checks.py": "dsl_validate.profile_checks",
    "validation/resolutions.py": "dsl_validate.resolutions",
    "validation/rules/__init__.py": "",
    "validation/rules/attachment.py": "dsl_validate.rules.attachment",
    "validation/rules/dsl_contract.py": "dsl_validate.rules.dsl_contract",
    "validation/rules/post_execute.py": "dsl_validate.rules.post_execute",
    "validation/rules/runtime_health.py": "dsl_validate.rules.runtime_health",
    "validation/rules/step_config.py": "dsl_validate.rules.step_config",
}


def shim_body(target: str) -> str:
    if not target:
        return '"""Compatibility package for ``nlp2dsl_sdk.validation.rules``."""\n'
    return (
        f'"""Compatibility shim — prefer ``{target}`` in new code."""\n'
        f"from {target} import *  # noqa: F403\n"
    )


def main() -> None:
    for rel, target in SHIMS.items():
        path = SDK / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(shim_body(target), encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
