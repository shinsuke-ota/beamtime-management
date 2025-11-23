"""drop old role column from users table

Revision ID: 0006
Revises: 0005
Create Date: 2025-11-23
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    user_columns = {column["name"] for column in inspector.get_columns("users")}

    # Check if old role column still exists
    if "role" in user_columns:
        # SQLite doesn't support DROP COLUMN, so recreate table without role column
        if bind.dialect.name == "sqlite":
            # Create new table without role column
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
                    affiliation VARCHAR,
                    department_id INTEGER,
                    role_id INTEGER NOT NULL,
                    password_hash VARCHAR NOT NULL,
                    FOREIGN KEY(department_id) REFERENCES departments(id),
                    FOREIGN KEY(role_id) REFERENCES roles(id)
                )
                """
            )

            # Copy data (excluding role column)
            op.execute(
                """
                INSERT INTO users_new 
                    (id, account_name, first_name, middle_name, last_name, name, 
                     email, affiliation, department_id, role_id, password_hash)
                SELECT 
                    id, account_name, first_name, middle_name, last_name, name,
                    email, affiliation, department_id, role_id, password_hash
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
            op.drop_column("users", "role")


def downgrade() -> None:
    # Downgrade not fully implemented - would require recreating old schema
    pass
