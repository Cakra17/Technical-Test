import uuid
import logging
from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from app.model import Product, ProductPayload
from app.services.products import addProduct, getProducts, getProductById, deleteProduct, updateProduct

router = APIRouter(
  prefix="/api/v1/products",
  tags=["products"]
)

@router.post("/")
async def add_product(product: ProductPayload):
  try:
    productId = uuid.uuid7()
    data = Product(
      id=productId,
      name=product.name,
      price=product.price,
      stock=product.stock,
      created_at=None
    )
    await addProduct(product=data)
    return {
      "message": "Product created successfully"
    }
  except Exception as e:
    logging.error("Failed to insert product")
    raise HTTPException(status_code=500, detail=f"Failed to insert product: {e}")

@router.get("/")
async def get_products(page: int = 1, per_page: int = 10):
  try:
    data = await getProducts(page=page, per_page=per_page)
    if data:
      return {
        "data": data
      }
    else:
      raise HTTPException(status_code=404, detail="Product Not Found")
  except Exception as e:
    logging.error(f"Failed to get product: {e}")
    raise HTTPException(status_code=500, detail=str(e))

@router.get("/{productId}")
async def get_product_by_id(productId: str):
  try:
    data = await getProductById(productId=productId)
    if data:
      return {
        "data": data
      }
    else:
      raise HTTPException(status_code=404, detail="Product Not Found")
  except Exception as e:
    logging.error(f"Failed to get product: {e}")
    raise HTTPException(status_code=500, detail=str(e))

@router.put("/{productId}")
async def update_user(productId: str, payload: ProductPayload):
  try:
    data = Product(
      id=productId,
      name=payload.name,
      price=payload.price,
      stock=payload.stock,
      created_at=None
    )
    await updateProduct(product=data)
    return {
      "message": "Product updated successfully"
    }
  except Exception as e:
    logging.error(f"Failed to update user: {e}")
    raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{productId}")
async def delete_user(productId: str):
  try:
    await deleteProduct(productId=productId)
    return {
      "message": "product deleted successfully"
    }
  except Exception as e:
    logging.error(f"Failed to delete user: {e}")
    raise HTTPException(status_code=500, detail=str(e))