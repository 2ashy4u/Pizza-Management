"""Updated Orders model and added Cart model

Revision ID: 89d72194f6d0
Revises: 
Create Date: 2023-04-27 10:35:02.600327

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '89d72194f6d0'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('orders', schema=None) as batch_op:
        # batch_op.drop_constraint('fk_orders_customers', type_='foreignkey')
        batch_op.drop_column('quantity')
        batch_op.drop_column('pizza_id')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('pizza_id', sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column('quantity', sa.INTEGER(), nullable=False))
        # batch_op.create_foreign_key('fk_orders_pizzas', 'pizzas', ['pizza_id'], ['id'])

    # ### end Alembic commands ###