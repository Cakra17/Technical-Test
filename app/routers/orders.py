import json
from app.config import logger, rd
from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from app.tasks import processOrder
from app.model import OrderPayload, Order
from app.services.orders import AddOrder, getOrders, getOrderById

router = APIRouter(
  prefix="/api/v1/orders",
  tags=["orders"]
)

def order_to_dict(order: Order) -> dict:
  return {
    "id": str(order.id),
    "amount": order.amount,
    "total_price": int(order.total_price),
    "status": order.status,
    "created_at": order.created_at.isoformat() if order.created_at else None
  }

def dict_to_order(od: dict) -> Order:
  return Order(
    id=od["id"],
    amount=od["amount"],
    total_price=od["total_price"],
    status=od["status"],
    created_at=od["created_at"]
  )

@router.post("/", status_code=201)
async def add_order(payload: OrderPayload):
  try:
    res = await AddOrder(payload)
    processOrder.delay(res)
    return {
      "message": "Order created and queued for processing",
      "order_id": res
    }
  except Exception as e:
    logger.error("Failed to insert order")
    raise HTTPException(status_code=500, detail=f"Failed to insert order: {e}")

@router.get("/", status_code=200)
async def get_orders(page: int = 1, per_page: int = 10):
  cache_key = f"orders:page:{page}:per_page:{per_page}"
  try:
    cache_data = rd.get(cache_key)
    if cache_data is not None:
      logger.info("cache hit")
      orders = [dict_to_order(od) for od in json.loads(cache_data)]
      return {
        "data": orders
      }
    data = await getOrders(page=page, per_page=per_page)
    orders_dict = [order_to_dict(o) for o in data]
    rd.setex(cache_key, 150, json.dumps(orders_dict))
    return {
      "data": data
    }
  except Exception as e:
    logger.error(f"Failed to get product: {e}")
    raise HTTPException(status_code=500, detail=str(e))

@router.get("/{orderId}", status_code=200)
async def get_order_Id(orderId: str):
  cache_key = f"order:{orderId}"
  try:
    cache_data = rd.get(cache_key)
    if cache_data is not None:
      logger.info("cache hit")
      order = dict_to_order(json.loads(cache_data))
      return {
        "data": order
      }
    data = await getOrderById(orderId=orderId)
  except Exception as e:
    logger.error(f"Failed to get product: {e}")
    raise HTTPException(status_code=500, detail=str(e))
  
  if data:
    order_dict = order_to_dict(data)
    rd.setex(cache_key, 150, json.dumps(order_dict))
    return {
      "data": data
    }
  else:
    raise HTTPException(status_code=404, detail="Order Not Found")
