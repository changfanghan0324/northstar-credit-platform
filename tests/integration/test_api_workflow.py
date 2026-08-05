from __future__ import annotations

from fastapi.testclient import TestClient
from northstar_api.main import app


def test_demo_case_full_api_workflow_and_session_isolation() -> None:
    with TestClient(app) as client:
        demos = client.get("/demo-cases")
        assert demos.status_code == 200
        assert len(demos.json()) == 3

        headers = {"X-Northstar-Session": "integration-owner"}
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
            headers={"X-Northstar-Session": "different-owner"},
        )
        assert hidden.status_code == 404


def test_create_save_then_analyze_has_no_partial_output() -> None:
    with TestClient(app) as client:
        owner = {"X-Northstar-Session": "integration-create"}
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
