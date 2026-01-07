import pytest
from datetime import datetime
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
from app.model import Order

from app.main import app

@pytest.mark.anyio
async def test_add_order():
  mock_order_id = "order_123"
  
  with patch("app.routers.orders.AddOrder", new_callable=AsyncMock) as mock_add_order, \
       patch("app.routers.orders.processOrder.delay") as mock_process:
    
    mock_add_order.return_value = mock_order_id
    
    async with AsyncClient(
      transport=ASGITransport(app=app), base_url="http://localhost:8000"
    ) as ac:
      response = await ac.post(
        "/api/v1/orders/",
        json={
          "product_id": "prod_123",
          "amount": 100
        }
      )
    
    assert response.status_code == 201
    assert response.json() == {"message": "Order is being processed"}
    mock_add_order.assert_called_once()
    mock_process.assert_called_once_with(mock_order_id)


@pytest.mark.anyio
async def test_add_order_failure():
  with patch("app.routers.orders.AddOrder", new_callable=AsyncMock) as mock_add_order:
    mock_add_order.side_effect = Exception("Database error")
    
    async with AsyncClient(
      transport=ASGITransport(app=app), base_url="http://localhost:8000"
    ) as ac:
      response = await ac.post(
        "/api/v1/orders/",
        json={
          "product_id": "prod_123",
          "amount": 100
        }
      )
    
    assert response.status_code == 500
    assert "Failed to insert order" in response.json()["detail"]


@pytest.mark.anyio
async def test_get_orders():
  mock_orders: list[Order] = [
    Order(
      id="019b96e9-27af-75a4-a4c8-12755693b966",
      total_price=10000,
      amount=100,
      status="success",
      created_at=datetime.now().isoformat()
    ),
    Order(
      id="019b96eb-305c-7a51-b17a-e61f301a65e3",
      total_price=10000,
      amount=10,
      status="failed",
      created_at=datetime.now().isoformat()
    )
  ]
  
  with patch("app.routers.orders.getOrders", new_callable=AsyncMock) as mock_get_orders, \
    patch("app.routers.orders.rd") as mock_redis:
    
    mock_get_orders.return_value = mock_orders
    mock_redis.get.return_value = None
    
    async with AsyncClient(
      transport=ASGITransport(app=app), base_url="http://localhost:8000"
    ) as ac:
      response = await ac.get("/api/v1/orders/?page=1&per_page=10")
    
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 2
    assert data[0]["id"] == "019b96e9-27af-75a4-a4c8-12755693b966"
    assert data[0]["total_price"] == 10000
    assert data[0]["amount"] == 100
    assert data[0]["status"] == "success"

    mock_get_orders.assert_called_once_with(page=1, per_page=10)


@pytest.mark.anyio
async def test_get_order_by_id():
  mock_order = Order(
    id="019b96e9-27af-75a4-a4c8-12755693b966",
    total_price=10000,
    amount=100,
    status="success",
    created_at=datetime.now().isoformat()
  )
  
  with patch("app.routers.orders.getOrderById", new_callable=AsyncMock) as mock_get_order, \
    patch("app.routers.orders.rd") as mock_redis:

    mock_get_order.return_value = mock_order
    mock_redis.get.return_value = None
    
    async with AsyncClient(
      transport=ASGITransport(app=app), base_url="http://localhost:8000"
    ) as ac:
      response = await ac.get("/api/v1/orders/019b96e9-27af-75a4-a4c8-12755693b966")
    
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["id"] == "019b96e9-27af-75a4-a4c8-12755693b966"
    assert data["total_price"] == 10000
    assert data["amount"] == 100
    assert data["status"] == "success"
    mock_get_order.assert_called_once_with(orderId="019b96e9-27af-75a4-a4c8-12755693b966")


@pytest.mark.anyio
async def test_get_order_by_id_not_found():
  with patch("app.routers.orders.getOrderById", new_callable=AsyncMock) as mock_get_order:
    mock_get_order.return_value = None
    
    async with AsyncClient(
      transport=ASGITransport(app=app), base_url="http://localhost:8000"
    ) as ac:
      response = await ac.get("/api/v1/orders/nonexistent_id")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Product Not Found"