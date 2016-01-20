"""empty message

Revision ID: 20f2fcc1cdc0
Revises: 47a16fb1c0f8
Create Date: 2016-01-19 18:42:14.669114

"""

# revision identifiers, used by Alembic.
revision = '20f2fcc1cdc0'
down_revision = '47a16fb1c0f8'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('managers', sa.Column('address', sa.String(length=1000), nullable=True))
    op.add_column('managers', sa.Column('certifications', sa.String(length=500), nullable=True))
    op.add_column('managers', sa.Column('name_suffix', sa.String(length=500), nullable=True))
    op.add_column('managers', sa.Column('phone', sa.String(length=30), nullable=True))
    op.drop_column('managers', 'json')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('managers', sa.Column('json', postgresql.JSON(), autoincrement=False, nullable=True))
    op.drop_column('managers', 'phone')
    op.drop_column('managers', 'name_suffix')
    op.drop_column('managers', 'certifications')
    op.drop_column('managers', 'address')
    ### end Alembic commands ###