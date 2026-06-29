import pytest

from mcp2nlp2dsl.server import build_mcp


def test_mcp_server_registers_tools() -> None:
    pytest.importorskip("mcp")
    mcp = build_mcp(name="test-nlp2dsl")
    assert mcp is not None
