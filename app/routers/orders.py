import logging
from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from app.tasks import processOrder
from app.model import OrderPayload
from app.services.orders import AddOrder, getOrders, getOrderById

router = APIRouter(
  prefix="/api/v1/orders",
  tags=["orders"]
)

@router.post("/", status_code=201)
async def add_order(payload: OrderPayload):
  try:
    res = await AddOrder(payload)
    processOrder.delay(res)
    return {
      "message": "Order is being processed"
    }
  except Exception as e:
    logging.error("Failed to insert order")
    raise HTTPException(status_code=500, detail=f"Failed to insert order: {e}")

@router.get("/", status_code=200)
async def get_orders(page: int = 1, per_page: int = 10):
  try:
    data = await getOrders(page=page, per_page=per_page)
    return {
      "data": data
    }
  except Exception as e:
    logging.error(f"Failed to get product: {e}")
    raise HTTPException(status_code=500, detail=str(e))

@router.get("/{orderId}", status_code=200)
async def get_order_Id(orderId: str):
  try:
    data = await getOrderById(orderId=orderId)
  except Exception as e:
    logging.error(f"Failed to get product: {e}")
    raise HTTPException(status_code=500, detail=str(e))
  
  if data:
    return {
      "data": data
    }
  else:
    raise HTTPException(status_code=404, detail="Product Not Found")
