import json

from pact_ir import ExecutionPlanIR, PlanStep, TargetKind

from nlp2cmd_propact import plan_to_propact_markdown, step_to_propact_block


def test_shell_plan_to_markdown():
    plan = ExecutionPlanIR(
        query="find py",
        source="rule_shell",
        steps=[
            PlanStep(
                id="s1",
                action="shell_find",
                target_kind=TargetKind.SHELL,
                dsl='find . -name "*.py"',
            )
        ],
    )
    md = plan_to_propact_markdown(plan)
    assert "```propact:shell" in md
    assert 'find . -name "*.py"' in md


def test_rest_block_with_json_body():
    step = PlanStep(
        id="s1",
        action="http_post",
        target_kind=TargetKind.REST,
        params={
            "method": "POST",
            "endpoint": "/api/chat/message",
            "body": {"session_id": "abc", "message": "hello"},
        },
    )
    block = step_to_propact_block(step)
    assert "```propact:rest" in block
    assert "POST /api/chat/message" in block
    assert '"session_id": "abc"' in block


def test_mcp_block_from_tool_params():
    step = PlanStep(
        id="s1",
        action="mcp_call",
        target_kind=TargetKind.MCP,
        params={
            "tool": "file_editor",
            "arguments": {"file_path": "out.txt", "content": "data"},
        },
    )
    block = step_to_propact_block(step)
    assert "```propact:mcp" in block
    payload = json.loads(block.split("```propact:mcp\n", 1)[1].rsplit("\n```", 1)[0])
    assert payload["method"] == "tools/call"
    assert payload["params"]["name"] == "file_editor"


def test_mcp_block_from_dsl():
    step = PlanStep(
        id="s1",
        action="mcp_call",
        target_kind=TargetKind.MCP,
        dsl='{"method": "tools/list", "id": 1}',
    )
    block = step_to_propact_block(step)
    assert '"tools/list"' in block


def test_ws_block_from_url_and_message():
    step = PlanStep(
        id="s1",
        action="ws_send",
        target_kind=TargetKind.WS,
        params={
            "type": "message",
            "url": "ws://localhost:8080/events",
            "data": {"action": "subscribe", "channel": "updates"},
        },
    )
    block = step_to_propact_block(step)
    assert "```propact:ws" in block
    assert "ws://localhost:8080/events" in block
    assert "subscribe" in block


def test_delegate_block_for_browser():
    step = PlanStep(
        id="s1",
        action="dom_click",
        target_kind=TargetKind.BROWSER,
        dsl="click #submit",
        params={"selector": "#submit"},
        description="Submit form",
    )
    block = step_to_propact_block(step)
    assert "```propact:delegate" in block
    assert "target_kind: browser" in block
    assert "action: dom_click" in block
    assert "selector: '#submit'" in block or 'selector: "#submit"' in block


def test_delegate_block_for_sql():
    step = PlanStep(
        id="s1",
        action="sql_query",
        target_kind=TargetKind.SQL,
        dsl="SELECT 1",
    )
    block = step_to_propact_block(step)
    assert "```propact:delegate" in block
    assert "target_kind: sql" in block


def test_mixed_plan_renders_all_block_types():
    plan = ExecutionPlanIR(
        query="mixed",
        source="test",
        steps=[
            PlanStep(id="s1", action="shell_find", target_kind=TargetKind.SHELL, dsl="ls"),
            PlanStep(
                id="s2",
                action="http_get",
                target_kind=TargetKind.REST,
                params={"method": "GET", "endpoint": "/health"},
            ),
            PlanStep(
                id="s3",
                action="dom_navigate",
                target_kind=TargetKind.BROWSER,
                dsl="goto https://example.com",
            ),
        ],
    )
    md = plan_to_propact_markdown(plan)
    assert "```propact:shell" in md
    assert "```propact:rest" in md
    assert "```propact:delegate" in md
