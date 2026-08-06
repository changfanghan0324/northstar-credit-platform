from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from northstar_api.database import CaseRecord, engine
from northstar_api.main import app
from sqlalchemy import select
from sqlalchemy.orm import Session


def test_demo_case_full_api_workflow_and_session_isolation() -> None:
    with TestClient(app) as client:
        demos = client.get("/demo-cases")
        assert demos.status_code == 200
        assert len(demos.json()) == 3

        headers = {"X-Northstar-Session": f"integration-owner-{uuid4()}"}
        opened = client.post("/demo-cases/stable-manufacturer/open", headers=headers)
        assert opened.status_code == 200
        case_id = opened.json()["id"]
        assert opened.json()["analysis"]["decision"]["outcome"] == (
            "Approve with conditions"
        )

        for surface in (
            "analysis",
            "financials",
            "risk",
            "stress",
            "decision",
            "memo",
        ):
            response = client.get(f"/cases/{case_id}/{surface}", headers=headers)
            assert response.status_code == 200

        pdf = client.get(f"/cases/{case_id}/memo.pdf", headers=headers)
        assert pdf.status_code == 200
        assert pdf.headers["content-type"] == "application/pdf"
        assert pdf.content.startswith(b"%PDF-1.4")

        hidden = client.get(
            f"/cases/{case_id}",
            headers={"X-Northstar-Session": f"different-owner-{uuid4()}"},
        )
        assert hidden.status_code == 404


def test_create_save_then_analyze_has_no_partial_output() -> None:
    with TestClient(app) as client:
        owner = {"X-Northstar-Session": f"integration-create-{uuid4()}"}
        template = client.post(
            "/demo-cases/software-services/open", headers=owner
        ).json()["input"]
        template["slug"] = "integration-custom"
        template["borrower"]["legal_name"] = "Integration Synthetic, Inc."

        created = client.post("/cases", headers=owner, json=template)
        assert created.status_code == 200
        assert created.json()["analysis"] is None

        case_id = created.json()["id"]
        analyzed = client.post(f"/cases/{case_id}/analyze", headers=owner)
        assert analyzed.status_code == 200
        assert analyzed.json()["case"]["borrower"]["legal_name"] == (
            "Integration Synthetic, Inc."
        )
        assert analyzed.json()["capacity"]["recommended"]["amount_minor"] == 900_000_000


def test_case_lifecycle_list_duplicate_archive_update_rerun_delete() -> None:
    with TestClient(app) as client:
        owner = {"X-Northstar-Session": f"integration-lifecycle-{uuid4()}"}
        template = client.get(
            "/demo-cases/stable-manufacturer/template", headers=owner
        ).json()
        created = client.post("/cases", headers=owner, json=template)
        assert created.status_code == 200
        case_id = created.json()["id"]

        assert client.post(f"/cases/{case_id}/validate", headers=owner).json()["valid"]
        assert (
            client.post(f"/cases/{case_id}/analyze", headers=owner).status_code == 200
        )

        listed = client.get("/cases", headers=owner).json()
        assert [item["id"] for item in listed] == [case_id]
        assert listed[0]["status"] == "analyzed"

        duplicated = client.post(f"/cases/{case_id}/duplicate", headers=owner)
        assert duplicated.status_code == 200
        duplicate_id = duplicated.json()["id"]
        assert duplicate_id != case_id
        assert duplicated.json()["status"] == "draft"
        assert duplicated.json()["analysis"] is None

        archived = client.post(f"/cases/{duplicate_id}/archive", headers=owner)
        assert archived.json()["archived"] is True

        template["borrower"]["legal_name"] = "Edited Synthetic Borrower"
        updated = client.put(f"/cases/{case_id}", headers=owner, json=template)
        assert updated.json()["status"] == "stale"
        assert updated.json()["analysis"] is None
        assert updated.json()["version"] == 2
        rerun = client.post(f"/cases/{case_id}/analyze", headers=owner)
        assert rerun.json()["case"]["borrower"]["legal_name"] == (
            "Edited Synthetic Borrower"
        )

        assert client.delete(f"/cases/{duplicate_id}", headers=owner).status_code == 204
        assert client.get(f"/cases/{duplicate_id}", headers=owner).status_code == 404


def test_server_issues_anonymous_cookie_and_runtime_is_truthful() -> None:
    with TestClient(app) as client:
        runtime = client.get("/runtime")
        assert runtime.status_code == 200
        assert runtime.json()["persistence"] in {
            "durable_postgresql",
            "temporary_session",
        }
        cases = client.get("/cases")
        assert "northstar_session" in cases.headers.get("set-cookie", "")


def test_localized_detailed_pdf_uses_currency_not_minor_units() -> None:
    with TestClient(app) as client:
        owner = {"X-Northstar-Session": f"integration-pdf-zh-{uuid4()}"}
        opened = client.post("/demo-cases/stable-manufacturer/open", headers=owner)
        case_id = opened.json()["id"]
        pdf = client.get(
            f"/cases/{case_id}/memo.pdf?locale=zh-TW&detail=detailed",
            headers=owner,
        )
        assert pdf.status_code == 200
        assert pdf.content.startswith(b"%PDF-1.4")
        assert b"minor units" not in pdf.content
        assert b"/UniCNS-UCS2-H" in pdf.content
        page_count = re.search(rb"/Count (\d+)", pdf.content)
        assert page_count is not None
        assert int(page_count.group(1)) > 1


def test_expired_case_is_not_read_or_listed() -> None:
    with TestClient(app) as client:
        owner = {"X-Northstar-Session": f"integration-expiry-{uuid4()}"}
        created = client.post(
            "/demo-cases/stable-manufacturer/open", headers=owner
        ).json()
        with Session(engine) as db:
            record = db.scalar(select(CaseRecord).where(CaseRecord.id == created["id"]))
            assert record is not None
            record.expires_at = datetime.now(UTC) - timedelta(seconds=1)
            db.commit()

        assert client.get(f"/cases/{created['id']}", headers=owner).status_code == 404
        assert client.get("/cases", headers=owner).json() == []


def test_english_pdf_preserves_mandated_disclaimer_punctuation() -> None:
    with TestClient(app) as client:
        owner = {"X-Northstar-Session": f"integration-pdf-en-{uuid4()}"}
        opened = client.post("/demo-cases/stable-manufacturer/open", headers=owner)
        pdf = client.get(
            f"/cases/{opened.json()['id']}/memo.pdf?locale=en",
            headers=owner,
        )

        assert (
            b"Synthetic demonstration \x97 not a real data-quality assessment"
            in pdf.content
        )
