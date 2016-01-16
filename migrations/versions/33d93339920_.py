"""empty message

Revision ID: 33d93339920
Revises: 61d1effeac7
Create Date: 2016-01-15 19:33:40.442954

"""

# revision identifiers, used by Alembic.
revision = '33d93339920'
down_revision = '61d1effeac7'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('managers', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_managers_user_id'), 'managers', ['user_id'], unique=False)
    op.create_foreign_key(None, 'managers', 'users', ['user_id'], ['user_id'])
    op.drop_constraint(u'users_manager_id_fkey', 'users', type_='foreignkey')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_foreign_key(u'users_manager_id_fkey', 'users', 'managers', ['manager_id'], ['manager_id'])
    op.drop_constraint(None, 'managers', type_='foreignkey')
    op.drop_index(op.f('ix_managers_user_id'), table_name='managers')
    op.drop_column('managers', 'user_id')
    ### end Alembic commands ###