"""add hierarchy documents

Revision ID: 001_add_hierarchy_documents
Revises:
Create Date: 2026-05-12
"""

from alembic import op
import sqlalchemy as sa


revision = "001_add_hierarchy_documents"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "hierarchy_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("doc_type", sa.String(length=30), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("bahagian", sa.String(length=120), nullable=True),
        sa.Column("cawangan", sa.String(length=120), nullable=True),
        sa.Column("meeting_date", sa.Date(), nullable=True),
        sa.Column("position", sa.String(length=200), nullable=False),
        sa.Column("candidate_name", sa.String(length=200), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=True),
    )


def downgrade():
    op.drop_table("hierarchy_documents")
