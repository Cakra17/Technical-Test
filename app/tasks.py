import asyncio
from .celery_app import celery_app
from app.services.orders import validateOrder
from app.config import logger, Database

@celery_app.task(bind=True, max_retries=3)
def processOrder(self, orderId: str):
    try:
        asyncio.run(run(orderId), loop_factory=asyncio.SelectorEventLoop)
    except Exception as e:
        logger.error(f"Order {orderId} processing failed: {e}")
        raise self.retry(exc=e, countdown=5)
  
async def run(orderId: str):
    await Database.init(min_size=2, max_size=5)
    
    try:
        logger.info(f"Order {orderId} Processed")
        res = await validateOrder(orderId=orderId)
        await asyncio.sleep(5)
        if res["status"] == "failed":
            logger.error(f"{res["reason"]}: {res["details"]}")
            logger.info("Process is finished, your order failed")
        elif res["status"] == "success":
            logger.info("Process is finished, your order success")
    except Exception as e:
        logger.error(f"Order {orderId} validation failed: {e}")
        raise
    finally:
        await Database.close()