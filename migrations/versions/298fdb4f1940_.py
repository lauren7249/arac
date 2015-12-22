"""empty message

Revision ID: 298fdb4f1940
Revises: 58d483953e52
Create Date: 2015-12-13 20:24:33.121540

"""

# revision identifiers, used by Alembic.
revision = '298fdb4f1940'
down_revision = '58d483953e52'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('client_prospect', sa.Column('common_schools', postgresql.JSONB(), nullable=True))
    op.drop_column('prospect', 'common_schools')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('prospect', sa.Column('common_schools', postgresql.JSONB(), autoincrement=False, nullable=True))
    op.drop_column('client_prospect', 'common_schools')
    ### end Alembic commands ###