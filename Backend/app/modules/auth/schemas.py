from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from app.shared.schemas import ORM

class Register(BaseModel): name: str = Field(min_length=2, max_length=120); email: EmailStr; password: str = Field(min_length=8, max_length=128)
class Login(BaseModel): email: EmailStr; password: str
class UserOut(ORM): id: int; name: str; email: EmailStr; created_at: datetime
class Token(BaseModel): access_token: str; token_type: str = "bearer"; user: UserOut
