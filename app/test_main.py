import pytest
from httpx import AsyncClient, ASGITransport

from .main import app

@pytest.mark.anyio
async def test_root():
  async with AsyncClient(
    transport=ASGITransport(app=app), base_url="http://localhost:8000/api/v1/"
  ) as ac:
    response = await ac.get("/health")
  assert response.status_code == 200
  assert response.json() == {"status": "Up and Running!!"}