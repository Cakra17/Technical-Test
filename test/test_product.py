import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock

from app.main import app

@pytest.mark.anyio
async def test_add_product():
  with patch("app.routers.products.addProduct", new_callable=AsyncMock) as mock_add_product:
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
    assert response.json() == {"message": "Product created successfully"}
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
  mock_products = [
    {"id": "prod_1", "name": "Product 1", "price": 50, "stock": 10},
    {"id": "prod_2", "name": "Product 2", "price": 75, "stock": 20}
  ]
  
  with patch("app.routers.products.getProducts", new_callable=AsyncMock) as mock_get_products:
    mock_get_products.return_value = mock_products
    
    async with AsyncClient(
      transport=ASGITransport(app=app), base_url="http://localhost:8000"
    ) as ac:
      response = await ac.get("/api/v1/products/?page=1&per_page=10")
    
    assert response.status_code == 200
    assert response.json() == {"data": mock_products}
    mock_get_products.assert_called_once_with(page=1, per_page=10)


@pytest.mark.anyio
async def test_get_product_by_id():
  mock_product = {
    "id": "prod_123",
    "name": "Test Product",
    "price": 100,
    "stock": 50
  }
  
  with patch("app.routers.products.getProductById", new_callable=AsyncMock) as mock_get_product:
    mock_get_product.return_value = mock_product
    
    async with AsyncClient(
      transport=ASGITransport(app=app), base_url="http://localhost:8000"
    ) as ac:
      response = await ac.get("/api/v1/products/prod_123")
    
    assert response.status_code == 200
    assert response.json() == {"data": mock_product}
    mock_get_product.assert_called_once_with(productId="prod_123")


@pytest.mark.anyio
async def test_get_product_by_id_not_found():
  with patch("app.routers.products.getProductById", new_callable=AsyncMock) as mock_get_product:
    mock_get_product.return_value = None
    
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