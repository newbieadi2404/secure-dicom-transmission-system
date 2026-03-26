from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserRegisterSchema(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=4)
    role: Optional[str] = "PATIENT"

class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str
