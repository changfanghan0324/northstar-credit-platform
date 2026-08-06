"""Enforce one immutable snapshot per case version.

Revision ID: 0003
"""

from collections.abc import Sequence

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_case_versions_number",
        "case_versions",
        ["case_id", "case_version"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_case_versions_number",
        "case_versions",
        type_="unique",
    )
