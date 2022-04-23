from fastapi import FastAPI
import utils
import routers

app = FastAPI()


@app.get("/")
async def get():
    return await utils.generate_user_id()


app.include_router(routers.router)
