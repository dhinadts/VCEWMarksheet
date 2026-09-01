"""add computerized marksheet artifacts

Revision ID: 7d9cbb891522
Revises: 871009b0e5c1
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "7d9cbb891522"
down_revision: Union[str, None] = "871009b0e5c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("marksheet_uploads", sa.Column("computerized_storage_key", sa.String(length=500), nullable=True))
    op.add_column("marksheet_uploads", sa.Column("approved_total", sa.Numeric(precision=8, scale=2), nullable=True))
    op.add_column("marksheet_uploads", sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True))
    op.create_unique_constraint("uq_marksheet_uploads_computerized_storage_key", "marksheet_uploads", ["computerized_storage_key"])


def downgrade() -> None:
    op.drop_constraint("uq_marksheet_uploads_computerized_storage_key", "marksheet_uploads", type_="unique")
    op.drop_column("marksheet_uploads", "approved_at")
    op.drop_column("marksheet_uploads", "approved_total")
    op.drop_column("marksheet_uploads", "computerized_storage_key")
