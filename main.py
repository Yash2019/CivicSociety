import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.db.db import create_table
from backend.routers.routes import router

os.makedirs("backend/media", exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_table()
    yield

app = FastAPI(
    title="Societal Innovation Collaboration Portal",
    description="Backend API for citizen challenge submissions, auto-routing, project lifecycle, and industry partnerships.",
    lifespan=lifespan
)

# Enable CORS for all frontend origins (localhost, Live Server, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount media directory for previewing uploaded photos and deliverables
app.mount("/media", StaticFiles(directory="backend/media"), name="media")

app.include_router(router)