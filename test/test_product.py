import pytest
from datetime import datetime
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
from app.model import Product

from app.main import app

@pytest.mark.anyio
async def test_add_product():
  mock_return_data = {
    "id": "019b96e9-27af-75a4-a4c8-12755693b966",
    "name": "Test Product",
    "price": 100,
    "stock": 50
  }
  with patch("app.routers.products.addProduct", new_callable=AsyncMock) as mock_add_product:

    mock_add_product.return_value = mock_return_data

    async with AsyncClient(
      transport=ASGITransport(app=app), base_url="http://localhost:8000"
    ) as ac:
      response = await ac.post(
        "/api/v1/products/",
        json={
          "name": "Test Product",
          "price": 100,
          "stock": 50
        }
      )
    
    assert response.status_code == 201
    expected_response = {
        "message": "Product created successfully", 
        "data": mock_return_data
    }
    assert response.json() == expected_response
    mock_add_product.assert_called_once()


@pytest.mark.anyio
async def test_add_product_failure():
  with patch("app.routers.products.addProduct", new_callable=AsyncMock) as mock_add_product:
    mock_add_product.side_effect = Exception("Database error")
    
    async with AsyncClient(
      transport=ASGITransport(app=app), base_url="http://localhost:8000"
    ) as ac:
      response = await ac.post(
        "/api/v1/products/",
        json={
          "name": "Test Product",
          "price": 100,
          "stock": 50
        }
      )
    
    assert response.status_code == 500
    assert "Failed to insert product" in response.json()["detail"]


@pytest.mark.anyio
async def test_get_products():
  mock_products: list[Product] = [
    Product(
      id="019b96e9-27af-75a4-a4c8-12755693b966",
      name="kapas",
      price=10000,
      stock=100,
      created_at=datetime.now()
    ),
    Product(
      id="019b96e9-27af-75a4-a4c8-12755693b966",
      name="batu",
      price=10000,
      stock=100,
      created_at=datetime.now()
    )
  ]
  
  with patch("app.routers.products.getProducts", new_callable=AsyncMock) as mock_get_products, \
    patch("app.routers.products.rd") as mock_redis:
    
    mock_get_products.return_value = mock_products
    mock_redis.get.return_value = None
    
    async with AsyncClient(
      transport=ASGITransport(app=app), base_url="http://localhost:8000"
    ) as ac:
      response = await ac.get("/api/v1/products/?page=1&per_page=10")
    
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 2
    assert data[0]["id"] == "019b96e9-27af-75a4-a4c8-12755693b966"
    assert data[0]["name"] == "kapas"
    assert data[0]["price"] == 10000
    assert data[0]["stock"] == 100
    mock_get_products.assert_called_once_with(page=1, per_page=10)


@pytest.mark.anyio
async def test_get_product_by_id():
  mock_product = Product(
    id="019b96e9-27af-75a4-a4c8-12755693b966",
    name="kapas",
    price=10000,
    stock=100,
    created_at=datetime.now()
  )
  
  with patch("app.routers.products.getProductById", new_callable=AsyncMock) as mock_get_product, \
    patch("app.routers.products.rd") as mock_redis:
    
    mock_get_product.return_value = mock_product
    mock_redis.get.return_value = None
    
    async with AsyncClient(
      transport=ASGITransport(app=app), base_url="http://localhost:8000"
    ) as ac:
      response = await ac.get("/api/v1/products/019b96e9-27af-75a4-a4c8-12755693b966")
    
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["id"] == "019b96e9-27af-75a4-a4c8-12755693b966"
    assert data["name"] == "kapas"
    assert data["price"] == 10000
    assert data["stock"] == 100
    mock_get_product.assert_called_once_with(productId="019b96e9-27af-75a4-a4c8-12755693b966")


@pytest.mark.anyio
async def test_get_product_by_id_not_found():
  with patch("app.routers.products.getProductById", new_callable=AsyncMock) as mock_get_product, \
   patch("app.routers.products.rd") as mock_redis:
    mock_get_product.return_value = None
    mock_redis.get.return_value = None
    
    async with AsyncClient(
      transport=ASGITransport(app=app), base_url="http://localhost:8000"
    ) as ac:
      response = await ac.get("/api/v1/products/nonexistent_id")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Product Not Found"


@pytest.mark.anyio
async def test_update_product():
  with patch("app.routers.products.updateProduct", new_callable=AsyncMock) as mock_update_product:
    async with AsyncClient(
      transport=ASGITransport(app=app), base_url="http://localhost:8000"
    ) as ac:
      response = await ac.put(
        "/api/v1/products/019b9605-51cb-763f-bfdd-db992540da8a",
        json={
          "name": "Updated Product",
          "price": 119,
          "stock": 30
        }
      )
    
    assert response.status_code == 200
    assert response.json() == {"message": "Product updated successfully"}
    mock_update_product.assert_called_once()


@pytest.mark.anyio
async def test_update_product_failure():
  with patch("app.routers.products.updateProduct", new_callable=AsyncMock) as mock_update_product:
    mock_update_product.side_effect = Exception("Database error")
    
    async with AsyncClient(
      transport=ASGITransport(app=app), base_url="http://localhost:8000"
    ) as ac:
      response = await ac.put(
        "/api/v1/products/prod_123",
        json={
          "name": "Updated Product",
          "price": 119,
          "stock": 30
        }
      )
    
    assert response.status_code == 500


@pytest.mark.anyio
async def test_delete_product():
  with patch("app.routers.products.deleteProduct", new_callable=AsyncMock) as mock_delete_product:
    async with AsyncClient(
      transport=ASGITransport(app=app), base_url="http://localhost:8000"
    ) as ac:
      response = await ac.delete("/api/v1/products/prod_123")
    
    assert response.status_code == 200
    assert response.json() == {"message": "product deleted successfully"}
    mock_delete_product.assert_called_once_with(productId="prod_123")


@pytest.mark.anyio
async def test_delete_product_failure():
  with patch("app.routers.products.deleteProduct", new_callable=AsyncMock) as mock_delete_product:
    mock_delete_product.side_effect = Exception("Database error")
    
    async with AsyncClient(
      transport=ASGITransport(app=app), base_url="http://localhost:8000"
    ) as ac:
      response = await ac.delete("/api/v1/products/prod_123")
    
    assert response.status_code == 500