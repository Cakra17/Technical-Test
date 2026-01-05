import logging
from app.config import Database
from app.model import User
from psycopg import errors

async def addUser(user: User) -> None:
  try:
    async with Database.get_connection() as conn:
      async with conn.cursor() as cur:
        await cur.execute("""
          INSERT INTO users (id, name, address, email) VALUES (%s, %s, %s, %s);
        """,
        (user.id, user.name, user.address, user.email,))
  except errors.UniqueViolation:
    logging.error(f"User with email {user.email} already exists")
    raise ValueError("Email already exists")
  except Exception as e:
    logging.error(f"Failed to insert user {e}")
    raise

async def getUserById(userId: str):
  try:
    async with Database.get_connection() as conn:
      async with conn.cursor() as cur:
        await cur.execute("""
          SELECT id, name, address, email, created_at FROM users WHERE id = %s;
        """,
        (userId,))
        user_data = await cur.fetchone()

        if user_data:
          return User(
            id=user_data[0], name=user_data[1], address=user_data[2], email=user_data[3], created_at=user_data[4]
          )
        else:
          return None
  except Exception as e:
    logging.error(f"Failed to get user {e}")
    raise

async def updateUser(user: User):
  try:
    async with Database.get_connection() as conn:
      async with conn.cursor() as cur:
        await cur.execute("""
          UPDATE users SET name = %s, address = %s, email = %s WHERE id = %s;
        """,
        (user.name, user.address, user.email, user.id,))

        if cur.rowcount == 0:
          logging.warning(f"No user found with ID: {user.id}")
          raise ValueError(f"User with ID {user.id} not found")
  except ValueError:
    raise
  except Exception as e:
    logging.error(f"Failed to update user {e}")
    raise

async def deleteUser(userId: str):
  try:
    async with Database.get_connection() as conn:
      async with conn.cursor() as cur:
        await cur.execute("""
          DELETE FROM users WHERE id = %s;
        """,
        (userId,))
        if cur.rowcount == 0:
          logging.warning(f"No user found with ID: {userId}")
          raise ValueError(f"User with ID {userId} not found")
  except ValueError:
    raise
  except Exception as e:
    logging.error(f"Failed to delete user {e}")
    raise