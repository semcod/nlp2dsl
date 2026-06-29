import pytest

from rest2nlp2dsl.app import create_app


def test_rest_health() -> None:
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    client = TestClient(create_app())
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_rest_schema() -> None:
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    client = TestClient(create_app())
    resp = client.get("/v1/schema/PARSE")
    assert resp.status_code == 200
    assert resp.json()["properties"]["verb"]["const"] == "PARSE"


def test_rest_proto() -> None:
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    client = TestClient(create_app())
    resp = client.get("/v1/proto")
    assert resp.status_code == 200
    data = resp.json()
    assert "command.proto" in data["files"]
    assert "result.proto" in data["files"]
