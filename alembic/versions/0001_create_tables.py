"""create tables

Revision ID: 0001
Revises: 
Create Date: 2024-03-17
"""

from alembic import op
import sqlalchemy as sa

import app.models as models

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("affiliation", sa.String(), nullable=True),
        sa.Column("role", sa.Enum(models.UserRole), nullable=False),
    )
    op.create_table(
        "research_projects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("pi_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("manager_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
    )
    op.create_table(
        "beamtime_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("research_projects.id"), nullable=False),
        sa.Column("requested_date", sa.Date(), nullable=False),
        sa.Column("duration_hours", sa.Integer(), nullable=False),
        sa.Column("justification", sa.Text(), nullable=True),
        sa.Column("status", sa.Enum(models.RequestStatus), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "allocations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("request_id", sa.Integer(), sa.ForeignKey("beamtime_requests.id"), nullable=False),
        sa.Column("beamline", sa.String(), nullable=False),
        sa.Column("slot_date", sa.Date(), nullable=False),
        sa.Column("slot_time", sa.String(), nullable=False),
        sa.Column("duration_hours", sa.Integer(), nullable=False),
        sa.Column("status", sa.Enum(models.AllocationStatus), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "approvals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("allocation_id", sa.Integer(), sa.ForeignKey("allocations.id"), nullable=False),
        sa.Column("approver_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("approved", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("approvals")
    op.drop_table("allocations")
    op.drop_table("beamtime_requests")
    op.drop_table("research_projects")
    op.drop_table("users")
