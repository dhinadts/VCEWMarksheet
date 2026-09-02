"""add admin submission workflow

Revision ID: 4f26a77dba31
Revises: 7d9cbb891522
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "4f26a77dba31"
down_revision: Union[str, None] = "7d9cbb891522"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column("marksheet_uploads", sa.Column("submission_status", sa.String(length=30), nullable=False, server_default="DRAFT"))
    op.add_column("marksheet_uploads", sa.Column("submitted_to_admin_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("marksheet_uploads", sa.Column("admin_reviewed_by", sa.Uuid(), nullable=True))
    op.add_column("marksheet_uploads", sa.Column("admin_reviewed_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key("fk_marksheet_admin_reviewed_by", "marksheet_uploads", "users", ["admin_reviewed_by"], ["id"])
    op.create_index("ix_marksheet_uploads_submission_status", "marksheet_uploads", ["submission_status"])

def downgrade() -> None:
    op.drop_index("ix_marksheet_uploads_submission_status", table_name="marksheet_uploads")
    op.drop_constraint("fk_marksheet_admin_reviewed_by", "marksheet_uploads", type_="foreignkey")
    op.drop_column("marksheet_uploads", "admin_reviewed_at")
    op.drop_column("marksheet_uploads", "admin_reviewed_by")
    op.drop_column("marksheet_uploads", "submitted_to_admin_at")
    op.drop_column("marksheet_uploads", "submission_status")
