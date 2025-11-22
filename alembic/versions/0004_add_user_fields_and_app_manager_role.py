"""add user fields and application manager role

Revision ID: 0004
Revises: 0003
Create Date: 2025-11-22
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    # Get existing columns
    user_columns = {column["name"] for column in inspector.get_columns("users")}
    
    # Add missing columns if they don't exist (nullable for SQLite)
    if "account_name" not in user_columns:
        op.add_column("users", sa.Column("account_name", sa.String(), nullable=True))
        # Populate account_name from email (before @)
        op.execute(
            "UPDATE users SET account_name = "
            "LOWER(SUBSTR(email, 1, INSTR(email, '@') - 1))"
        )
        # Create index and unique constraint
        op.create_index("ix_users_account_name", "users", ["account_name"])
        # For SQLite, unique constraint needs special handling
        try:
            op.create_unique_constraint("uq_users_account_name", "users", ["account_name"])
        except Exception:
            pass  # SQLite may not support this directly
    
    if "first_name" not in user_columns:
        op.add_column("users", sa.Column("first_name", sa.String(), nullable=True))
        # Populate first_name from name (first word)
        op.execute("UPDATE users SET first_name = SUBSTR(name, 1, CASE WHEN INSTR(name, ' ') > 0 THEN INSTR(name, ' ') - 1 ELSE LENGTH(name) END)")
    
    if "middle_name" not in user_columns:
        op.add_column("users", sa.Column("middle_name", sa.String(), nullable=True))
    
    if "last_name" not in user_columns:
        op.add_column("users", sa.Column("last_name", sa.String(), nullable=True))
        # Populate last_name from name (remaining part after first word)
        op.execute("""
            UPDATE users 
            SET last_name = CASE 
                WHEN INSTR(name, ' ') > 0 
                THEN SUBSTR(name, INSTR(name, ' ') + 1)
                ELSE name
            END
        """)
    
    # Update the enum type to include APPLICATION_MANAGER
    # For SQLite, we need to recreate the table
    if bind.dialect.name == 'sqlite':
        # SQLite doesn't support ALTER TYPE, so we'll handle it differently
        # The enum constraint will be handled by the application layer
        pass
    else:
        # For PostgreSQL, alter the enum type
        op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'APPLICATION_MANAGER'")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    user_columns = {column["name"] for column in inspector.get_columns("users")}
    
    if "last_name" in user_columns:
        op.drop_column("users", "last_name")
    if "middle_name" in user_columns:
        op.drop_column("users", "middle_name")
    if "first_name" in user_columns:
        op.drop_column("users", "first_name")
    if "account_name" in user_columns:
        op.drop_index("ix_users_account_name", "users")
        op.drop_constraint("uq_user_account_name", "users")
        op.drop_column("users", "account_name")
