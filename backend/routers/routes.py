from fastapi import APIRouter, Depends, UploadFile, Form, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.db.db import get_db
from backend.enums import (
    SubmitterType,
    InstitutionDomain,
    InstitutionType,
    RoutingStatus,
)
from backend.Models.projects_db import Projects
from backend.Models.institutions import Institutions
from backend.Models.problems_db import Problems
from backend.schemas.schema import (
    ProblemSchemaInput,
    ProblemSchemaOutput,
    RoutedProblemResponse,
    InstitutionResponse,
    Institution,
    TeamCreate,
    TeamResponse,
    ProjectCreate,
    ProjectResponse,
    ProjectStageUpdate,
    ProjectApprovalUpdate,
    MilestoneCreate,
    MilestoneResponse,
    MilestoneStatusUpdate,
    OutcomeUpsert,
    OutcomeResponse,
    PartnershipCreate,
    PartnershipResponse,
    PartnershipStatusUpdate,
    DeliverableResponse,
    MessageCreate,
    MessageResponse,
    DashboardStats,
    UserCreate,
    UserResponse,
)
from backend.services.classification import (
    inputProblems,
    getProblems,
    createYourInstitution,
    getProblemsForInstitution,
    update_routing_status,
    create_team,
    get_team,
    list_teams,
    create_project,
    update_project_stage,
    approve_project,
    add_milestone,
    get_project_milestones,
    update_milestone_status,
    upsert_project_outcomes,
    get_project_outcomes,
    add_deliverable,
    get_project_deliverables,
    request_partnership,
    update_partnership_status,
    get_project_partnerships,
    get_institution_partnerships,
    add_project_message,
    get_project_messages,
    get_dashboard_summary,
    create_user,
    get_user,
    list_users,
)

router = APIRouter()


# --- PROBLEM SUBMISSION ENDPOINTS ---
@router.post('/PostProblems', response_model=ProblemSchemaOutput)
@router.post('/problems', response_model=ProblemSchemaOutput)
async def Problems_endpoint(
    title: str = Form(...),
    description: str = Form(...),
    submitter_type: SubmitterType = Form(...),
    district: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    submitted_by: int | None = Form(None),
    photo: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
):
    data = ProblemSchemaInput(
        title=title,
        description=description,
        submitter_type=submitter_type,
        district=district,
        latitude=latitude,
        longitude=longitude,
        submitted_by=submitted_by,
    )
    return await inputProblems(data, photo, db)


@router.get('/problems', response_model=list[ProblemSchemaOutput])
async def list_problems_endpoint(db: AsyncSession = Depends(get_db)):
    stmt = select(Problems).order_by(Problems.created_at.desc())
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get('/get_problem/{user_id}', response_model=list[ProblemSchemaOutput])
@router.get('/problems/user/{user_id}', response_model=list[ProblemSchemaOutput])
async def get_problem_endpoint(user_id: int, db: AsyncSession = Depends(get_db)):
    return await getProblems(user_id, db)


