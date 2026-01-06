import logging
import uuid
from app.config import Database
from app.model import OrderPayload, Order

async def AddOrder(order: OrderPayload):
  try:
    async with Database.get_connection() as conn:
      async with conn.transaction():
        async with conn.cursor() as cur:
          await cur.execute("""
              SELECT price FROM products WHERE id = %s
          """,
          (order.product_id,))
          res = await cur.fetchone()
          
          total_price = order.amount * res[0]
          orderId = uuid.uuid7()
          await conn.execute("""
            INSERT INTO orders (id, product_id, amount, total_price, status) VALUES (%s, %s, %s, %s, %s)
          """,
          (orderId, order.product_id, order.amount, total_price, "pending",)) 
  except Exception as e:
    logging.error(f"Failed to insert {e}")
    raise

async def getOrders(page: int, per_page: int):
  try:
    async with Database.get_connection() as conn:
      async with conn.cursor() as cur:
        offset = (page - 1) * per_page
        await cur.execute("""
          SELECT id, amount, total_price, status, created_at FROM orders ORDER BY created_at DESC LIMIT %s OFFSET %s;
        """,
        (per_page, offset,))
        order_data = await cur.fetchall()

        orders: list[Order] = []
        for data in order_data:
          orders.append(
            Order(
              id = data[0], amount = data[1], total_price = data[2], status = data[3], created_at = data[4]
            )
          )
        return orders
  except Exception as e:
    logging.error(f"Failed to get orders {e}")
    raise

async def getOrderById(orderId: str):
  try:
    async with Database.get_connection() as conn:
      async with conn.cursor() as cur:
        await cur.execute("""
          SELECT id, amount, total_price, status, created_at FROM orders WHERE id = %s;
        """,
        (orderId,))
        order_data = await cur.fetchone()

        if order_data:
          return Order(
            id = order_data[0], 
            amount = order_data[1], 
            total_price = order_data[2], 
            status = order_data[3], 
            created_at = order_data[4]
          )
        else:
          return None
  except Exception as e:
    logging.error(f"Failed to get user {e}")
    raise

async def validateOrder(orderId: str):
  try:
    async with Database.get_connection() as conn:
      async with conn.transaction():
        async with conn.cursor() as cur:
          await conn.execute("""
              SELECT id, product_id, amount, total_price, status FROM orders WHERE id = %s FOR UPDATE
          """,
          (orderId,))
          order = await conn.fetchone()

          if not order:
            raise ValueError("Order not found")

          if order[4] != "pending":
            raise (f"Order {orderId} already processed with status {order[4]}")

          await conn.execute("""
              SELECT name, stock, price FROM products WHERE id = %s FOR UPDATE
          """,
          (order[1],))
          product = await conn.fetchone()

          if order[2] > product[1]:
            await conn.execute("""
              UPDATE orders SET status = %s WHERE id = %s
            """,
            ("failed", orderId))
            raise ValueError(f"Insufficient stock for {product[0]}: need {order[2]}, available {product[1]}")
          
          await conn.execute("""
              UPDATE products SET stock = stock - %s WHERE id = %s
          """,
          (order[2], order[1],))
          
          await conn.execute("""
              UPDATE orders SET status = %s WHERE id = %s
          """,
          ("success", orderId,))
  except Exception as e:
    logging.error(f"Failed to insert {e}")
    raise 