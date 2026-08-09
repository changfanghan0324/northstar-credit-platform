"""HTTP contract for Northstar's calculated case workflow."""

from __future__ import annotations

import hashlib
import os
import secrets
import time
from collections import defaultdict, deque
from collections.abc import AsyncIterator, Awaitable, Callable, Iterator
from contextlib import asynccontextmanager
from typing import Annotated, Any

from fastapi import Cookie, Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from northstar_credit_app import AnalysisResult, CaseInput, analyze_case
from northstar_credit_app.demo import list_demo_cases, load_demo_case
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import (
    AuditRecord,
    CaseRecord,
    CaseVersionRecord,
    audit,
    count_active_cases,
    create_case,
    get_case,
    get_case_version,
    initialize_database,
    list_audit_records,
    list_case_versions,
    list_cases,
    session_scope,
    snapshot_case,
    update_version_analysis,
)
from .pdf import render_memo_pdf


class CaseEnvelope(BaseModel):
    id: str
    title: str
    status: str
    version: int
    archived: bool
    updated_at: str
    expires_at: str
    input: CaseInput
    analysis: AnalysisResult | None


class CaseSummary(BaseModel):
    id: str
    title: str
    slug: str
    borrower_name: str
    status: str
    version: int
    archived: bool
    updated_at: str
    decision: str | None
    grade: int | None


class AuditEntry(BaseModel):
    id: str
    action: str
    version: int
    details: dict[str, Any]
    created_at: str


class CaseVersionSummary(BaseModel):
    version: int
    status: str
    created_at: str
    analyzed: bool


REQUEST_LIMIT = 60
CASE_QUOTA = 10
PDF_LIMIT = 5
MAX_PAYLOAD_BYTES = 1_048_576
PRODUCT_MODE = "portfolio_demo"
_requests: dict[str, deque[float]] = defaultdict(deque)
_pdf_requests: dict[str, deque[float]] = defaultdict(deque)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    initialize_database()
    yield


app = FastAPI(
    title="Northstar Credit Platform API",
    version="1.0.0",
    description="Deterministic educational corporate-credit underwriting API.",
    lifespan=lifespan,
)
allowed_origins = [
    value.strip()
    for value in os.environ.get(
        "NORTHSTAR_ALLOWED_ORIGINS",
        "https://northstar-credit-platform.vercel.app,http://localhost:3000",
    ).split(",")
    if value.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Northstar-Session"],
    allow_credentials=True,
)


