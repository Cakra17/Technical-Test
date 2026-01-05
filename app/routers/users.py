from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from app.model import User, UserPayload
from app.services.users import addUser, updateUser, deleteUser, getUserById
import logging
import uuid

router = APIRouter(
  prefix="/api/v1/users",
  tags=["users"]
)

@router.post("/")
async def add_user(payload: UserPayload):
  try:
    userId = uuid.uuid7()
    data = User(
      id=userId,
      name=payload.name,
      email=payload.email,
      address=payload.address,
      created_at=None
    )
    await addUser(user=data) 
    return {
      "message": "User created successfully"
    }
  except Exception as e:
    logging.error(f"Failed to insert user: {e}")
    raise HTTPException(status_code=500, detail=str(e))


@router.get("/{userId}")
async def get_user_by_id(userId: str):
  try:
    data = await getUserById(userId=userId)
    if data:
      return {
        "data": data
      }
    else:
      raise HTTPException(status_code=404, detail="User Not Found")
  except Exception as e:
    logging.error(f"Failed to get user: {e}")
    raise HTTPException(status_code=500, detail=str(e))

@router.put("/{userId}")
async def update_user(userId: str, payload: UserPayload):
  try:
    data = User(
      id=userId,
      name=payload.name,
      email=payload.email,
      address=payload.address,
      created_at=None
    )
    await updateUser(user=data)
    return {
      "message": "User updated successfully"
    }
  except Exception as e:
    logging.error(f"Failed to update user: {e}")
    raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{userId}")
async def delete_user(userId: str):
  try:
    await deleteUser(userId=userId)
    return {
      "message": "user deleted successfully"
    }
  except Exception as e:
    logging.error(f"Failed to delete user: {e}")
    raise HTTPException(status_code=500, detail=str(e))