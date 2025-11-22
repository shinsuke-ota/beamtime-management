"""add institutions and departments tables and user department id

Revision ID: 0003
Revises: 0002
Create Date: 2025-02-25
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "institutions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.UniqueConstraint("name", name="uq_institution_name"),
    )

    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("institution_id", sa.Integer(), sa.ForeignKey("institutions.id"), nullable=False),
        sa.UniqueConstraint("institution_id", "name", name="uq_department_institution_name"),
    )

    op.add_column(
        "users",
        sa.Column(
            "department_id", sa.Integer(), sa.ForeignKey("departments.id"), nullable=True
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "department_id")
    op.drop_table("departments")
    op.drop_table("institutions")
