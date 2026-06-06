"""
PostgresWorkflowRepo — persystencja workflow w PostgreSQL.

Tabele tworzą się automatycznie przy starcie (create_all).
Używa asyncpg + SQLAlchemy async dla nieblokujących operacji.
"""

import logging
from collections.abc import Mapping
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.db import DEFAULT_LIST_LIMIT, WorkflowRepo

log = logging.getLogger("db.postgres")

MAX_NAME_LENGTH: int = int("255")


class Base(DeclarativeBase):
    pass


class WorkflowRunModel(Base):
    __tablename__ = "workflow_runs"

    id = Column(String(32), primary_key=True)
    name = Column(String(MAX_NAME_LENGTH), nullable=False, index=True)
    status = Column(String(32), nullable=False, index=True)
    trigger = Column(String(32), default="manual")
    steps = Column(JSONB, default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), onupdate=lambda: datetime.now(UTC).replace(tzinfo=None))

    def to_dict(self) -> dict:
        return {
            "workflow_id": self.id,
            "name": self.name,
            "status": self.status,
            "trigger": self.trigger,
            "steps": self.steps or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class WorkflowEventModel(Base):
    __tablename__ = "workflow_events"

    id = Column(String(64), primary_key=True)
    workflow_id = Column(String(32), nullable=False, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    data = Column(JSONB, nullable=False, default=dict)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
        index=True,
    )


class PostgresWorkflowRepo(WorkflowRepo):

    def __init__(self, database_url: str):
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

        self._database_url = database_url
        self._engine = None
        self._session_factory = None
        self._initialized = False
        log.info("Postgres workflow repo configured: %s", database_url.split("@")[-1])

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
        log.info("Database tables ensured")

    async def save_run(self, workflow_id: str, name: str, status: str, data: dict) -> None:
        await self._ensure_tables()

        async with self._get_session_factory()() as session:
            now = datetime.now(UTC).replace(tzinfo=None)
            statement = pg_insert(WorkflowRunModel).values(
                id=workflow_id,
                name=name,
                status=status,
                trigger=data.get("trigger", "manual"),
                steps=data.get("steps", []),
                created_at=now,
                updated_at=now,
            )
            statement = statement.on_conflict_do_update(
                index_elements=[WorkflowRunModel.id],
                set_={
                    "name": name,
                    "status": status,
                    "trigger": data.get("trigger", "manual"),
                    "steps": data.get("steps", []),
                    "updated_at": now,
                },
            )
            await session.execute(statement)
            await session.commit()
            log.debug("Saved workflow run %s (%s)", workflow_id, name)

    async def update_run_status(self, workflow_id: str, status: str) -> None:
        await self._ensure_tables()

        async with self._get_session_factory()() as session:
            await session.execute(
                text("UPDATE workflow_runs SET status = :status, updated_at = :now WHERE id = :id"),
                {"status": status, "now": datetime.now(UTC).replace(tzinfo=None), "id": workflow_id},
            )
            await session.commit()

    async def get_run(self, workflow_id: str) -> dict | None:
        await self._ensure_tables()

        async with self._get_session_factory()() as session:
            result = await session.get(WorkflowRunModel, workflow_id)
            if result:
                return result.to_dict()
            return None

    async def list_runs(self, limit: int = DEFAULT_LIST_LIMIT, offset: int = 0) -> list[dict]:
        await self._ensure_tables()

        async with self._get_session_factory()() as session:
            result = await session.execute(
                text(
                    "SELECT * FROM workflow_runs ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
                ),
                {"limit": limit, "offset": offset},
            )
            rows = result.mappings().all()
            return [
                {
                    "workflow_id": r["id"],
                    "name": r["name"],
                    "status": r["status"],
                    "trigger": r["trigger"],
                    "steps": r["steps"],
                    "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                }
                for r in rows
            ]

    async def count_runs(self) -> int:
        await self._ensure_tables()

        async with self._get_session_factory()() as session:
            result = await session.execute(text("SELECT COUNT(*) FROM workflow_runs"))
            return result.scalar() or 0

    async def append_event(self, workflow_id: str, event: dict) -> None:
        await self._ensure_tables()
        event_id = str(event.get("event_id") or "")
        if not event_id:
            raise ValueError("event_id is required")

        async with self._get_session_factory()() as session:
            now = datetime.now(UTC).replace(tzinfo=None)
            statement = pg_insert(WorkflowEventModel).values(
                id=event_id,
                workflow_id=workflow_id,
                event_type=str(event.get("event_type") or ""),
                data=event,
                created_at=now,
            )
            statement = statement.on_conflict_do_nothing(index_elements=[WorkflowEventModel.id])
            await session.execute(statement)
            await session.commit()

    async def list_events(
        self,
        workflow_id: str,
        *,
        limit: int = 200,
        offset: int = 0,
    ) -> list[dict]:
        await self._ensure_tables()

        async with self._get_session_factory()() as session:
            result = await session.execute(
                text(
                    """
                    SELECT data FROM workflow_events
                    WHERE workflow_id = :workflow_id
                    ORDER BY created_at ASC, id ASC
                    LIMIT :limit OFFSET :offset
                    """
                ),
                {"workflow_id": workflow_id, "limit": limit, "offset": offset},
            )
            rows = result.mappings().all()
            return [dict(row["data"]) for row in rows]

    async def close(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()
