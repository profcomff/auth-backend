import hashlib
import random
import string
import uuid
from datetime import datetime, timedelta

import sqlalchemy.sql.functions
from pydantic import ValidationError
from sqlalchemy import and_, text

import schemas
from connect import engine

## from users import tokens_table, users_table
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
    result = engine.execute(query).fetchone()
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
    result = engine.execute(query)

    return {"result": user.dict(), "token": token}


async def user_data_update(token: str, new_data: dict):
    query = tokens_table.select().where(str(tokens_table.columns.token) == token)
    result = engine.execute(query).fetchone()
    if not result:
        raise Exception
    else:
        ## get_info_query = users_table.select().where(users_table.columns.id == result["user_id"])
        try:
            for row in new_data.keys():
                try:
                    update_query = users_table.update().values(row=new_data[row])
                    engine.execute(update_query)
                except Exception:
                    print("error")
        except ValidationError:
            print("non correct")
        return result


async def generate_user_id():
    query = users_table.select().order_by(users_table.columns.id)
    result = engine.execute(query).fetchall()
    if result:
        return result[-1]["id"] + 1
    else:
        return 1


async def generate_token_id():
    query = tokens_table.select().order_by(tokens_table.columns.id)
    result = engine.execute(query).fetchall()
    if result:
        return result[-1]["id"] + 1
    else:
        return 1
