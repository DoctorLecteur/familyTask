"""tasks tables

Revision ID: 375efe166af7
Revises: 40fdd65da663
Create Date: 2022-07-18 21:51:41.036739

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '375efe166af7'
down_revision = '40fdd65da663'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('tasks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('id_type_task', sa.Integer(), nullable=True),
    sa.Column('title', sa.String(length=64), nullable=True),
    sa.Column('id_priority', sa.Integer(), nullable=True),
    sa.Column('id_status', sa.Integer(), nullable=True),
    sa.Column('id_users', sa.Integer(), nullable=True),
    sa.Column('deadline', sa.DateTime(), nullable=True),
    sa.Column('description', sa.String(length=1024), nullable=True),
    sa.ForeignKeyConstraint(['id_priority'], ['priority.id'], ),
    sa.ForeignKeyConstraint(['id_status'], ['status.id'], ),
    sa.ForeignKeyConstraint(['id_type_task'], ['type_task.id'], ),
    sa.ForeignKeyConstraint(['id_users'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tasks_title'), 'tasks', ['title'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_tasks_title'), table_name='tasks')
    op.drop_table('tasks')
    # ### end Alembic commands ###
