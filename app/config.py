import logging
from psycopg_pool import AsyncConnectionPool
from contextlib import asynccontextmanager

logging.basicConfig(
  level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)

class Database:
  _pool: AsyncConnectionPool = None

  @classmethod
  async def init(cls, min_size: int, max_size: int) -> AsyncConnectionPool:
    if cls._pool is None:
      DSN = "postgresql://admin:adminsecret@localhost:5432/techtest"
      cls._pool = AsyncConnectionPool(
        conninfo=DSN, 
        min_size=min_size, 
        max_size=max_size, 
        open=False
      )
      await cls._pool.open()
      logging.info(f"Database pool initialized with {min_size}-{max_size} connections")
  
  @classmethod
  async def close(cls):
    if cls._pool:
      await cls._pool.close()
      cls._pool = None
      logging.info("Database connection pool closed")

  @classmethod
  @asynccontextmanager
  async def get_connection(cls):
    if cls._pool is None:
      raise RuntimeError("Database not initialized")
    else:
      async with cls._pool.connection() as conn:
        yield conn


async def run_migration() -> None:
  MIGRATIONS = [
    """
    CREATE TABLE IF NOT EXISTS users (
      id UUID PRIMARY KEY,
      name VARCHAR(255) NOT NULL,
      address VARCHAR(255) NOT NULL,
      created_at TIMESTAMPTZ DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS products (
      id UUID PRIMARY KEY,
      name VARCHAR(255) NOT NULL,
      price NUMERIC(18, 0) NOT NULL,
      stock INT NOT NULL,
      created_at TIMESTAMPTZ DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS orders (
      id UUID PRIMARY KEY,
      user_id UUID NOT NULL,
      total_price NUMERIC(18,0) NOT NULL,
      created_at TIMESTAMPTZ DEFAULT NOW(),
      CONSTRAINT fk_orders_users
        FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE RESTRICT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS order_items (
      id UUID PRIMARY KEY,
      order_id UUID NOT NULL,
      product_id UUID NOT NULL,
      amount INT NOT NULL,
      price NUMERIC(18, 0) NOT NULL,
      created_at TIMESTAMPTZ DEFAULT NOW(),
      CONSTRAINT fk_order_items_orders
        FOREIGN KEY (order_id)
        REFERENCES orders(id) ON DELETE RESTRICT,
      CONSTRAINT fk_order_items_products
        FOREIGN KEY (product_id)
        REFERENCES products(id) ON DELETE RESTRICT
    )
    """
  ]

  try:
    async with Database.get_connection() as conn:
      for i, migration in enumerate(MIGRATIONS, 1):
        try:
          await conn.execute(migration)
          logging.info(f"Migration {i}/{len(MIGRATIONS)} completed")
        except Exception as e:
          logging.error(f"Migration {i} failed: {e}")
          raise
    logging.info("All migrations completed successfully")
  except Exception as e:
    logging.error(f"Migration process failed: {e}")
    raise
  