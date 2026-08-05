"""HTTP contract for Northstar's calculated case workflow."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from typing import Annotated, Any

from fastapi import Depends, FastAPI, Header, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from northstar_credit_app import AnalysisResult, CaseInput, analyze_case
from northstar_credit_app.demo import list_demo_cases, load_demo_case
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .database import (
    CaseRecord,
    create_case,
    get_case,
    initialize_database,
    session_scope,
)
from .pdf import render_memo_pdf


class CaseEnvelope(BaseModel):
    id: str
    input: CaseInput
    analysis: AnalysisResult | None


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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["Content-Type", "X-Northstar-Session"],
)


def database() -> Iterator[Session]:
    yield from session_scope()


def session_id(
    x_northstar_session: Annotated[str | None, Header()] = None,
) -> str:
    return (x_northstar_session or "public-demo")[:80]


Database = Annotated[Session, Depends(database)]
SessionId = Annotated[str, Depends(session_id)]


def _analysis(record: CaseRecord) -> AnalysisResult:
    if record.analysis_json is None:
        raise HTTPException(409, "Case has not been analyzed")
    return AnalysisResult.model_validate(record.analysis_json)


def _envelope(record: CaseRecord) -> CaseEnvelope:
    return CaseEnvelope(
        id=record.id,
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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "northstar-credit-api"}


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


@app.post("/demo-cases/{slug}/open", response_model=CaseEnvelope)
def open_demo(slug: str, db: Database, owner: SessionId) -> CaseEnvelope:
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
    )
    return _envelope(record)


@app.post("/cases", response_model=CaseEnvelope)
def new_case(case: CaseInput, db: Database, owner: SessionId) -> CaseEnvelope:
    record = create_case(
        db,
        session_id=owner,
        slug=case.slug,
        input_json=case.model_dump(mode="json"),
        analysis_json=None,
    )
    return _envelope(record)


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
    db.commit()
    db.refresh(record)
    return _envelope(record)


@app.post("/cases/{case_id}/analyze", response_model=AnalysisResult)
def run_analysis(case_id: str, db: Database, owner: SessionId) -> AnalysisResult:
    record = _owned(db, case_id, owner)
    result = analyze_case(CaseInput.model_validate(record.input_json))
    record.analysis_json = result.model_dump(mode="json")
    db.commit()
    return result


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
def memo_pdf(case_id: str, db: Database, owner: SessionId) -> Response:
    result = _analysis(_owned(db, case_id, owner))
    return Response(
        content=render_memo_pdf(result),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{result.case.slug}-credit-memo.pdf"'
        },
    )
