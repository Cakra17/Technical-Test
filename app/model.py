from pydantic import BaseModel, UUID7
from typing import Union
from datetime import datetime

class User(BaseModel):
  id: UUID7
  name: str
  email: str
  address: str
  created_at: Union[datetime, None]

class UserPayload(BaseModel):
  name: str
  email: str
  address: str