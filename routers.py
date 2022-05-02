import traceback
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, UUID4

import schemas
from schemas import UserCreate
import utils

router = APIRouter(prefix="/users")


@router.post("/sign-up", response_model=schemas.SignUpModel)
async def create_user(user: schemas.UserCreate):
    db_user = await utils.get_user_by_email(email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await utils.create_user(user=user)


@router.post("/auth", response_model=schemas.TokenInformation)
async def auth(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await utils.get_user_by_email(email=form_data.username)

    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    if not utils.validate_password(
            password=form_data.password, hashed_password=user["hashed_password"]
    ):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    return await utils.create_user_token(user_id=user["id"])


@router.post("/update")
async def user_data_update(token: UUID4, new_data: schemas.UserUpdateModel):
    try:
        return await utils.user_data_update(token, new_data)
    except HTTPException as e:
        traceback.print_tb(e.__traceback__)
