"""add password hash column and optional admin seed

Revision ID: 0002
Revises: 0001
Create Date: 2025-02-20
"""
import os

from alembic import op
import sqlalchemy as sa
from passlib.context import CryptContext

# revision identifiers, used by Alembic.
revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


ADMIN_ROLES = {"PI", "PROJECT_MANAGER", "ALLOCATOR", "APPROVER"}


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_columns = {col["name"] for col in inspector.get_columns("users")}
    added_column = False

    if "password_hash" not in existing_columns:
        op.add_column(
            "users",
            sa.Column("password_hash", sa.String(), nullable=False, server_default=""),
        )
        added_column = True

    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")
    admin_name = os.getenv("ADMIN_NAME", "Admin User")
    admin_affiliation = os.getenv("ADMIN_AFFILIATION")
    admin_role = os.getenv("ADMIN_ROLE", "APPROVER")

    if admin_email and admin_password:
        role = admin_role if admin_role in ADMIN_ROLES else "APPROVER"
        password_hash = pwd_context.hash(admin_password)
        connection.execute(
            sa.text(
                """
                INSERT INTO users (name, email, affiliation, role, password_hash)
                VALUES (:name, :email, :affiliation, :role, :password_hash)
                ON CONFLICT(email) DO NOTHING
                """
            ),
            {
                "name": admin_name,
                "email": admin_email,
                "affiliation": admin_affiliation,
                "role": role,
                "password_hash": password_hash,
            },
        )

    if added_column:
        # SQLite does not support dropping a column default via ALTER TABLE,
        # so we only clear the default on databases that allow it. The column
        # remains NOT NULL and application code always supplies a hash, so the
        # empty-string default is only used while backfilling existing rows.
        if connection.dialect.name != "sqlite":
            op.alter_column("users", "password_hash", server_default=None)


def downgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_columns = {col["name"] for col in inspector.get_columns("users")}

    if "password_hash" in existing_columns:
        op.drop_column("users", "password_hash")
