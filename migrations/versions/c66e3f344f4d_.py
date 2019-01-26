"""empty message

Revision ID: c66e3f344f4d
Revises: 
Create Date: 2019-01-26 01:08:49.268282

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c66e3f344f4d'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('devices',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=32), nullable=False),
    sa.Column('description', sa.TEXT(), nullable=True),
    sa.Column('code', sa.String(length=30), nullable=False),
    sa.Column('date_created', sa.DateTime(timezone=True), nullable=True),
    sa.Column('date_updated', sa.DateTime(timezone=True), nullable=True),
    sa.Column('status', sa.Enum('enabled', 'disabled', 'deleted'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_table('contents',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=True),
    sa.Column('description', sa.TEXT(), nullable=True),
    sa.Column('device_id', sa.Integer(), nullable=True),
    sa.Column('date_created', sa.DateTime(timezone=True), nullable=True),
    sa.Column('date_updated', sa.DateTime(timezone=True), nullable=True),
    sa.Column('expire_date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('status', sa.Enum('enabled', 'disabled', 'deleted'), nullable=False),
    sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('contents')
    op.drop_table('devices')
    # ### end Alembic commands ###
