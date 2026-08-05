"""Create anonymous credit-case storage.

Revision ID: 0001
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "credit_cases",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("session_id", sa.String(length=80), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("input_json", sa.JSON(), nullable=False),
        sa.Column("analysis_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_credit_cases_session_id", "credit_cases", ["session_id"])
    op.create_index("ix_credit_cases_slug", "credit_cases", ["slug"])


def downgrade() -> None:
    op.drop_index("ix_credit_cases_slug", table_name="credit_cases")
    op.drop_index("ix_credit_cases_session_id", table_name="credit_cases")
    op.drop_table("credit_cases")
