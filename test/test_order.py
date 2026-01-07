import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock

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
  mock_orders = [
    {"id": "order_1", "product_id": "prod_123", "total_price": 10000, "amount": 100, "status": "success"},
    {"id": "order_2", "product_id": "prod_456", "total_price": 10000, "amount": 10, "status": "failed"}
  ]
  
  with patch("app.routers.orders.getOrders", new_callable=AsyncMock) as mock_get_orders:
    mock_get_orders.return_value = mock_orders
    
    async with AsyncClient(
      transport=ASGITransport(app=app), base_url="http://localhost:8000"
    ) as ac:
      response = await ac.get("/api/v1/orders/?page=1&per_page=10")
    
    assert response.status_code == 200
    assert response.json() == {"data": mock_orders}
    mock_get_orders.assert_called_once_with(page=1, per_page=10)


@pytest.mark.anyio
async def test_get_order_by_id():
  mock_order = {
    "id": "order_123",
    "customer_name": "John Doe",
    "total": 100.00,
    "status": "processing"
  }
  
  with patch("app.routers.orders.getOrderById", new_callable=AsyncMock) as mock_get_order:
    mock_get_order.return_value = mock_order
    
    async with AsyncClient(
      transport=ASGITransport(app=app), base_url="http://localhost:8000"
    ) as ac:
      response = await ac.get("/api/v1/orders/order_123")
    
    assert response.status_code == 200
    assert response.json() == {"data": mock_order}
    mock_get_order.assert_called_once_with(orderId="order_123")


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