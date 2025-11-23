"""remove affiliation column from users table

Revision ID: 0007
Revises: 0006
Create Date: 2025-11-23
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    user_columns = {column["name"] for column in inspector.get_columns("users")}

    # Check if affiliation column exists
    if "affiliation" in user_columns:
        # SQLite doesn't support DROP COLUMN, so recreate table without affiliation
        if bind.dialect.name == "sqlite":
            # Create new table without affiliation column
            op.execute(
                """
                CREATE TABLE users_new (
                    id INTEGER PRIMARY KEY,
                    account_name VARCHAR NOT NULL UNIQUE,
                    first_name VARCHAR NOT NULL,
                    middle_name VARCHAR,
                    last_name VARCHAR NOT NULL,
                    name VARCHAR NOT NULL,
                    email VARCHAR NOT NULL UNIQUE,
                    department_id INTEGER,
                    role_id INTEGER NOT NULL,
                    password_hash VARCHAR NOT NULL,
                    FOREIGN KEY(department_id) REFERENCES departments(id),
                    FOREIGN KEY(role_id) REFERENCES roles(id)
                )
                """
            )

            # Copy data (excluding affiliation column)
            op.execute(
                """
                INSERT INTO users_new 
                    (id, account_name, first_name, middle_name, last_name, name, 
                     email, department_id, role_id, password_hash)
                SELECT 
                    id, account_name, first_name, middle_name, last_name, name,
                    email, department_id, role_id, password_hash
                FROM users
                """
            )

            # Drop old table and rename new one
            op.execute("DROP TABLE users")
            op.execute("ALTER TABLE users_new RENAME TO users")

            # Recreate indexes
            op.create_index("ix_users_account_name", "users", ["account_name"])
            op.create_index("ix_users_email", "users", ["email"])
            op.create_index("ix_users_role_id", "users", ["role_id"])
        else:
            # For other databases, simply drop the column
            op.drop_column("users", "affiliation")


def downgrade() -> None:
    # Add affiliation column back
    op.add_column(
        "users",
        sa.Column("affiliation", sa.String(), nullable=True)
    )
