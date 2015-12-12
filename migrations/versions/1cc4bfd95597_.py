"""empty message

Revision ID: 1cc4bfd95597
Revises: 58423c7d2bae
Create Date: 2015-12-11 17:08:08.303263

"""

# revision identifiers, used by Alembic.
revision = '1cc4bfd95597'
down_revision = '58423c7d2bae'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('prospect', sa.Column('common_schools', postgresql.JSONB(), nullable=True))
    op.drop_column('prospect', 'common_school')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('prospect', sa.Column('common_school', sa.VARCHAR(length=200), autoincrement=False, nullable=True))
    op.drop_column('prospect', 'common_schools')
    ### end Alembic commands ###
