"""empty message

Revision ID: c4b7078341e
Revises: 116d7f936250
Create Date: 2016-01-13 22:25:20.431263

"""

# revision identifiers, used by Alembic.
revision = 'c4b7078341e'
down_revision = '116d7f936250'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('linkedin_industry', sa.String(length=1024), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'linkedin_industry')
    ### end Alembic commands ###
