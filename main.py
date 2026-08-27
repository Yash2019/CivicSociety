from backend.db.db import create_table
from fastapi import FastAPI
from backend.routers.routes import router
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_table()
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(router)