"""Add versioned anonymous workflow, audit, and normalized analysis entities.

Revision ID: 0002
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _owned_table(name: str) -> None:
    op.create_table(
        name,
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "case_id",
            sa.String(length=36),
            sa.ForeignKey("credit_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("case_version", sa.Integer(), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(f"ix_{name}_case_version", name, ["case_id", "case_version"])


def upgrade() -> None:
    op.add_column("credit_cases", sa.Column("title", sa.String(160), nullable=True))
    op.add_column("credit_cases", sa.Column("status", sa.String(24), nullable=True))
    op.add_column("credit_cases", sa.Column("version", sa.Integer(), nullable=True))
    op.add_column("credit_cases", sa.Column("archived", sa.Boolean(), nullable=True))
    op.add_column(
        "credit_cases",
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_credit_cases_status", "credit_cases", ["status"])
    op.create_index("ix_credit_cases_archived", "credit_cases", ["archived"])
    op.create_index("ix_credit_cases_expires_at", "credit_cases", ["expires_at"])

    op.create_table(
        "case_audit_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "case_id",
            sa.String(36),
            sa.ForeignKey("credit_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("session_id", sa.String(80), nullable=False),
        sa.Column("action", sa.String(40), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("details_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_case_audit_logs_case_id", "case_audit_logs", ["case_id"])
    op.create_index("ix_case_audit_logs_session_id", "case_audit_logs", ["session_id"])

    for table in (
        "case_versions",
        "borrowers",
        "loan_requests",
        "financial_periods",
        "normalized_financials",
        "adjustments",
        "debt_instruments",
        "business_risk_assessments",
        "scenarios",
        "scenario_assumptions",
        "analyses",
        "policy_checks",
        "capacity_constraints",
        "covenant_recommendations",
        "covenant_tests",
        "decisions",
        "memo_versions",
    ):
        _owned_table(table)


def downgrade() -> None:
    for table in reversed(
        (
            "case_versions",
            "borrowers",
            "loan_requests",
            "financial_periods",
            "normalized_financials",
            "adjustments",
            "debt_instruments",
            "business_risk_assessments",
            "scenarios",
            "scenario_assumptions",
            "analyses",
            "policy_checks",
            "capacity_constraints",
            "covenant_recommendations",
            "covenant_tests",
            "decisions",
            "memo_versions",
        )
    ):
        op.drop_index(f"ix_{table}_case_version", table_name=table)
        op.drop_table(table)
    op.drop_index("ix_case_audit_logs_session_id", table_name="case_audit_logs")
    op.drop_index("ix_case_audit_logs_case_id", table_name="case_audit_logs")
    op.drop_table("case_audit_logs")
    op.drop_index("ix_credit_cases_expires_at", table_name="credit_cases")
    op.drop_index("ix_credit_cases_archived", table_name="credit_cases")
    op.drop_index("ix_credit_cases_status", table_name="credit_cases")
    for column in ("expires_at", "archived", "version", "status", "title"):
        op.drop_column("credit_cases", column)