@app.middleware("http")
async def operational_controls(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    request_id = secrets.token_hex(8)
    request.state.request_id = request_id
    content_length = int(request.headers.get("content-length", "0") or 0)
    if content_length > MAX_PAYLOAD_BYTES:
        return JSONResponse(
            status_code=413,
            content={
                "code": "payload_too_large",
                "message": "Request body exceeds the 1 MiB anonymous-demo limit.",
                "field": None,
                "remediation": "Reduce the case payload and try again.",
                "request_id": request_id,
            },
        )
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(HTTPException)
async def structured_http_error(request: Request, error: HTTPException) -> JSONResponse:
    detail = error.detail
    if isinstance(detail, dict):
        payload = detail
    else:
        payload = {
            "code": "request_failed",
            "message": str(detail),
            "field": None,
            "remediation": "Review the request and try again.",
        }
    payload["request_id"] = getattr(request.state, "request_id", "unknown")
    return JSONResponse(status_code=error.status_code, content=payload)


@app.exception_handler(RequestValidationError)
async def structured_validation_error(
    request: Request, error: RequestValidationError
) -> JSONResponse:
    first = error.errors()[0] if error.errors() else {}
    location = first.get("loc", [])
    field = ".".join(str(item) for item in location if item != "body") or None
    return JSONResponse(
        status_code=422,
        content={
            "code": "validation_failed",
            "message": first.get("msg", "Request validation failed."),
            "field": field,
            "remediation": "Correct the identified field and submit again.",
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


def database() -> Iterator[Session]:
    yield from session_scope()


def session_id(
    response: Response,
    x_northstar_session: Annotated[str | None, Header()] = None,
    northstar_session: Annotated[str | None, Cookie()] = None,
) -> str:
    allow_test_header = (
        os.environ.get("NORTHSTAR_ALLOW_TEST_SESSION_HEADER") == "1"
        or "PYTEST_CURRENT_TEST" in os.environ
    )
    header_session = x_northstar_session if allow_test_header else None
    raw = (header_session or northstar_session or "").strip()
    if not raw:
        raw = secrets.token_urlsafe(32)
        response.set_cookie(
            "northstar_session",
            raw,
            httponly=True,
            secure=os.environ.get("VERCEL") == "1",
            samesite="lax",
            max_age=7 * 24 * 60 * 60,
        )
    owner = hashlib.sha256(raw[:200].encode()).hexdigest()
    now = time.time()
    bucket = _requests[owner]
    while bucket and bucket[0] < now - 60:
        bucket.popleft()
    if len(bucket) >= REQUEST_LIMIT:
        raise HTTPException(
            429,
            {
                "code": "rate_limit_exceeded",
                "message": "Anonymous request limit reached.",
                "field": None,
                "remediation": "Wait one minute before trying again.",
            },
        )
    bucket.append(now)
    return owner


Database = Annotated[Session, Depends(database)]
SessionId = Annotated[str, Depends(session_id)]


def _analysis(record: CaseRecord) -> AnalysisResult:
    if record.analysis_json is None:
        raise HTTPException(409, "Case has not been analyzed")
    return AnalysisResult.model_validate(record.analysis_json)


def _envelope(record: CaseRecord) -> CaseEnvelope:
    return CaseEnvelope(
        id=record.id,
        title=record.title,
        status=record.status,
        version=record.version,
        archived=record.archived,
        updated_at=record.updated_at.isoformat(),
        expires_at=record.expires_at.isoformat(),
        input=CaseInput.model_validate(record.input_json),
        analysis=None
        if record.analysis_json is None
        else AnalysisResult.model_validate(record.analysis_json),
    )


def _owned(db: Session, case_id: str, owner: str) -> CaseRecord:
    record = get_case(db, case_id, owner)
    if record is None:
        raise HTTPException(404, "Case not found for this session")
    return record


def _quota(db: Session, owner: str) -> None:
    if count_active_cases(db, owner) >= CASE_QUOTA:
        raise HTTPException(
            409,
            {
                "code": "case_quota_reached",
                "message": "This anonymous session already has ten active cases.",
                "field": None,
                "remediation": "Archive or delete a case before creating another.",
            },
        )


def _validation_payload(
    case: CaseInput, *, case_version: int | None = None
) -> dict[str, Any]:
    result = analyze_case(case)
    missing = [
        component.key
        for component in result.scorecard.components
        if component.status == "blocked"
    ]
    policy_warnings = [
        f"{check.label}: {check.status}"
        for check in result.policy_checks
        if check.status not in {"pass", "not_applicable"}
    ]
    return {
        "valid": not missing,
        "case_version": case_version,
        "missing": missing,
        "warnings": [
            "Synthetic demonstration — not a real data-quality assessment",
            "Do not enter confidential information.",
            *policy_warnings,
        ],
        "currency": case.request.amount.currency,
        "estimated_confidence": result.scorecard.confidence_score,
        "provenance": result.provenance.model_dump(mode="json"),
        "completion": result.completion.model_dump(mode="json"),
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "northstar-credit-api"}


@app.get("/runtime")
def runtime() -> dict[str, Any]:
    durable = bool(os.environ.get("DATABASE_URL"))
    return {
        "persistence": "durable_postgresql" if durable else "temporary_session",
        "product_mode": PRODUCT_MODE,
        "durable": durable,
        "retention_days": 7,
        "case_quota": CASE_QUOTA,
        "requests_per_minute": REQUEST_LIMIT,
        "pdfs_per_hour": PDF_LIMIT,
        "maximum_payload_bytes": MAX_PAYLOAD_BYTES,
        "rate_limit_scope": "best_effort_instance",
        "notice": (
            "Anonymous synthetic cases expire after seven days."
            if durable
            else "Temporary portfolio-demo storage: cases expire within seven days and may disappear earlier after a service restart."
        ),
    }


@app.get("/demo-cases")
def demo_cases() -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for case in list_demo_cases():
        result = analyze_case(case)
        output.append(
            {
                "slug": case.slug,
                "borrower": case.borrower.model_dump(mode="json"),
                "request": case.request.model_dump(mode="json"),
                "decision": result.decision.model_dump(mode="json"),
                "grade": result.scorecard.grade,
                "recommended": result.capacity.recommended.model_dump(mode="json"),
            }
        )
    return output


@app.get("/demo-cases/{slug}/template", response_model=CaseInput)
def demo_template(slug: str) -> CaseInput:
    try:
        return load_demo_case(slug)
    except KeyError as error:
        raise HTTPException(404, "Demo case not found") from error


@app.post("/demo-cases/{slug}/open", response_model=CaseEnvelope)
def open_demo(slug: str, db: Database, owner: SessionId) -> CaseEnvelope:
    _quota(db, owner)
    try:
        case = load_demo_case(slug)
    except KeyError as error:
        raise HTTPException(404, "Demo case not found") from error
    result = analyze_case(case)
    record = create_case(
        db,
        session_id=owner,
        slug=case.slug,
        input_json=case.model_dump(mode="json"),
        analysis_json=result.model_dump(mode="json"),
        title=case.borrower.legal_name,
    )
    return _envelope(record)


@app.post("/cases", response_model=CaseEnvelope)
def new_case(case: CaseInput, db: Database, owner: SessionId) -> CaseEnvelope:
    _quota(db, owner)
    record = create_case(
        db,
        session_id=owner,
        slug=case.slug,
        input_json=case.model_dump(mode="json"),
        analysis_json=None,
        title=case.borrower.legal_name,
    )
    return _envelope(record)


@app.post("/cases/validate-input")
def validate_input(case: CaseInput, _: SessionId) -> dict[str, Any]:
    return _validation_payload(case)


@app.get("/cases", response_model=list[CaseSummary])
def cases(db: Database, owner: SessionId) -> list[CaseSummary]:
    output: list[CaseSummary] = []
    for record in list_cases(db, owner):
        analysis = (
            None
            if record.analysis_json is None
            else AnalysisResult.model_validate(record.analysis_json)
        )
        input_case = CaseInput.model_validate(record.input_json)
        output.append(
            CaseSummary(
                id=record.id,
                title=record.title,
                slug=record.slug,
                borrower_name=input_case.borrower.legal_name,
                status=record.status,
                version=record.version,
                archived=record.archived,
                updated_at=record.updated_at.isoformat(),
                decision=None if analysis is None else analysis.decision.outcome,
                grade=None if analysis is None else analysis.scorecard.grade,
            )
        )
    return output


@app.get("/cases/{case_id}", response_model=CaseEnvelope)
def read_case(case_id: str, db: Database, owner: SessionId) -> CaseEnvelope:
    return _envelope(_owned(db, case_id, owner))


@app.put("/cases/{case_id}", response_model=CaseEnvelope)
def update_case(
    case_id: str, case: CaseInput, db: Database, owner: SessionId
) -> CaseEnvelope:
    record = _owned(db, case_id, owner)
    record.input_json = case.model_dump(mode="json")
    record.analysis_json = None
    record.title = case.borrower.legal_name
    record.slug = case.slug
    record.version += 1
    record.status = "stale"
    snapshot_case(db, record)
    audit(db, record, "updated", {"analysis_stale": True})
    db.commit()
    db.refresh(record)
    return _envelope(record)


@app.post("/cases/{case_id}/validate")
def validate_case(case_id: str, db: Database, owner: SessionId) -> dict[str, Any]:
    record = _owned(db, case_id, owner)
    case = CaseInput.model_validate(record.input_json)
    return _validation_payload(case, case_version=record.version)


@app.post("/cases/{case_id}/analyze", response_model=AnalysisResult)
def run_analysis(case_id: str, db: Database, owner: SessionId) -> AnalysisResult:
    record = _owned(db, case_id, owner)
    result = analyze_case(CaseInput.model_validate(record.input_json))
    record.analysis_json = result.model_dump(mode="json")
    record.status = "blocked" if result.analysis_status == "blocked" else "analyzed"
    update_version_analysis(db, record)
    audit(db, record, "analyzed", {"input_hash": result.input_hash})
    db.commit()
    return result


@app.post("/cases/{case_id}/duplicate", response_model=CaseEnvelope)
def duplicate_case(case_id: str, db: Database, owner: SessionId) -> CaseEnvelope:
    _quota(db, owner)
    source = _owned(db, case_id, owner)
    case = CaseInput.model_validate(source.input_json)
    copied = case.model_copy(
        update={"slug": f"{case.slug}-copy-{secrets.token_hex(3)}"}
    )
    record = create_case(
        db,
        session_id=owner,
        slug=copied.slug,
        title=f"{source.title} (Copy)",
        input_json=copied.model_dump(mode="json"),
        analysis_json=None,
    )
    audit(db, record, "duplicated", {"source_case_id": source.id})
    db.commit()
    return _envelope(record)


@app.post("/cases/{case_id}/archive", response_model=CaseEnvelope)
def archive_case(case_id: str, db: Database, owner: SessionId) -> CaseEnvelope:
    record = _owned(db, case_id, owner)
    record.archived = not record.archived
    record.status = (
        "archived"
        if record.archived
        else ("analyzed" if record.analysis_json else "draft")
    )
    audit(db, record, "archived" if record.archived else "restored")
    db.commit()
    db.refresh(record)
    return _envelope(record)


@app.get("/cases/{case_id}/versions", response_model=list[CaseVersionSummary])
def case_versions(
    case_id: str, db: Database, owner: SessionId
) -> list[CaseVersionSummary]:
    _owned(db, case_id, owner)
    return [
        CaseVersionSummary(
            version=item.case_version,
            status=str(item.payload_json.get("status", "draft")),
            created_at=item.created_at.isoformat(),
            analyzed=item.payload_json.get("analysis") is not None,
        )
        for item in list_case_versions(db, case_id)
    ]


@app.post("/cases/{case_id}/versions/{version}/restore", response_model=CaseEnvelope)
def restore_case_version(
    case_id: str, version: int, db: Database, owner: SessionId
) -> CaseEnvelope:
    record = _owned(db, case_id, owner)
    source = get_case_version(db, case_id, version)
    if source is None:
        raise HTTPException(404, "Case version not found")
    restored_input = CaseInput.model_validate(source.payload_json["input"])
    record.input_json = restored_input.model_dump(mode="json")
    record.analysis_json = None
    record.title = restored_input.borrower.legal_name
    record.slug = restored_input.slug
    record.version += 1
    record.status = "stale"
    snapshot_case(db, record)
    audit(db, record, "version_restored", {"source_version": version})
    db.commit()
    db.refresh(record)
    return _envelope(record)


@app.get("/cases/{case_id}/audit", response_model=list[AuditEntry])
def case_audit(case_id: str, db: Database, owner: SessionId) -> list[AuditEntry]:
    _owned(db, case_id, owner)
    return [
        AuditEntry(
            id=item.id,
            action=item.action,
            version=item.version,
            details=item.details_json,
            created_at=item.created_at.isoformat(),
        )
        for item in list_audit_records(db, case_id)
    ]


@app.delete("/cases/{case_id}", status_code=204)
def delete_case(case_id: str, db: Database, owner: SessionId) -> Response:
    record = _owned(db, case_id, owner)
    for item in db.scalars(select(AuditRecord).where(AuditRecord.case_id == record.id)):
        db.delete(item)
    for version_item in db.scalars(
        select(CaseVersionRecord).where(CaseVersionRecord.case_id == record.id)
    ):
        db.delete(version_item)
    db.delete(record)
    db.commit()
    return Response(status_code=204)


@app.get("/cases/{case_id}/analysis", response_model=AnalysisResult)
def analysis(case_id: str, db: Database, owner: SessionId) -> AnalysisResult:
    return _analysis(_owned(db, case_id, owner))


@app.get("/cases/{case_id}/financials")
def financials(case_id: str, db: Database, owner: SessionId) -> dict[str, Any]:
    result = _analysis(_owned(db, case_id, owner))
    return {"metrics": result.metrics, "scorecard": result.scorecard}


@app.get("/cases/{case_id}/risk")
def risk(case_id: str, db: Database, owner: SessionId) -> dict[str, Any]:
    result = _analysis(_owned(db, case_id, owner))
    return {"scorecard": result.scorecard, "business_risk": result.case.business_risk}


@app.get("/cases/{case_id}/stress")
def stress(case_id: str, db: Database, owner: SessionId) -> dict[str, Any]:
    result = _analysis(_owned(db, case_id, owner))
    return {
        "scenarios": result.scenarios,
        "covenants": result.covenants,
        "reverse_stress": result.reverse_stress,
    }


@app.get("/cases/{case_id}/decision")
def decision(case_id: str, db: Database, owner: SessionId) -> dict[str, Any]:
    result = _analysis(_owned(db, case_id, owner))
    return {"decision": result.decision, "capacity": result.capacity}


@app.get("/cases/{case_id}/memo")
def memo(case_id: str, db: Database, owner: SessionId) -> dict[str, Any]:
    result = _analysis(_owned(db, case_id, owner))
    return {"sections": result.memo_sections, "input_hash": result.input_hash}


@app.get("/cases/{case_id}/memo.pdf")
def memo_pdf(
    case_id: str,
    db: Database,
    owner: SessionId,
    locale: str = "en",
    detail: str = "executive",
) -> Response:
    if locale not in {"en", "zh-TW"}:
        raise HTTPException(422, "PDF locale must be en or zh-TW")
    if detail not in {"executive", "detailed"}:
        raise HTTPException(422, "PDF detail must be executive or detailed")
    now = time.time()
    bucket = _pdf_requests[owner]
    while bucket and bucket[0] < now - 3600:
        bucket.popleft()
    if len(bucket) >= PDF_LIMIT:
        raise HTTPException(429, "Anonymous PDF limit reached; try again later")
    bucket.append(now)
    result = _analysis(_owned(db, case_id, owner))
    return Response(
        content=render_memo_pdf(
            result, locale=locale, detailed=detail.lower() == "detailed"
        ),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{result.case.slug}-credit-memo.pdf"'
        },
    )
