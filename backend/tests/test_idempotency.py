from __future__ import annotations

import pytest

from app.idempotency import (
    MemoryIdempotencyStore,
    PostgresIdempotencyStore,
    create_idempotency_store,
    workflow_fingerprint,
)


@pytest.mark.asyncio
async def test_memory_idempotency_replays_finished_response() -> None:
    store = MemoryIdempotencyStore()
    fingerprint = workflow_fingerprint({"name": "wf", "steps": []})

    status, response = await store.start("key-1", fingerprint)
    assert status == "started"
    assert response is None

    await store.finish("key-1", {"status": "executed", "result": {"workflow_id": "wf-1"}})

    status, response = await store.start("key-1", fingerprint)
    assert status == "replay"
    assert response == {"status": "executed", "result": {"workflow_id": "wf-1"}}


@pytest.mark.asyncio
async def test_memory_idempotency_detects_conflict_and_in_progress() -> None:
    store = MemoryIdempotencyStore()
    first = workflow_fingerprint({"name": "wf", "steps": []})
    second = workflow_fingerprint({"name": "other", "steps": []})

    assert await store.start("key-1", first) == ("started", None)
    assert await store.start("key-1", first) == ("in_progress", None)
    assert await store.start("key-1", second) == ("conflict", None)


def test_idempotency_factory_uses_memory_without_postgres() -> None:
    assert isinstance(create_idempotency_store(postgres_url=""), MemoryIdempotencyStore)


def test_idempotency_factory_uses_postgres_with_url() -> None:
    store = create_idempotency_store("postgresql://user:pass@localhost:5432/testdb")
    assert isinstance(store, PostgresIdempotencyStore)


def test_workflow_fingerprint_ignores_empty_optional_fields() -> None:
    from app.idempotency import normalize_workflow_for_fingerprint

    a = {
        "name": "auto_send_invoice",
        "steps": [{"action": "send_invoice", "config": {"amount": 500, "to": "a@b.pl"}}],
    }
    b = {
        "name": "auto_send_invoice",
        "steps": [
            {
                "action": "send_invoice",
                "config": {"amount": 500, "to": "a@b.pl", "attachment_path": ""},
            }
        ],
    }
    assert workflow_fingerprint(a) == workflow_fingerprint(b)
    assert normalize_workflow_for_fingerprint(a)["steps"][0]["config"] == {
        "amount": 500,
        "to": "a@b.pl",
    }
