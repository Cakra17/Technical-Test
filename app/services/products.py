from app.config import logger
from app.config import Database
from app.model import Product
from typing import Union

async def addProduct(product: Product) -> Product:
  try:
    async with Database.get_connection() as conn:
      async with conn.cursor() as cur:
        await cur.execute("""
          INSERT INTO products (id, name, stock, price) VALUES (%s, %s, %s, %s) RETURNING created_at;
        """,
        (product.id, product.name, product.stock, product.price,)) 
        res = await cur.fetchone()
        return Product(
          id=product.id,
          name=product.name,
          stock=product.stock,
          price=product.price,
          created_at=res[0]
        )
  except Exception as e:
    logger.error(f"Failed to insert {e}")
    raise

async def getProducts(page: int, per_page: int) -> list[Product]:
  try:
    async with Database.get_connection() as conn:
      async with conn.cursor() as cur:
        offset = (page - 1) * per_page
        await cur.execute("""
          SELECT id, name, stock, price, created_at FROM products ORDER BY created_at DESC LIMIT %s OFFSET %s;
        """,
        (per_page, offset,))
        product_data = await cur.fetchall()

        products: list[Product] = []
        for data in product_data:
          products.append(
            Product(
              id=data[0], name=data[1], stock=data[2], price=data[3], created_at=data[4]
            )
          )
        return products
  except Exception as e:
    logger.error(f"Failed to insert user {e}")
    raise

async def getProductById(productId: str) -> Union[Product,None]:
  try:
    async with Database.get_connection() as conn:
      async with conn.cursor() as cur:
        await cur.execute("""
          SELECT id, name, stock, price, created_at FROM products WHERE id = %s;
        """,
        (productId,))
        product_data = await cur.fetchone()

        if product_data:
          return Product(
            id=product_data[0], name=product_data[1], stock=product_data[2], price=product_data[3], created_at=product_data[4]
          )
        else:
          return None
  except Exception as e:
    logger.error(f"Failed to get user {e}")
    raise

async def updateProduct(product: Product) -> None:
  try:
    async with Database.get_connection() as conn:
      async with conn.cursor() as cur:
        await cur.execute("""
          UPDATE products SET name = %s, stock = %s, price = %s WHERE id = %s;
        """,
        (product.name, product.stock, product.price, product.id,))

        if cur.rowcount == 0:
          logger.warning(f"No product found with ID: {product.id}")
          raise ValueError(f"Product with ID {product.id} not found")
  except ValueError:
    raise
  except Exception as e:
    logger.error(f"Failed to update user {e}")
    raise

async def deleteProduct(productId: str) -> None:
  try:
    async with Database.get_connection() as conn:
      async with conn.cursor() as cur:
        await cur.execute("""
          DELETE FROM products WHERE id = %s;
        """,
        (productId,))
        if cur.rowcount == 0:
          logger.warning(f"No product found with ID: {productId}")
          raise ValueError(f"Product with ID {productId} not found")
  except ValueError:
    raise
  except Exception as e:
    logger.error(f"Failed to delete user {e}")
    raise