"""Idempotency stores for workflow execution requests."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from collections.abc import Mapping
from typing import Any, Literal

from sqlalchemy import Column, DateTime, String, delete, select, update
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

IdempotencyStartStatus = Literal["started", "replay", "conflict", "in_progress"]
log = logging.getLogger("backend.idempotency")


@dataclass
class IdempotencyRecord:
    key: str
    fingerprint: str
    status: str
    response: dict[str, Any] | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class IdempotencyStore:
    """Async idempotency store interface."""

    async def start(
        self,
        key: str,
        fingerprint: str,
    ) -> tuple[IdempotencyStartStatus, dict[str, Any] | None]:
        raise NotImplementedError

    async def finish(self, key: str, response: dict[str, Any], *, status: str = "completed") -> None:
        raise NotImplementedError

    async def clear(self) -> None:
        raise NotImplementedError


class MemoryIdempotencyStore(IdempotencyStore):
    """Process-local fallback idempotency store."""

    def __init__(self) -> None:
        self._records: dict[str, IdempotencyRecord] = {}
        self._lock = asyncio.Lock()

    async def start(
        self,
        key: str,
        fingerprint: str,
    ) -> tuple[IdempotencyStartStatus, dict[str, Any] | None]:
        async with self._lock:
            record = self._records.get(key)
            if record is None:
                self._records[key] = IdempotencyRecord(
                    key=key,
                    fingerprint=fingerprint,
                    status="in_progress",
                )
                return "started", None
            if record.fingerprint != fingerprint:
                return "conflict", None
            if record.status == "in_progress":
                return "in_progress", None
            return "replay", dict(record.response or {})

    async def finish(self, key: str, response: dict[str, Any], *, status: str = "completed") -> None:
        async with self._lock:
            record = self._records.get(key)
            if record is None:
                return
            record.status = status
            record.response = dict(response)
            record.updated_at = datetime.now(UTC)

    async def clear(self) -> None:
        async with self._lock:
            self._records.clear()


class Base(DeclarativeBase):
    pass


class IdempotencyRecordModel(Base):
    __tablename__ = "workflow_idempotency"

    key = Column(String(255), primary_key=True)
    fingerprint = Column(String(64), nullable=False, index=True)
    status = Column(String(32), nullable=False, index=True)
    response = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), index=True)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
        onupdate=lambda: datetime.now(UTC).replace(tzinfo=None),
    )


class PostgresIdempotencyStore(IdempotencyStore):
    """Durable idempotency store backed by PostgreSQL."""

    def __init__(self, database_url: str):
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        self._database_url = database_url
        self._engine = None
        self._session_factory = None
        self._initialized = False
        log.info("Postgres idempotency store configured: %s", database_url.split("@")[-1])

    def _ensure_engine(self):
        if self._engine is None:
            self._engine = create_async_engine(
                self._database_url,
                echo=False,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
            )
        if self._session_factory is None:
            self._session_factory = async_sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
        return self._engine

    def _get_session_factory(self):
        self._ensure_engine()
        return self._session_factory

    async def _ensure_tables(self) -> None:
        if self._initialized:
            return
        engine = self._ensure_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self._initialized = True
        log.info("Idempotency tables ensured")

    async def start(
        self,
        key: str,
        fingerprint: str,
    ) -> tuple[IdempotencyStartStatus, dict[str, Any] | None]:
        await self._ensure_tables()
        now = datetime.now(UTC).replace(tzinfo=None)
        async with self._get_session_factory()() as session:
            statement = (
                pg_insert(IdempotencyRecordModel)
                .values(
                    key=key,
                    fingerprint=fingerprint,
                    status="in_progress",
                    response=None,
                    created_at=now,
                    updated_at=now,
                )
                .on_conflict_do_nothing(index_elements=[IdempotencyRecordModel.key])
                .returning(IdempotencyRecordModel.key)
            )
            inserted = (await session.execute(statement)).scalar_one_or_none()
            await session.commit()
            if inserted:
                return "started", None

        async with self._get_session_factory()() as session:
            result = await session.get(IdempotencyRecordModel, key)
            if result is None:
                log.warning("idempotency insert conflict but row missing for key=%s", key)
                return "in_progress", None
            if result.fingerprint != fingerprint:
                return "conflict", None
            if result.status == "in_progress":
                return "in_progress", None
            return "replay", dict(result.response or {})

    async def finish(self, key: str, response: dict[str, Any], *, status: str = "completed") -> None:
        await self._ensure_tables()
        async with self._get_session_factory()() as session:
            await session.execute(
                update(IdempotencyRecordModel)
                .where(IdempotencyRecordModel.key == key)
                .values(
                    status=status,
                    response=response,
                    updated_at=datetime.now(UTC).replace(tzinfo=None),
                )
            )
            await session.commit()

    async def clear(self) -> None:
        await self._ensure_tables()
        async with self._get_session_factory()() as session:
            await session.execute(delete(IdempotencyRecordModel))
            await session.commit()

    async def close(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()


def workflow_fingerprint(workflow: Any) -> str:
    normalized = normalize_workflow_for_fingerprint(workflow)
    payload = json.dumps(normalized, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def normalize_workflow_for_fingerprint(workflow: Any) -> dict[str, Any]:
    """Stable fingerprint input — ignores empty optional fields and step order drift."""
    if not isinstance(workflow, Mapping):
        return {}
    steps: list[dict[str, Any]] = []
    for step in workflow.get("steps") or []:
        if not isinstance(step, Mapping):
            continue
        raw_cfg = step.get("config") if isinstance(step.get("config"), Mapping) else {}
        config = {
            str(k): v
            for k, v in raw_cfg.items()
            if v is not None and v != "" and v != [] and v != {}
        }
        steps.append({"action": str(step.get("action") or ""), "config": config})
    steps.sort(
        key=lambda item: (
            item["action"],
            json.dumps(item["config"], sort_keys=True, ensure_ascii=False),
        )
    )
    out: dict[str, Any] = {}
    if workflow.get("name"):
        out["name"] = workflow.get("name")
    if workflow.get("trigger"):
        out["trigger"] = workflow.get("trigger")
    out["steps"] = steps
    return out


def create_idempotency_store(postgres_url: str | None = None) -> IdempotencyStore:
    """Factory mirroring workflow history persistence settings."""
    if postgres_url is None:
        from app.config import BackendSettings

        postgres_url = BackendSettings().postgres_url
    if postgres_url:
        return PostgresIdempotencyStore(postgres_url)
    return MemoryIdempotencyStore()


idempotency_store = create_idempotency_store()
