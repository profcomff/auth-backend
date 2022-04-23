from typing import List

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm

import schemas
from schemas import UserCreate
import utils

router = APIRouter(prefix="/users")


@router.post("/sign-up", response_model=UserCreate)
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
