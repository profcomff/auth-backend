from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, UUID4, Field, validator


class UserCreate(BaseModel):
    email: EmailStr = Field(..., alias="Email")
    first_name: str
    last_name: str
    patronymic: str
    password: str = Field(..., alias="Password")

    class Config:
        uselist = False


class UserInformation(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    patronymic: str


class TokenInformation(BaseModel):
    token: UUID4 = Field(..., alias="access_token")
    expires: datetime

    class Config:
        allow_population_by_field_name = True

    @validator("token")
    def hexlify_token(cls, value):
        return value.hex
