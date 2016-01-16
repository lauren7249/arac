"""empty message

Revision ID: 61d1effeac7
Revises: 2a7cdeab308d
Create Date: 2016-01-15 19:11:57.168722

"""

# revision identifiers, used by Alembic.
revision = '61d1effeac7'
down_revision = '2a7cdeab308d'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_managers_user_id', table_name='managers')
    op.drop_constraint(u'managers_user_id_fkey', 'managers', type_='foreignkey')
    op.drop_column('managers', 'user_id')
    op.add_column('users', sa.Column('manager_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_users_manager_id'), 'users', ['manager_id'], unique=False)
    op.create_foreign_key(None, 'users', 'managers', ['manager_id'], ['manager_id'])
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'users', type_='foreignkey')
    op.drop_index(op.f('ix_users_manager_id'), table_name='users')
    op.drop_column('users', 'manager_id')
    op.add_column('managers', sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key(u'managers_user_id_fkey', 'managers', 'users', ['user_id'], ['user_id'])
    op.create_index('ix_managers_user_id', 'managers', ['user_id'], unique=False)
    ### end Alembic commands ###