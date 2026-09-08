from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.db.db import create_table
from backend.routers.routes import router

MEDIA_DIR = Path(__file__).resolve().parent / "backend" / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

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

# This API does not use cookie authentication, so credentials must remain off
# when allowing development origins broadly.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount media directory for previewing uploaded photos and deliverables
app.mount("/media", StaticFiles(directory=str(MEDIA_DIR)), name="media")

from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.exc import IntegrityError

@app.exception_handler(IntegrityError)
async def integrity_exception_handler(request, exc: IntegrityError):
    return JSONResponse(
        status_code=400,
        content={"detail": "Database constraint error. Check referenced IDs and duplicate values."}
    )

app.include_router(router)

FRONTEND_DIST = Path(__file__).resolve().parent / "frontend" / "dist"
if (FRONTEND_DIST / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="frontend_assets")

@app.get("/{full_path:path}", include_in_schema=False)
async def serve_frontend_spa(full_path: str):
    file_path = FRONTEND_DIST / full_path
    if file_path.is_file():
        return FileResponse(file_path)
    index_file = FRONTEND_DIST / "index.html"
    if index_file.is_file():
        return FileResponse(index_file)
    return JSONResponse(status_code=404, content={"detail": "Not found"})
