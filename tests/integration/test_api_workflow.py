from __future__ import annotations

from datetime import UTC, datetime, timedelta
from io import BytesIO
from uuid import uuid4

from fastapi.testclient import TestClient
from northstar_api.database import CaseRecord, engine
from northstar_api.main import app
from pypdf import PdfReader
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
        restored = client.post(f"/cases/{duplicate_id}/archive", headers=owner)
        assert restored.json()["archived"] is False

        template["borrower"]["legal_name"] = "Edited Synthetic Borrower"
        updated = client.put(f"/cases/{case_id}", headers=owner, json=template)
        assert updated.json()["status"] == "stale"
        assert updated.json()["analysis"] is None
        assert updated.json()["version"] == 2
        rerun = client.post(f"/cases/{case_id}/analyze", headers=owner)
        assert rerun.json()["case"]["borrower"]["legal_name"] == (
            "Edited Synthetic Borrower"
        )

        versions = client.get(f"/cases/{case_id}/versions", headers=owner)
        assert [item["version"] for item in versions.json()] == [2, 1]
        history = client.get(f"/cases/{case_id}/audit", headers=owner)
        assert {item["action"] for item in history.json()} >= {
            "created",
            "updated",
            "analyzed",
        }

        version_restore = client.post(
            f"/cases/{case_id}/versions/1/restore", headers=owner
        )
        assert version_restore.status_code == 200
        assert version_restore.json()["version"] == 3
        assert version_restore.json()["status"] == "stale"
        assert version_restore.json()["analysis"] is None
        assert version_restore.json()["input"]["borrower"]["legal_name"] == (
            "Alder Creek Components, Inc."
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


def test_public_demo_catalog_does_not_race_anonymous_session_cookie() -> None:
    with TestClient(app) as client:
        catalog = client.get("/demo-cases")
        template = client.get("/demo-cases/stable-manufacturer/template")
        assert catalog.status_code == 200
        assert template.status_code == 200
        assert "northstar_session" not in catalog.headers.get("set-cookie", "")
        assert "northstar_session" not in template.headers.get("set-cookie", "")

        opened = client.post("/demo-cases/stable-manufacturer/open")
        assert opened.status_code == 200
        assert "northstar_session" in opened.headers.get("set-cookie", "")
        assert client.get(f"/cases/{opened.json()['id']}").status_code == 200


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
        assert b"NotoSansTC" in pdf.content
        assert b"/ToUnicode" in pdf.content
        reader = PdfReader(BytesIO(pdf.content))
        assert len(reader.pages) > 1
        assert reader.metadata is not None
        assert reader.metadata.title == "北極星授信備忘錄"
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        assert "統一授信機制" in text


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

        reader = PdfReader(BytesIO(pdf.content))
        text = "\n".join(page.extract_text() for page in reader.pages)
        assert "Synthetic demonstration data" in text
        assert "Educational and illustrative only" in text
        assert "Resolved mechanics: term_loan; fully_amortizing" in text


def test_blocked_debt_reconciliation_is_visible_in_analysis_and_pdf() -> None:
    with TestClient(app) as client:
        owner = {"X-Northstar-Session": f"integration-debt-blocked-{uuid4()}"}
        template = client.post(
            "/demo-cases/stable-manufacturer/open", headers=owner
        ).json()["input"]
        template["slug"] = "integration-debt-reconciliation-blocked"
        template["debt_instruments"] = [
            {
                "name": "Unreconciled instrument",
                "principal": {
                    "amount_minor": 1_000_000_000,
                    "currency": "USD",
                    "minor_unit_exponent": 2,
                },
                "annual_rate": "0.06",
                "rate_type": "fixed",
                "spread": "0",
                "rate_floor": "0",
                "scheduled_amortization": {
                    "amount_minor": 10_000_000,
                    "currency": "USD",
                    "minor_unit_exponent": 2,
                },
                "maturity_year": 5,
                "secured": False,
                "seniority": "Senior",
                "collateral": "None",
                "schedule_completeness": "complete",
            }
        ]
        created = client.post("/cases", headers=owner, json=template)
        assert created.status_code == 200
        analyzed = client.post(f"/cases/{created.json()['id']}/analyze", headers=owner)
        assert analyzed.status_code == 200
        analysis = analyzed.json()
        assert analysis["debt_reconciliation"]["status"] == "blocked"
        assert analysis["debt_reconciliation"]["selected_source"] == "blocked_mismatch"
        assert analysis["metrics"]["dscr"]["status"] == "blocked"
        pdf = client.get(
            f"/cases/{created.json()['id']}/memo.pdf?locale=en&detail=detailed",
            headers=owner,
        )
        assert pdf.status_code == 200
        text = "\n".join(
            page.extract_text() or "" for page in PdfReader(BytesIO(pdf.content)).pages
        )
        assert "Debt reconciliation: blocked" in text
        assert "blocked_mismatch" in text


def test_partial_debt_reconciliation_residual_is_visible_in_memo_and_pdf() -> None:
    with TestClient(app) as client:
        owner = {"X-Northstar-Session": f"integration-debt-partial-{uuid4()}"}
        template = client.post(
            "/demo-cases/stable-manufacturer/open", headers=owner
        ).json()["input"]
        template["slug"] = "integration-debt-reconciliation-partial"
        template["debt_instruments"] = [
            {
                "name": "Long-term partial schedule",
                "principal": {
                    "amount_minor": 6_000_000_000,
                    "currency": "USD",
                    "minor_unit_exponent": 2,
                },
                "annual_rate": "0.08",
                "rate_type": "floating",
                "spread": "0",
                "rate_floor": "0",
                "scheduled_amortization": {
                    "amount_minor": 900_000_000,
                    "currency": "USD",
                    "minor_unit_exponent": 2,
                },
                "maturity_year": 5,
                "secured": False,
                "seniority": "Senior",
                "collateral": "None",
                "schedule_completeness": "partial",
            }
        ]
        created = client.post("/cases", headers=owner, json=template)
        assert created.status_code == 200
        analyzed = client.post(f"/cases/{created.json()['id']}/analyze", headers=owner)
        assert analyzed.status_code == 200
        analysis = analyzed.json()
        assert analysis["debt_reconciliation"]["status"] == "reconciled"
        assert (
            analysis["debt_reconciliation"]["selected_source"]
            == "partial_schedule_with_residual"
        )
        assert analysis["debt_reconciliation"]["residual_maturity_status"] == "unknown"
        assert "Unscheduled residual debt" in " ".join(
            analysis["memo_sections"]["debt_maturity_schedule"]
        )
        pdf = client.get(
            f"/cases/{created.json()['id']}/memo.pdf?locale=en&detail=detailed",
            headers=owner,
        )
        assert pdf.status_code == 200
        text = "\n".join(
            page.extract_text() or "" for page in PdfReader(BytesIO(pdf.content)).pages
        )
        assert "Debt reconciliation: reconciled" in text
        assert "Unscheduled residual debt" in text
        assert "maturity status unknown" in text


def test_five_year_bullet_maturity_and_no_refinancing_are_visible_in_bilingual_pdf() -> (
    None
):
    with TestClient(app) as client:
        owner = {"X-Northstar-Session": f"integration-bullet-exit-{uuid4()}"}
        template = client.post(
            "/demo-cases/stable-manufacturer/open", headers=owner
        ).json()["input"]
        template["slug"] = "integration-five-year-bullet"
        template["request"].update(
            {
                "amount": {
                    "amount_minor": 2_500_000_000,
                    "currency": "USD",
                    "minor_unit_exponent": 2,
                },
                "amortization_type": "bullet",
                "amortization_years": None,
                "maturity_years": 5,
                "bullet_percentage": "1",
            }
        )
        created = client.post("/cases", headers=owner, json=template)
        assert created.status_code == 200
        case_id = created.json()["id"]
        analyzed = client.post(f"/cases/{case_id}/analyze", headers=owner)
        assert analyzed.status_code == 200
        analysis = analyzed.json()
        severe = next(
            item for item in analysis["scenarios"] if item["name"] == "severe"
        )
        assert severe["maturity_year"] == 5
        assert severe["balloon_amount"]["amount_minor"] == 2_500_000_000
        assert severe["maturity_test_status"] == "breach"
        assert severe["no_refinancing_status"] == "breach"
        for locale, expected_text in (("en", "Maturity year 5"), ("zh-TW", "到期年 5")):
            pdf = client.get(
                f"/cases/{case_id}/memo.pdf?locale={locale}&detail=detailed",
                headers=owner,
            )
            assert pdf.status_code == 200
            text = "\n".join(
                page.extract_text() or ""
                for page in PdfReader(BytesIO(pdf.content)).pages
            )
            assert expected_text in text


def test_revolver_abl_contract_is_visible_in_bilingual_pdf() -> None:
    with TestClient(app) as client:
        owner = {"X-Northstar-Session": f"integration-abl-{uuid4()}"}
        template = client.post(
            "/demo-cases/stable-manufacturer/open", headers=owner
        ).json()["input"]
        template["slug"] = "integration-revolver-abl"
        template["request"].update(
            {
                "amount": {
                    "amount_minor": 1_000_000_000,
                    "currency": "USD",
                    "minor_unit_exponent": 2,
                },
                "facility_type": "asset_based",
                "security_type": "asset_based",
                "amortization_type": "revolver",
                "initial_drawn_amount": {
                    "amount_minor": 200_000_000,
                    "currency": "USD",
                    "minor_unit_exponent": 2,
                },
                "commitment_fee_bps": 100,
            }
        )
        template["borrowing_base"] = {
            "accounts_receivable": {
                "gross_receivables": {
                    "amount_minor": 1_000_000_000,
                    "currency": "USD",
                    "minor_unit_exponent": 2,
                },
                "ineligible_receivables": {
                    "amount_minor": 100_000_000,
                    "currency": "USD",
                    "minor_unit_exponent": 2,
                },
                "past_due_receivables": {
                    "amount_minor": 50_000_000,
                    "currency": "USD",
                    "minor_unit_exponent": 2,
                },
                "cross_aged_receivables": {
                    "amount_minor": 0,
                    "currency": "USD",
                    "minor_unit_exponent": 2,
                },
                "foreign_receivables": {
                    "amount_minor": 0,
                    "currency": "USD",
                    "minor_unit_exponent": 2,
                },
                "concentration_reserve": {
                    "amount_minor": 0,
                    "currency": "USD",
                    "minor_unit_exponent": 2,
                },
                "dilution_reserve": {
                    "amount_minor": 0,
                    "currency": "USD",
                    "minor_unit_exponent": 2,
                },
                "advance_rate": "0.80",
            },
            "inventory": {
                "gross_inventory": {
                    "amount_minor": 0,
                    "currency": "USD",
                    "minor_unit_exponent": 2,
                },
                "ineligible_inventory": {
                    "amount_minor": 0,
                    "currency": "USD",
                    "minor_unit_exponent": 2,
                },
                "obsolete_inventory": {
                    "amount_minor": 0,
                    "currency": "USD",
                    "minor_unit_exponent": 2,
                },
                "advance_rate": "0.50",
                "inventory_cap": {
                    "amount_minor": 0,
                    "currency": "USD",
                    "minor_unit_exponent": 2,
                },
            },
            "other_collateral": {
                "equipment": {
                    "amount_minor": 0,
                    "currency": "USD",
                    "minor_unit_exponent": 2,
                },
                "real_estate": {
                    "amount_minor": 0,
                    "currency": "USD",
                    "minor_unit_exponent": 2,
                },
                "cash": {
                    "amount_minor": 0,
                    "currency": "USD",
                    "minor_unit_exponent": 2,
                },
                "other": {
                    "amount_minor": 0,
                    "currency": "USD",
                    "minor_unit_exponent": 2,
                },
            },
            "additional_reserves": {
                "amount_minor": 0,
                "currency": "USD",
                "minor_unit_exponent": 2,
            },
            "prior_liens": {
                "amount_minor": 0,
                "currency": "USD",
                "minor_unit_exponent": 2,
            },
        }
        created = client.post("/cases", headers=owner, json=template)
        assert created.status_code == 200
        case_id = created.json()["id"]
        analyzed = client.post(f"/cases/{case_id}/analyze", headers=owner)
        assert analyzed.status_code == 200
        view = analyzed.json()["revolver_abl"]
        assert view["availability"]["amount_minor"] == 480_000_000
        assert view["commitment_fee"]["amount_minor"] == 8_000_000
        for locale, expected_text in (
            ("en", "Revolver/ABL mechanics"),
            ("zh-TW", "循環／ABL 機制"),
        ):
            pdf = client.get(
                f"/cases/{case_id}/memo.pdf?locale={locale}&detail=detailed",
                headers=owner,
            )
            assert pdf.status_code == 200
            text = "\n".join(
                page.extract_text() or ""
                for page in PdfReader(BytesIO(pdf.content)).pages
            )
            assert expected_text in text
