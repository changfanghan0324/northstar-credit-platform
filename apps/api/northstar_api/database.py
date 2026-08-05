"""SQLAlchemy persistence for anonymous educational credit cases."""

from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, DateTime, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    pass


class CaseRecord(Base):
    __tablename__ = "credit_cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(80), index=True)
    slug: Mapped[str] = mapped_column(String(120), index=True)
    input_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    analysis_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


def _database_url() -> str:
    configured = os.environ.get("DATABASE_URL")
    if configured:
        return configured.replace("postgres://", "postgresql+psycopg://", 1)
    return "sqlite+pysqlite:////tmp/northstar-credit.db"


engine = create_engine(_database_url(), pool_pre_ping=True)


def initialize_database() -> None:
    Base.metadata.create_all(engine)


def session_scope() -> Iterator[Session]:
    with Session(engine) as session:
        yield session


def create_case(
    session: Session,
    *,
    session_id: str,
    slug: str,
    input_json: dict[str, Any],
    analysis_json: dict[str, Any] | None,
) -> CaseRecord:
    now = datetime.now(UTC)
    record = CaseRecord(
        id=str(uuid4()),
        session_id=session_id,
        slug=slug,
        input_json=input_json,
        analysis_json=analysis_json,
        created_at=now,
        updated_at=now,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def get_case(session: Session, case_id: str, session_id: str) -> CaseRecord | None:
    return session.scalar(
        select(CaseRecord).where(
            CaseRecord.id == case_id, CaseRecord.session_id == session_id
        )
    )
