from fastapi import FastAPI
from .config import Database, run_migration
from .routers import users, products, orders
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
  await Database.init(min_size=5, max_size=10)
  await run_migration()
  yield
  await Database.close()

app = FastAPI(lifespan=lifespan)
app.include_router(users.router)
app.include_router(products.router)
app.include_router(orders.router)

@app.get("/api/v1/health")
async def health():
  return {"status": "Up and Running!!"}

