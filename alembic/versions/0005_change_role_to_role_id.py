"""change user role to role_id and add access_level to roles

Revision ID: 0005
Revises: 0004
Create Date: 2025-11-22
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


# Map roles to access levels based on AccessLevel enum
ROLE_ACCESS_LEVELS = {
    "APPLICATION_MANAGER": 6,
    "PI": 2,
    "PROJECT_MANAGER": 3,
    "ALLOCATOR": 4,
    "APPROVER": 5,
}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    # Add access_level column to roles table if it doesn't exist
    role_columns = {col["name"] for col in inspector.get_columns("roles")}
    if "access_level" not in role_columns:
        op.add_column(
            "roles",
            sa.Column("access_level", sa.Integer(), nullable=True)
        )
        
        # Update access_level for existing roles
        for role_slug, access_level in ROLE_ACCESS_LEVELS.items():
            op.execute(
                f"UPDATE roles SET access_level = {access_level} "
                f"WHERE slug = '{role_slug}'"
            )
    
    # Check if we need to convert role column to role_id
    user_columns = {col["name"] for col in inspector.get_columns("users")}
    
    if "role" in user_columns and "role_id" not in user_columns:
        # Add role_id column
        op.add_column(
            "users",
            sa.Column("role_id", sa.Integer(), nullable=True)
        )
        
        # Populate role_id from role enum values
        # First, ensure all roles exist in roles table
        op.execute("""
            INSERT OR IGNORE INTO roles (slug, display_name, access_level)
            VALUES 
                ('APPLICATION_MANAGER', 'Application Manager', 6),
                ('PI', 'PI', 2),
                ('PROJECT_MANAGER', 'Project Manager', 3),
                ('ALLOCATOR', 'Allocator', 4),
                ('APPROVER', 'Approver', 5)
        """)
        
        # Update role_id based on role
        op.execute("""
            UPDATE users
            SET role_id = (
                SELECT id FROM roles WHERE roles.slug = users.role
            )
        """)
        
        # Create index on role_id
        op.create_index("ix_users_role_id", "users", ["role_id"])
        
        # For SQLite, we can't easily drop the old role column
        # We'll keep both for now and the application will use role_id


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    user_columns = {col["name"] for col in inspector.get_columns("users")}
    
    if "role_id" in user_columns:
        op.drop_index("ix_users_role_id", "users")
        op.drop_column("users", "role_id")
    
    role_columns = {col["name"] for col in inspector.get_columns("roles")}
    if "access_level" in role_columns:
        op.drop_column("roles", "access_level")