@router.get('/problems/{id}', response_model=ProblemSchemaOutput)
async def get_problem_by_id_endpoint(id: int, db: AsyncSession = Depends(get_db)):
    problem = await db.get(Problems, id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    return problem


# --- INSTITUTION ENDPOINTS ---
@router.post('/institutions', response_model=InstitutionResponse)
async def create_institution_json_endpoint(data: Institution, db: AsyncSession = Depends(get_db)):
    return await createYourInstitution(data, db)


@router.post('/create_institution', response_model=InstitutionResponse)
@router.post('/create_instituion', response_model=InstitutionResponse)
async def create_institution_endpoint(
    name: str = Form(...),
    type: InstitutionType = Form(...),
    domain: InstitutionDomain | None = Form(None),
    domains: str | None = Form(None),
    district: str = Form(...),
    has_incubation: bool = Form(...),
    db: AsyncSession = Depends(get_db),
):
    parsed_domains = []
    if domains:
        parsed_domains = [d.strip() for d in domains.split(",") if d.strip()]
    elif domain:
        parsed_domains = [domain.value]

    data = Institution(
        name=name,
        type=type,
        domain=domain,
        domains=parsed_domains,
        district=district,
        has_incubation=has_incubation,
    )
    return await createYourInstitution(data, db)


@router.get('/institutions', response_model=list[InstitutionResponse])
async def list_institutions_endpoint(db: AsyncSession = Depends(get_db)):
    stmt = select(Institutions).order_by(Institutions.id.asc())
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get('/institutions/{id}', response_model=InstitutionResponse)
async def get_institution_by_id_endpoint(id: int, db: AsyncSession = Depends(get_db)):
    institution = await db.get(Institutions, id)
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")
    return institution


@router.get('/institutions/{id}/problems', response_model=list[RoutedProblemResponse])
async def route_institute_endpoint(id: int, db: AsyncSession = Depends(get_db)):
    return await getProblemsForInstitution(id, db)


# --- ROUTING ENDPOINTS ---
@router.post('/routings/{id}/accept')
async def accept_routing_endpoint(id: int, db: AsyncSession = Depends(get_db)):
    return await update_routing_status(id, RoutingStatus.accepted, db)


@router.post('/routings/{id}/decline')
async def decline_routing_endpoint(id: int, db: AsyncSession = Depends(get_db)):
    return await update_routing_status(id, RoutingStatus.declined, db)


# --- TEAM ENDPOINTS ---
@router.post('/teams', response_model=TeamResponse)
async def create_team_endpoint(data: TeamCreate, db: AsyncSession = Depends(get_db)):
    return await create_team(data, db)


@router.get('/teams', response_model=list[TeamResponse])
async def list_teams_endpoint(db: AsyncSession = Depends(get_db)):
    return await list_teams(db)


@router.get('/teams/{id}', response_model=TeamResponse)
async def get_team_endpoint(id: int, db: AsyncSession = Depends(get_db)):
    return await get_team(id, db)


# --- PROJECT ENDPOINTS ---
@router.post('/projects', response_model=ProjectResponse)
async def create_project_endpoint(data: ProjectCreate, db: AsyncSession = Depends(get_db)):
    return await create_project(data, db)


@router.get('/projects', response_model=list[ProjectResponse])
async def list_projects_endpoint(db: AsyncSession = Depends(get_db)):
    stmt = select(Projects).order_by(Projects.created_at.desc())
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get('/projects/{id}', response_model=ProjectResponse)
async def get_project_endpoint(id: int, db: AsyncSession = Depends(get_db)):
    project = await db.get(Projects, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch('/projects/{id}/stage', response_model=ProjectResponse)
async def update_project_stage_endpoint(id: int, data: ProjectStageUpdate, db: AsyncSession = Depends(get_db)):
    return await update_project_stage(id, data.stage, db)


@router.patch('/projects/{id}/approve', response_model=ProjectResponse)
async def approve_project_endpoint(id: int, data: ProjectApprovalUpdate, db: AsyncSession = Depends(get_db)):
    return await approve_project(id, data.approval_status, data.approved_by_user_id, db)


# --- MILESTONE ENDPOINTS ---
@router.post('/projects/{id}/milestones', response_model=MilestoneResponse)
async def add_milestone_endpoint(id: int, data: MilestoneCreate, db: AsyncSession = Depends(get_db)):
    return await add_milestone(id, data, db)


@router.get('/projects/{id}/milestones', response_model=list[MilestoneResponse])
async def get_project_milestones_endpoint(id: int, db: AsyncSession = Depends(get_db)):
    return await get_project_milestones(id, db)


@router.patch('/milestones/{id}/status', response_model=MilestoneResponse)
async def update_milestone_status_endpoint(id: int, data: MilestoneStatusUpdate, db: AsyncSession = Depends(get_db)):
    return await update_milestone_status(id, data.status, db)


# --- DELIVERABLES ENDPOINTS ---
@router.post('/projects/{id}/deliverables', response_model=DeliverableResponse)
async def upload_deliverable_endpoint(
    id: int,
    doc_type: str = Form(...),
    milestone_id: int | None = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    return await add_deliverable(id, milestone_id, doc_type, file, db)


@router.get('/projects/{id}/deliverables', response_model=list[DeliverableResponse])
async def get_project_deliverables_endpoint(id: int, db: AsyncSession = Depends(get_db)):
    return await get_project_deliverables(id, db)


# --- OUTCOMES ENDPOINTS ---
@router.post('/projects/{id}/outcomes', response_model=OutcomeResponse)
async def record_outcomes_endpoint(id: int, data: OutcomeUpsert, db: AsyncSession = Depends(get_db)):
    return await upsert_project_outcomes(id, data, db)


@router.get('/projects/{id}/outcomes', response_model=OutcomeResponse)
async def get_outcomes_endpoint(id: int, db: AsyncSession = Depends(get_db)):
    return await get_project_outcomes(id, db)


# --- INDUSTRY PARTNERSHIPS ENDPOINTS ---
@router.post('/projects/{id}/partnerships', response_model=PartnershipResponse)
async def request_partnership_endpoint(id: int, data: PartnershipCreate, db: AsyncSession = Depends(get_db)):
    return await request_partnership(id, data, db)


@router.patch('/partnerships/{id}/status', response_model=PartnershipResponse)
async def update_partnership_status_endpoint(id: int, data: PartnershipStatusUpdate, db: AsyncSession = Depends(get_db)):
    return await update_partnership_status(id, data.status, db)


@router.get('/projects/{id}/partnerships', response_model=list[PartnershipResponse])
async def get_project_partnerships_endpoint(id: int, db: AsyncSession = Depends(get_db)):
    return await get_project_partnerships(id, db)


@router.get('/institutions/{id}/partnerships', response_model=list[PartnershipResponse])
async def get_institution_partnerships_endpoint(id: int, db: AsyncSession = Depends(get_db)):
    return await get_institution_partnerships(id, db)


# --- PROJECT MESSAGES / DISCUSSION ENDPOINTS ---
@router.post('/projects/{id}/messages', response_model=MessageResponse)
async def post_project_message_endpoint(id: int, data: MessageCreate, db: AsyncSession = Depends(get_db)):
    return await add_project_message(id, data, db)


@router.get('/projects/{id}/messages', response_model=list[MessageResponse])
async def get_project_messages_endpoint(id: int, db: AsyncSession = Depends(get_db)):
    return await get_project_messages(id, db)


# --- DASHBOARD ENDPOINT ---
@router.get('/dashboard', response_model=DashboardStats)
async def get_dashboard_endpoint(db: AsyncSession = Depends(get_db)):
    return await get_dashboard_summary(db)


# --- USER ENDPOINTS ---
@router.post('/users', response_model=UserResponse)
async def create_user_endpoint(data: UserCreate, db: AsyncSession = Depends(get_db)):
    return await create_user(data, db)


@router.get('/users', response_model=list[UserResponse])
async def list_users_endpoint(db: AsyncSession = Depends(get_db)):
    return await list_users(db)


@router.get('/users/{id}', response_model=UserResponse)
async def get_user_endpoint(id: int, db: AsyncSession = Depends(get_db)):
    return await get_user(id, db)