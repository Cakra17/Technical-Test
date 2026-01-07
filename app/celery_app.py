import os
from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown
from app.config import logger
import asyncio

os.environ.setdefault("FORKED_BY_MULTIPROCESSING", "1")
redis_url = os.getenv("REDIS_URL","redis://redis:6379/0")
celery_app = Celery(
  "jobs",
  broker= redis_url,
  backend= redis_url,
  include= ["app.tasks"]
)

@worker_process_init.connect
def init_worker(**kwargs):
    from app.config import Database
    
    logger.info("Initializing database pool for Celery worker...")
    asyncio.run(Database.initialize(min_size=2, max_size=5))
    logger.info("Database pool initialized for Celery worker")

@worker_process_shutdown.connect
def shutdown_worker(**kwargs):
    from app.config import Database
    
    logger.info("Closing database pool for Celery worker...")
    asyncio.run(Database.close())
    logger.info("Database pool closed for Celery worker")