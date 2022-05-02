import hashlib
import random
import string
import uuid
from datetime import datetime, timedelta

from fastapi import HTTPException
from pydantic import ValidationError, UUID4
from sqlalchemy import and_, text

import schemas
from connect import engine

from connect import users_table, tokens_table


def get_random_string(length=12):
    return "".join(random.choice(string.ascii_letters) for _ in range(length))


def hash_password(password: str, salt: str = None):
    if salt is None:
        salt = get_random_string()
    enc = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return enc.hex()


def validate_password(password: str, hashed_password: str):
    salt, hashed = hashed_password.split("$")
    return hash_password(password, salt) == hashed


async def get_user_by_email(email: str):
    query = users_table.select().where(users_table.c.email == email)
    result = engine.execute(query).fetchone()
    return result


async def get_user_by_token(token: str):
    query = tokens_table.join(users_table).select().where(
        and_(
            tokens_table.c.token == token,
            tokens_table.c.expires > datetime.now()
        )
    )
    result = engine.execute(query).fetchone()
    return await result


async def create_user_token(user_id: int):
    token_id = await generate_token_id()
    token = uuid.uuid4()
    expires = datetime.now() + timedelta(weeks=2)
    query = (
        tokens_table.insert()
            .values(expires=expires, user_id=user_id, id=token_id, token=token)
            .returning(tokens_table.c.token, tokens_table.c.expires)
    )
    engine.execute(query).fetchone()
    return {"token": token, "expires": expires}


async def create_user(user: schemas.UserCreate):
    salt = get_random_string()
    hashed_password = hash_password(user.password, salt)
    user_id = await generate_user_id()
    token = await create_user_token(user_id)
    query = users_table.insert().values(
        email=user.email, first_name=user.first_name, hashed_password=f"{salt}${hashed_password}",
        last_name=user.last_name, patronymic=user.patronymic, id=user_id, is_active=True
    ).returning(users_table.columns.is_active)
    engine.execute(query)
    tokeninfo = schemas.TokenInformation(**token)

    return {"result": user.dict(), "token": tokeninfo}


async def user_data_update(token: UUID4, new_data: schemas.UserUpdateModel):
    if check_token(token):
        user_id = engine.execute(tokens_table.select().where(token.__str__() == tokens_table.columns.token)).fetchone()["user_id"]
        if new_data.first_name is not None and new_data.first_name is not "":
            engine.execute(
                users_table.update().where(users_table.columns.id == user_id).values(first_name=new_data.first_name))
        if new_data.last_name is not None and new_data.last_name is not "":
            engine.execute(
                users_table.update().where(users_table.columns.id == user_id).values(last_name=new_data.last_name))
        if new_data.patronymic is not None and new_data.patronymic is not "":
            engine.execute(
                users_table.update().where(users_table.columns.id == user_id).values(patronymic=new_data.patronymic))


async def generate_user_id() -> int:
    query = users_table.select().order_by(users_table.columns.id)
    result = engine.execute(query).fetchall()
    if result:
        return result[-1]["id"] + 1
    else:
        return 1


async def generate_token_id() -> int:
    query = tokens_table.select().order_by(tokens_table.columns.id)
    result = engine.execute(query).fetchall()
    if result:
        return result[-1]["id"] + 1
    else:
        return 1


def check_token(token: UUID4) -> bool:
    query = tokens_table.select().where(
        token.__str__() == tokens_table.columns.token)
    result = engine.execute(query).fetchone()
    if result and datetime.strptime(str(result["expires"]), '%Y-%m-%d') >= datetime.today():
        return True
    else:
        raise HTTPException(status_code=403)

