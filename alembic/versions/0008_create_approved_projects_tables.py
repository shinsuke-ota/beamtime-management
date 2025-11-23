"""create approved projects tables

Revision ID: 0008
Revises: 0007
Create Date: 2025-11-23

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check and create experimental_courses table
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if 'experimental_courses' not in inspector.get_table_names():
        op.create_table(
            'experimental_courses',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name')
        )
        op.create_index(op.f('ix_experimental_courses_id'), 'experimental_courses', ['id'], unique=False)

        # Insert default experimental courses
        op.execute("""
            INSERT INTO experimental_courses (name) VALUES
            ('WS'), ('WSS'), ('WN'), ('EN'), ('ENN'), ('N0'), ('N'), ('W'), ('H')
        """)

    # Create approved_projects table
    if 'approved_projects' not in inspector.get_table_names():
        op.create_table(
            'approved_projects',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('project_number', sa.String(), nullable=False),
            sa.Column('title', sa.String(), nullable=False),
            sa.Column('summary', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('project_number')
        )
        op.create_index(op.f('ix_approved_projects_id'), 'approved_projects', ['id'], unique=False)
        op.create_index(op.f('ix_approved_projects_project_number'), 'approved_projects', ['project_number'], unique=False)

    # Create project_pis table
    if 'project_pis' not in inspector.get_table_names():
        op.create_table(
            'project_pis',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('project_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('is_primary', sa.Boolean(), nullable=False),
            sa.ForeignKeyConstraint(['project_id'], ['approved_projects.id'], ),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('project_id', 'user_id', name='uq_project_pi')
        )
        op.create_index(op.f('ix_project_pis_id'), 'project_pis', ['id'], unique=False)

    # Create beam_requests table
    if 'beam_requests' not in inspector.get_table_names():
        op.create_table(
            'beam_requests',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('project_id', sa.Integer(), nullable=False),
            sa.Column('beam_species', sa.String(), nullable=False),
            sa.Column('max_intensity', sa.String(), nullable=True),
            sa.Column('required_resolution', sa.String(), nullable=True),
            sa.Column('course_id', sa.Integer(), nullable=False),
            sa.Column('planned_irradiation_hours', sa.Integer(), nullable=False),
            sa.Column('completed_irradiation_hours', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['course_id'], ['experimental_courses.id'], ),
            sa.ForeignKeyConstraint(['project_id'], ['approved_projects.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_beam_requests_id'), 'beam_requests', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_beam_requests_id'), table_name='beam_requests')
    op.drop_table('beam_requests')
    op.drop_index(op.f('ix_project_pis_id'), table_name='project_pis')
    op.drop_table('project_pis')
    op.drop_index(op.f('ix_approved_projects_project_number'), table_name='approved_projects')
    op.drop_index(op.f('ix_approved_projects_id'), table_name='approved_projects')
    op.drop_table('approved_projects')
    op.drop_index(op.f('ix_experimental_courses_id'), table_name='experimental_courses')
    op.drop_table('experimental_courses')
