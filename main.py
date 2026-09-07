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

tags_metadata = [
    {
        "name": "1. Users",
        "description": "Create and manage users (Citizens, Students, Faculty, Admins). **Fill this first** to get user IDs.",
    },
    {
        "name": "2. Institutions",
        "description": "Create academic institutions and industry organizations (universities, CSR, research labs, startups).",
    },
    {
        "name": "3. Problems & Challenges",
        "description": "Citizen problem submissions with AI auto-classification, deduplication, and geo-location.",
    },
    {
        "name": "4. Institution Routing",
        "description": "Review and accept or decline societal problems routed to matching institutions.",
    },
    {
        "name": "5. Teams",
        "description": "Form multidisciplinary teams and assign faculty mentors to solve accepted challenges.",
    },
    {
        "name": "6. Projects",
        "description": "Create project proposals, track project stages, and manage administrative approvals.",
    },
    {
        "name": "7. Milestones & Deliverables",
        "description": "Define project milestones, update completion status, and upload deliverable documents.",
    },
    {
        "name": "8. Industry Partnerships",
        "description": "Connect industry partners for funding, mentorship, prototyping, or technology transfer.",
    },
    {
        "name": "9. Outcomes & IP",
        "description": "Record patents filed, startups created, and intellectual property generated.",
    },
    {
        "name": "10. Messages & Discussion",
        "description": "Project-level communication threads between citizens, teams, faculty, and industry.",
    },
    {
        "name": "11. Dashboard & Analytics",
        "description": "Aggregated statistical insights across categories, districts, stages, and outcomes.",
    },
]

app = FastAPI(
    title="Societal Innovation Collaboration Portal",
    description="Backend API for citizen challenge submissions, auto-routing, project lifecycle, and industry partnerships.",
    openapi_tags=tags_metadata,
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

from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

@app.exception_handler(IntegrityError)
async def integrity_exception_handler(request, exc: IntegrityError):
    detail = str(exc.orig) if hasattr(exc, "orig") else str(exc)
    return JSONResponse(
        status_code=400,
        content={"detail": f"Database constraint error (check IDs provided): {detail}"}
    )

app.include_router(router)