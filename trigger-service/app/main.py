"""Minimal trigger ingress — webhooks and schedules → NLP2DSL backend."""

from __future__ import annotations

import os
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException

BACKEND_URL = os.getenv("NLP2DSL_BACKEND_URL", "http://localhost:8010").rstrip("/")
TIMEOUT = float(os.getenv("NLP2DSL_TRIGGER_TIMEOUT", "30"))

app = FastAPI(title="NLP2DSL Trigger Service", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "trigger-service", "backend": BACKEND_URL}


async def _post_backend(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(f"{BACKEND_URL}{path}", json=payload)
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()


@app.post("/triggers/webhook/{trigger_id}")
async def webhook_trigger(trigger_id: str, body: dict[str, Any]) -> dict[str, Any]:
    """Map webhook payload to workflow plan or execute."""
    text = str(body.get("text") or body.get("query") or "").strip()
    execute = bool(body.get("execute", False))
    if text:
        path = "/workflow/from-text"
        payload: dict[str, Any] = {"text": text, "mode": body.get("mode", "auto")}
        if execute:
            payload["execute"] = True
        result = await _post_backend(path, payload)
    elif body.get("workflow"):
        path = "/workflow/execute" if execute else "/workflow/plan"
        result = await _post_backend(path, body)
    else:
        raise HTTPException(status_code=400, detail="Provide 'text' or 'workflow' in body")

    return {
        "trigger_id": trigger_id,
        "source": "webhook",
        "execute": execute,
        "result": result,
    }


@app.post("/triggers/event")
async def event_trigger(body: dict[str, Any]) -> dict[str, Any]:
    """Normalized system event → workflow."""
    event_type = str(body.get("event_type") or body.get("type") or "unknown")
    text = str(body.get("text") or "").strip()
    if not text and body.get("payload"):
        text = f"Obsłuż zdarzenie {event_type}: {body['payload']}"
    if not text:
        raise HTTPException(status_code=400, detail="Event requires 'text' or 'payload'")

    execute = bool(body.get("execute", False))
    payload: dict[str, Any] = {"text": text, "mode": body.get("mode", "auto")}
    if execute:
        payload["execute"] = True
    result = await _post_backend("/workflow/from-text", payload)
    return {"source": "event", "event_type": event_type, "result": result}
