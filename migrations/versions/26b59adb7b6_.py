"""empty message

Revision ID: 26b59adb7b6
Revises: 5096425b46bd
Create Date: 2015-12-13 15:09:11.454873

"""

# revision identifiers, used by Alembic.
revision = '26b59adb7b6'
down_revision = '5096425b46bd'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('cloudsponge_raw',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_email', sa.String(500), nullable=True),
    sa.Column('account_email', sa.String(500), nullable=True),
    sa.Column('primary_contact_email', sa.String(500), nullable=True),
    sa.Column('service', sa.String(500), nullable=True),
    sa.Column('contact', postgresql.JSONB(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cloudsponge_raw_account_email'), 'cloudsponge_raw', ['account_email'], unique=False)
    op.create_index(op.f('ix_cloudsponge_raw_primary_contact_email'), 'cloudsponge_raw', ['primary_contact_email'], unique=False)
    op.create_index(op.f('ix_cloudsponge_raw_service'), 'cloudsponge_raw', ['service'], unique=False)
    op.create_index(op.f('ix_cloudsponge_raw_user_email'), 'cloudsponge_raw', ['user_email'], unique=False)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_cloudsponge_raw_user_email'), table_name='cloudsponge_raw')
    op.drop_index(op.f('ix_cloudsponge_raw_service'), table_name='cloudsponge_raw')
    op.drop_index(op.f('ix_cloudsponge_raw_primary_contact_email'), table_name='cloudsponge_raw')
    op.drop_index(op.f('ix_cloudsponge_raw_account_email'), table_name='cloudsponge_raw')
    op.drop_table('cloudsponge_raw')
    ### end Alembic commands ###
