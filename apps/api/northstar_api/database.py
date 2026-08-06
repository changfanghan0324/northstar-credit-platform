"""SQLAlchemy persistence for anonymous educational credit cases."""

from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    create_engine,
    func,
    select,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    pass


class CaseRecord(Base):
    __tablename__ = "credit_cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(80), index=True)
    slug: Mapped[str] = mapped_column(String(120), index=True)
    title: Mapped[str] = mapped_column(String(160), default="Untitled case")
    status: Mapped[str] = mapped_column(String(24), default="draft", index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    archived: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    input_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    analysis_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class AuditRecord(Base):
    __tablename__ = "case_audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    case_id: Mapped[str] = mapped_column(
        ForeignKey("credit_cases.id", ondelete="CASCADE"), index=True
    )
    session_id: Mapped[str] = mapped_column(String(80), index=True)
    action: Mapped[str] = mapped_column(String(40))
    version: Mapped[int] = mapped_column(Integer)
    details_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CaseVersionRecord(Base):
    """Immutable input snapshot for one user-visible case version."""

    __tablename__ = "case_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    case_id: Mapped[str] = mapped_column(
        ForeignKey("credit_cases.id", ondelete="CASCADE"), index=True
    )
    case_version: Mapped[int] = mapped_column(Integer, index=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


def _database_url() -> str:
    configured = os.environ.get("DATABASE_URL")
    if configured:
        return configured.replace("postgres://", "postgresql+psycopg://", 1)
    return "sqlite+pysqlite:////tmp/northstar-credit-v3.db"


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
    title: str | None = None,
) -> CaseRecord:
    now = datetime.now(UTC)
    record = CaseRecord(
        id=str(uuid4()),
        session_id=session_id,
        slug=slug,
        title=title or slug.replace("-", " ").title(),
        status="analyzed" if analysis_json is not None else "draft",
        version=1,
        archived=False,
        input_json=input_json,
        analysis_json=analysis_json,
        created_at=now,
        updated_at=now,
        expires_at=now + timedelta(days=7),
    )
    session.add(record)
    session.add(
        CaseVersionRecord(
            id=str(uuid4()),
            case_id=record.id,
            case_version=record.version,
            payload_json={
                "title": record.title,
                "status": record.status,
                "input": input_json,
                "analysis": analysis_json,
            },
            created_at=now,
        )
    )
    session.add(
        AuditRecord(
            id=str(uuid4()),
            case_id=record.id,
            session_id=session_id,
            action="created",
            version=1,
            details_json={"analyzed": analysis_json is not None},
            created_at=now,
        )
    )
    session.commit()
    session.refresh(record)
    return record


def get_case(session: Session, case_id: str, session_id: str) -> CaseRecord | None:
    now = datetime.now(UTC)
    return session.scalar(
        select(CaseRecord).where(
            CaseRecord.id == case_id,
            CaseRecord.session_id == session_id,
            CaseRecord.expires_at > now,
        )
    )


def list_cases(session: Session, session_id: str) -> list[CaseRecord]:
    now = datetime.now(UTC)
    return list(
        session.scalars(
            select(CaseRecord)
            .where(
                CaseRecord.session_id == session_id,
                CaseRecord.expires_at > now,
            )
            .order_by(CaseRecord.updated_at.desc())
        )
    )


def count_active_cases(session: Session, session_id: str) -> int:
    now = datetime.now(UTC)
    return int(
        session.scalar(
            select(func.count())
            .select_from(CaseRecord)
            .where(
                CaseRecord.session_id == session_id,
                CaseRecord.archived.is_(False),
                CaseRecord.expires_at > now,
            )
        )
        or 0
    )


def audit(
    session: Session,
    record: CaseRecord,
    action: str,
    details: dict[str, Any] | None = None,
) -> None:
    now = datetime.now(UTC)
    record.updated_at = now
    session.add(
        AuditRecord(
            id=str(uuid4()),
            case_id=record.id,
            session_id=record.session_id,
            action=action,
            version=record.version,
            details_json=details or {},
            created_at=now,
        )
    )


def snapshot_case(session: Session, record: CaseRecord) -> CaseVersionRecord:
    snapshot = CaseVersionRecord(
        id=str(uuid4()),
        case_id=record.id,
        case_version=record.version,
        payload_json={
            "title": record.title,
            "status": record.status,
            "input": record.input_json,
            "analysis": record.analysis_json,
        },
        created_at=datetime.now(UTC),
    )
    session.add(snapshot)
    return snapshot


def update_version_analysis(session: Session, record: CaseRecord) -> None:
    snapshot = session.scalar(
        select(CaseVersionRecord)
        .where(
            CaseVersionRecord.case_id == record.id,
            CaseVersionRecord.case_version == record.version,
        )
        .order_by(CaseVersionRecord.created_at.desc())
    )
    if snapshot is None:
        snapshot_case(session, record)
        return
    snapshot.payload_json = {
        **snapshot.payload_json,
        "status": record.status,
        "analysis": record.analysis_json,
    }


def list_case_versions(session: Session, case_id: str) -> list[CaseVersionRecord]:
    return list(
        session.scalars(
            select(CaseVersionRecord)
            .where(CaseVersionRecord.case_id == case_id)
            .order_by(CaseVersionRecord.case_version.desc())
        )
    )


def get_case_version(
    session: Session, case_id: str, version: int
) -> CaseVersionRecord | None:
    return session.scalar(
        select(CaseVersionRecord).where(
            CaseVersionRecord.case_id == case_id,
            CaseVersionRecord.case_version == version,
        )
    )


def list_audit_records(session: Session, case_id: str) -> list[AuditRecord]:
    return list(
        session.scalars(
            select(AuditRecord)
            .where(AuditRecord.case_id == case_id)
            .order_by(AuditRecord.created_at.desc())
        )
    )
