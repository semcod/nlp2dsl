"""Sync HTTP client for Mullm orchestrator (POST /api/commands/tasks)."""

from __future__ import annotations

import os
import uuid
from typing import Any

import requests

DEFAULT_MULLM_API_URL = "http://localhost:8080"
DEFAULT_TIMEOUT_S = 30.0


class MullmClientError(RuntimeError):
    """Mullm API call failed."""

    def __init__(self, message: str, *, status_code: int | None = None, body: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class MullmClient:
    """Minimal Mullm task delegate client."""

    def __init__(
        self,
        base_url: str | None = None,
        *,
        timeout_s: float = DEFAULT_TIMEOUT_S,
        session: requests.Session | None = None,
    ):
        self.base_url = (base_url or os.environ.get("MULLM_API_URL") or DEFAULT_MULLM_API_URL).rstrip(
            "/"
        )
        self.timeout_s = timeout_s
        self._session = session or requests.Session()

    def create_task(self, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}/api/commands/tasks"
        try:
            resp = self._session.post(url, json=payload, timeout=self.timeout_s)
        except requests.RequestException as exc:
            raise MullmClientError(f"Mullm unreachable at {self.base_url}: {exc}") from exc

        if resp.status_code >= 400:
            try:
                body = resp.json()
            except ValueError:
                body = resp.text
            raise MullmClientError(
                f"Mullm API error {resp.status_code}",
                status_code=resp.status_code,
                body=body,
            )

        data = resp.json()
        if not isinstance(data, dict):
            raise MullmClientError("Mullm API returned non-object JSON", body=data)
        return data

    def simulate_task(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Offline preview when Mullm is unavailable or mode=simulate."""
        task_id = f"SIM-TASK-{uuid.uuid4().hex[:12]}"
        command_id = f"SIM-CMD-{uuid.uuid4().hex[:12]}"
        return {
            "task_id": task_id,
            "command_id": command_id,
            "status": "simulated",
            "title": payload.get("title"),
            "transport": "simulated",
            "payload_echo": payload,
        }

    def ping(self) -> bool:
        try:
            resp = self._session.get(f"{self.base_url}/health", timeout=5.0)
            return resp.status_code < 500
        except requests.RequestException:
            return False
