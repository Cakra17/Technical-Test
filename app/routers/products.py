import uuid
import json
from app.config import rd, logger
from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from app.model import Product, ProductPayload
from app.services.products import addProduct, getProducts, getProductById, deleteProduct, updateProduct

router = APIRouter(
  prefix="/api/v1/products",
  tags=["products"]
)

def product_to_dict(product: Product) -> dict:
  return {
    "id": str(product.id),
    "name": product.name,
    "price": int(product.price),
    "stock": product.stock,
    "created_at": product.created_at.isoformat() if product.created_at else None
  }

def dict_to_product(pd: dict) -> Product:
  return Product(
    id=pd["id"],
    name=pd["name"],
    price=pd["price"],
    stock=pd["stock"],
    created_at=pd["created_at"]
  )

@router.post("/", status_code=201)
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
    res = await addProduct(product=data)
    return {
      "message": "Product created successfully",
      "data": res
    }
  except Exception as e:
    logger.error("Failed to insert product")
    raise HTTPException(status_code=500, detail=f"Failed to insert product: {e}")

@router.get("/", status_code=200)
async def get_products(page: int = 1, per_page: int = 10):
  cache_key = f"products:page:{page}:per_page:{per_page}"
  try:
    cache_data = rd.get(cache_key)
    if cache_data is not None:
      logger.info("cache hit")
      products = [dict_to_product(d) for d in json.loads(cache_data)]
      return {
        "data": products
      }
    data = await getProducts(page=page, per_page=per_page)
    products_dict = [product_to_dict(p) for p in data]
    rd.setex(cache_key, 150, json.dumps(products_dict))
    return {
      "data": data
    }
  except Exception as e:
    logger.error(f"Failed to get product: {e}")
    raise HTTPException(status_code=500, detail=str(e))

@router.get("/{productId}", status_code=200)
async def get_product_by_id(productId: str):
  cache_key = f"product:{productId}"
  try:
    cache_data = rd.get(cache_key)
    if cache_data is not None:
      logger.info("cache hit")
      product = dict_to_product(json.loads(cache_data))
      return {
        "data": product
      }
    data = await getProductById(productId=productId)
  except Exception as e:
    logger.error(f"Failed to get product: {e}")
    raise HTTPException(status_code=500, detail=str(e))
  
  if data is not None:
    product_dict = product_to_dict(data)
    rd.setex(cache_key, 150, json.dumps(product_dict))
    return {
      "data": data
    }
  else:
    raise HTTPException(status_code=404, detail="Product Not Found")

@router.put("/{productId}", status_code=200)
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
    logger.error(f"Failed to update user: {e}")
    raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{productId}", status_code=200)
async def delete_user(productId: str):
  try:
    await deleteProduct(productId=productId)
    return {
      "message": "product deleted successfully"
    }
  except Exception as e:
    logger.error(f"Failed to delete user: {e}")
    raise HTTPException(status_code=500, detail=str(e))