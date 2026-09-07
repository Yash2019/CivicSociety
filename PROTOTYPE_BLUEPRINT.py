"""
PROTOTYPE IMPLEMENTATION BLUEPRINT & BUG FIX GUIDE
===================================================
Target: Societal Innovation Collaboration Portal (SIH Prototype)
Scope: Complete Prototype Backend (excluding Auth, Notifications/Chat, and Frontend)

Instructions for You:
---------------------
You can read this file section by section and type/integrate it into your own codebase.
No files in your existing backend have been modified. 

TABLE OF CONTENTS:
------------------
PART 1: BUG FIXES FOR EXISTING CODE (What to fix in your current files)
PART 2: NEW ENUMS (to add to backend/enums.py)
PART 3: NEW & FIXED MODELS (to update backend/Models/)
PART 4: NEW PYDANTIC SCHEMAS (to add to backend/schemas/schema.py)
PART 5: NEW SERVICES & LOGIC (to add to backend/services/)
        - 5.1 Priority Score Calculator
        - 5.2 Routing Actions (Accept / Decline)
        - 5.3 Teams & Project Lifecycle
        - 5.4 Milestones, Deliverables & Outcomes
        - 5.5 Industry Partnerships
        - 5.6 Analytics Dashboard Aggregator
PART 6: NEW FASTAPI ROUTER ENDPOINTS (to add to backend/routers/routes.py)
"""

# ==============================================================================
# PART 1: BUG FIXES FOR EXISTING FILES
# ==============================================================================

"""
BUG FIX 1: `backend/Models/teams_db.py`
---------------------------------------
ISSUE:
  `Team_member` lacked `__tablename__` and `primary_key=True` on mapped columns.
  SQLAlchemy DeclarativeBase throws an error as soon as this class is imported.

FIX IN `backend/Models/teams_db.py`:
Replace class `Team_member` with:

class TeamMember(Base):
    __tablename__ = 'team_members'

    team_id: Mapped[int] = mapped_column(
        ForeignKey('teams.id'),
        primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id'),
        primary_key=True
    )
"""

"""
BUG FIX 2: `backend/routers/routes.py` - User Problems Endpoint
--------------------------------------------------------------
ISSUE:
  1. Route was `@router.get('/get_problem{user_id}')` - missing `/`
  2. Service filtered `Problems.id == user_id` instead of `Problems.submitted_by == user_id`
  3. It only returned one problem instead of a list of problems submitted by that user.

FIX IN `backend/services/classification.py`:
async def getProblemsByUser(user_id: int, db: AsyncSession):
    stmt = select(Problems).where(Problems.submitted_by == user_id)
    result = await db.execute(stmt)
    return result.scalars().all()

FIX IN `backend/routers/routes.py`:
@router.get('/problems/user/{user_id}', response_model=list[ProblemSchemaOutput])
async def get_user_problems_endpoint(user_id: int, db: AsyncSession = Depends(get_db)):
    return await getProblemsByUser(user_id, db)
"""

"""
BUG FIX 3: `backend/routers/routes.py` - Institute Problems Response Model
------------------------------------------------------------------------
ISSUE:
  `@router.get('/institutions/{id}/problems', response_model=list[ProblemSchemaInput])`
  Using `ProblemSchemaInput` drops the problem `id`, `category`, and `status` from the response.

FIX:
Change `response_model=list[ProblemSchemaInput]` to `response_model=list[ProblemSchemaOutput]`.
"""

"""
BUG FIX 4: `backend/services/classification.py` - Commit inside loop
--------------------------------------------------------------------
ISSUE:
  In `routeProblemtoInstitute()`, `await db.commit()` was inside the `for inst in institutions:` loop.

FIX:
Move `await db.commit()` OUTSIDE the loop so all routings commit in a single transaction.
"""


# ==============================================================================
# PART 2: NEW ENUMS (Add to `backend/enums.py`)
# ==============================================================================

from enum import Enum

class ProjectStage(str, Enum):
    proposed = "proposed"
    active = "active"
    testing = "testing"
    deployed = "deployed"
    completed = "completed"

class ApprovalStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class MilestoneStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"

class PartnershipType(str, Enum):
    mentorship = "mentorship"
    funding = "funding"
    prototyping = "prototyping"
    technology_transfer = "technology_transfer"

class PartnershipStatus(str, Enum):
    requested = "requested"
    accepted = "accepted"
    declined = "declined"


# ==============================================================================
# PART 3: NEW & COMPLETED MODELS (Add to `backend/Models/`)
# ==============================================================================

from datetime import datetime, date
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy import ForeignKey, DateTime, Date, func, String, Text, Integer, Boolean
from sqlalchemy import Enum as SQLEnum

# Base can be imported from your backend.db.db
# from backend.db.db import Base

class Base(DeclarativeBase):
    pass

# --- 3.1 Basic Users Model (Lightweight for prototype without full Auth) ---
class Users(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="citizen") # citizen, student, faculty, industry, gov_admin
    institution_id: Mapped[int | None] = mapped_column(ForeignKey("institutions.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# --- 3.2 Projects Model ---
class Projects(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    proposal_text: Mapped[str] = mapped_column(Text, nullable=False)

    stage: Mapped[ProjectStage] = mapped_column(
        SQLEnum(ProjectStage),
        default=ProjectStage.proposed,
        nullable=False
    )
    approval_status: Mapped[ApprovalStatus] = mapped_column(
        SQLEnum(ApprovalStatus),
        default=ApprovalStatus.pending,
        nullable=False
    )
    approved_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# --- 3.3 Milestones Model ---
class Milestones(Base):
    __tablename__ = "milestones"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[MilestoneStatus] = mapped_column(
        SQLEnum(MilestoneStatus),
        default=MilestoneStatus.pending,
        nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# --- 3.4 Deliverables Model ---
class Deliverables(Base):
    __tablename__ = "deliverables"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    milestone_id: Mapped[int | None] = mapped_column(ForeignKey("milestones.id"), nullable=True)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    doc_type: Mapped[str] = mapped_column(String(50), nullable=False) # e.g., 'cad_model', 'source_code', 'test_report'
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# --- 3.5 Project Outcomes Model (Patents, Startups, IP) ---
class ProjectOutcomes(Base):
    __tablename__ = "project_outcomes"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), unique=True, nullable=False)
    patents_filed: Mapped[int] = mapped_column(Integer, default=0)
    startups_created: Mapped[int] = mapped_column(Integer, default=0)
    ip_generated: Mapped[str | None] = mapped_column(Text, nullable=True)
    impact_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# --- 3.6 Industry Partnerships Model ---
class IndustryPartnerships(Base):
    __tablename__ = "industry_partnerships"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    industry_institution_id: Mapped[int] = mapped_column(ForeignKey("institutions.id"), nullable=False)
    partnership_type: Mapped[PartnershipType] = mapped_column(
        SQLEnum(PartnershipType),
        nullable=False
    )
    status: Mapped[PartnershipStatus] = mapped_column(
        SQLEnum(PartnershipStatus),
        default=PartnershipStatus.requested,
        nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ==============================================================================
# PART 4: PYDANTIC SCHEMAS (Add to `backend/schemas/schema.py`)
# ==============================================================================

from pydantic import BaseModel, ConfigDict

# --- Team Schemas ---
class TeamCreate(BaseModel):
    problem_id: int
    institution_id: int
    faculty_mentor_id: int
    member_user_ids: list[int] = []

class TeamResponse(BaseModel):
    id: int
    problem_id: int
    institution_id: int
    faculty_mentor_id: int
    member_user_ids: list[int] = []
    model_config = ConfigDict(from_attributes=True)

# --- Project Schemas ---
class ProjectCreate(BaseModel):
    team_id: int
    problem_id: int
    title: str
    proposal_text: str

class ProjectStageUpdate(BaseModel):
    stage: ProjectStage

class ProjectApprovalUpdate(BaseModel):
    approval_status: ApprovalStatus
    approved_by_user_id: int

class ProjectResponse(BaseModel):
    id: int
    team_id: int
    problem_id: int
    title: str
    proposal_text: str
    stage: ProjectStage
    approval_status: ApprovalStatus
    approved_by_user_id: int | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Milestone Schemas ---
class MilestoneCreate(BaseModel):
    title: str
    description: str | None = None
    due_date: date | None = None

class MilestoneStatusUpdate(BaseModel):
    status: MilestoneStatus

class MilestoneResponse(BaseModel):
    id: int
    project_id: int
    title: str
    description: str | None
    due_date: date | None
    status: MilestoneStatus
    completed_at: datetime | None
    model_config = ConfigDict(from_attributes=True)

# --- Outcomes Schemas ---
class OutcomeUpsert(BaseModel):
    patents_filed: int = 0
    startups_created: int = 0
    ip_generated: str | None = None
    impact_notes: str | None = None

class OutcomeResponse(OutcomeUpsert):
    id: int
    project_id: int
    model_config = ConfigDict(from_attributes=True)

# --- Industry Partnership Schemas ---
class PartnershipCreate(BaseModel):
    industry_institution_id: int
    partnership_type: PartnershipType
    notes: str | None = None

class PartnershipStatusUpdate(BaseModel):
    status: PartnershipStatus

class PartnershipResponse(BaseModel):
    id: int
    project_id: int
    industry_institution_id: int
    partnership_type: PartnershipType
    status: PartnershipStatus
    notes: str | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Dashboard Summary Schema ---
class DashboardStats(BaseModel):
    total_problems: int
    problems_by_status: dict[str, int]
    problems_by_category: dict[str, int]
    problems_by_district: dict[str, int]
    total_projects: int
    projects_by_stage: dict[str, int]
    total_patents: int
    total_startups: int
    active_industry_partnerships: int


# ==============================================================================
# PART 5: SERVICES LOGIC (Add to `backend/services/`)
# ==============================================================================

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from fastapi import HTTPException

# ------------------------------------------------------------------------------
# 5.1 Priority Score Calculator
# ------------------------------------------------------------------------------
# In plan.md: priority_score computed from submitter type weight + urgency rule.
# PRIs, ULBs, and Govt Depts represent larger populations, so they get higher base weights.
SUBMITTER_WEIGHTS = {
    "govt_dept": 90,
    "ulb": 85,
    "pri": 80,
    "community_org": 65,
    "individual": 40
}

def compute_priority_score(submitter_type_value: str, has_media: bool = True) -> int:
    base = SUBMITTER_WEIGHTS.get(submitter_type_value, 40)
    # Extra points for visual evidence validation
    evidence_bonus = 10 if has_media else 0
    return min(base + evidence_bonus, 100)


# ------------------------------------------------------------------------------
# 5.2 Routing Actions (Accept / Decline)
# ------------------------------------------------------------------------------
# from backend.Models.institutions import Routings
# from backend.enums import RoutingStatus

async def update_routing_status(routing_id: int, new_status: str, db: AsyncSession):
    # routing = await db.get(Routings, routing_id)
    # if not routing:
    #     raise HTTPException(status_code=404, detail="Routing record not found")
    # routing.status = new_status
    # await db.commit()
    # await db.refresh(routing)
    # return routing
    pass


# ------------------------------------------------------------------------------
# 5.3 Teams & Project Lifecycle Services
# ------------------------------------------------------------------------------
async def create_team(data: TeamCreate, db: AsyncSession):
    """
    Creates a multidisciplinary team and maps the student members.
    """
    # 1. Create team record
    new_team = Teams(
        problem_id=data.problem_id,
        institution_id=data.institution_id,
        faculty_mentor_id=data.faculty_mentor_id
    )
    db.add(new_team)
    await db.flush() # get new_team.id

    # 2. Add team members
    for user_id in data.member_user_ids:
        member = TeamMember(team_id=new_team.id, user_id=user_id)
        db.add(member)

    await db.commit()
    await db.refresh(new_team)
    return {
        "id": new_team.id,
        "problem_id": new_team.problem_id,
        "institution_id": new_team.institution_id,
        "faculty_mentor_id": new_team.faculty_mentor_id,
        "member_user_ids": data.member_user_ids
    }

async def create_project(data: ProjectCreate, db: AsyncSession):
    """
    Creates a solution proposal for a team solving a specific problem.
    """
    project = Projects(
        team_id=data.team_id,
        problem_id=data.problem_id,
        title=data.title,
        proposal_text=data.proposal_text,
        stage=ProjectStage.proposed,
        approval_status=ApprovalStatus.pending
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project

async def update_project_stage(project_id: int, new_stage: ProjectStage, db: AsyncSession):
    project = await db.get(Projects, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project.stage = new_stage
    await db.commit()
    await db.refresh(project)
    return project

async def approve_project(project_id: int, approval_status: ApprovalStatus, admin_id: int, db: AsyncSession):
    project = await db.get(Projects, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project.approval_status = approval_status
    project.approved_by_user_id = admin_id
    if approval_status == ApprovalStatus.approved and project.stage == ProjectStage.proposed:
        project.stage = ProjectStage.active
    await db.commit()
    await db.refresh(project)
    return project


# ------------------------------------------------------------------------------
# 5.4 Milestones & Outcomes Services
# ------------------------------------------------------------------------------
async def add_milestone(project_id: int, data: MilestoneCreate, db: AsyncSession):
    milestone = Milestones(
        project_id=project_id,
        title=data.title,
        description=data.description,
        due_date=data.due_date,
        status=MilestoneStatus.pending
    )
    db.add(milestone)
    await db.commit()
    await db.refresh(milestone)
    return milestone

async def update_milestone_status(milestone_id: int, status: MilestoneStatus, db: AsyncSession):
    milestone = await db.get(Milestones, milestone_id)
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    milestone.status = status
    if status == MilestoneStatus.completed:
        milestone.completed_at = datetime.utcnow()
    await db.commit()
    await db.refresh(milestone)
    return milestone

async def upsert_project_outcomes(project_id: int, data: OutcomeUpsert, db: AsyncSession):
    stmt = select(ProjectOutcomes).where(ProjectOutcomes.project_id == project_id)
    result = await db.execute(stmt)
    outcome = result.scalar_one_or_none()

    if not outcome:
        outcome = ProjectOutcomes(
            project_id=project_id,
            patents_filed=data.patents_filed,
            startups_created=data.startups_created,
            ip_generated=data.ip_generated,
            impact_notes=data.impact_notes
        )
        db.add(outcome)
    else:
        outcome.patents_filed = data.patents_filed
        outcome.startups_created = data.startups_created
        outcome.ip_generated = data.ip_generated
        outcome.impact_notes = data.impact_notes

    await db.commit()
    await db.refresh(outcome)
    return outcome


# ------------------------------------------------------------------------------
# 5.5 Industry Partnerships Services
# ------------------------------------------------------------------------------
async def request_partnership(project_id: int, data: PartnershipCreate, db: AsyncSession):
    partnership = IndustryPartnerships(
        project_id=project_id,
        industry_institution_id=data.industry_institution_id,
        partnership_type=data.partnership_type,
        notes=data.notes,
        status=PartnershipStatus.requested
    )
    db.add(partnership)
    await db.commit()
    await db.refresh(partnership)
    return partnership

async def update_partnership_status(partnership_id: int, status: PartnershipStatus, db: AsyncSession):
    partnership = await db.get(IndustryPartnerships, partnership_id)
    if not partnership:
        raise HTTPException(status_code=404, detail="Partnership request not found")
    partnership.status = status
    await db.commit()
    await db.refresh(partnership)
    return partnership


# ------------------------------------------------------------------------------
# 5.6 Analytics Dashboard Aggregation
# ------------------------------------------------------------------------------
async def get_dashboard_summary(db: AsyncSession):
    """
    Executes fast aggregate queries for the judge/government dashboard:
    - Problem breakdown by status, category, district
    - Project stage breakdown
    - Quantified impacts (patents, startups, partnerships)
    """
    # 1. Total Problems
    # problems_total = await db.scalar(select(func.count(Problems.id))) or 0
    # 2. Problems grouped by status
    # status_q = await db.execute(select(Problems.status, func.count(Problems.id)).group_by(Problems.status))
    # problems_by_status = {str(k.value if hasattr(k, 'value') else k): count for k, count in status_q.all()}
    
    # 3. Problems grouped by category
    # cat_q = await db.execute(select(Problems.category, func.count(Problems.id)).group_by(Problems.category))
    # problems_by_cat = {str(k.value if hasattr(k, 'value') else k): count for k, count in cat_q.all() if k}

    # 4. Total patents and startups from outcomes
    total_patents = await db.scalar(select(func.coalesce(func.sum(ProjectOutcomes.patents_filed), 0))) or 0
    total_startups = await db.scalar(select(func.coalesce(func.sum(ProjectOutcomes.startups_created), 0))) or 0

    # 5. Active partnerships
    active_partnerships = await db.scalar(
        select(func.count(IndustryPartnerships.id))
        .where(IndustryPartnerships.status == PartnershipStatus.accepted)
    ) or 0

    return {
        "total_problems": 0, # replace with problems_total
        "problems_by_status": {}, # replace with problems_by_status
        "problems_by_category": {}, # replace with problems_by_cat
        "problems_by_district": {},
        "total_projects": 0,
        "projects_by_stage": {},
        "total_patents": total_patents,
        "total_startups": total_startups,
        "active_industry_partnerships": active_partnerships
    }


# ==============================================================================
# PART 6: PROTOTYPE ROUTER ENDPOINTS (Add to `backend/routers/routes.py`)
# ==============================================================================

from fastapi import APIRouter, Depends

# router = APIRouter()

"""
# --- ROUTING ENDPOINTS ---
@router.post('/routings/{id}/accept')
async def accept_routing_endpoint(id: int, db: AsyncSession = Depends(get_db)):
    return await update_routing_status(id, "accepted", db)

@router.post('/routings/{id}/decline')
async def decline_routing_endpoint(id: int, db: AsyncSession = Depends(get_db)):
    return await update_routing_status(id, "declined", db)

# --- TEAM ENDPOINTS ---
@router.post('/teams', response_model=TeamResponse)
async def create_team_endpoint(data: TeamCreate, db: AsyncSession = Depends(get_db)):
    return await create_team(data, db)

# --- PROJECT ENDPOINTS ---
@router.post('/projects', response_model=ProjectResponse)
async def create_project_endpoint(data: ProjectCreate, db: AsyncSession = Depends(get_db)):
    return await create_project(data, db)

@router.get('/projects', response_model=list[ProjectResponse])
async def list_projects_endpoint(db: AsyncSession = Depends(get_db)):
    stmt = select(Projects)
    res = await db.execute(stmt)
    return res.scalars().all()

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

@router.patch('/milestones/{id}/status', response_model=MilestoneResponse)
async def update_milestone_status_endpoint(id: int, data: MilestoneStatusUpdate, db: AsyncSession = Depends(get_db)):
    return await update_milestone_status(id, data.status, db)

# --- OUTCOMES ENDPOINTS ---
@router.post('/projects/{id}/outcomes', response_model=OutcomeResponse)
async def record_outcomes_endpoint(id: int, data: OutcomeUpsert, db: AsyncSession = Depends(get_db)):
    return await upsert_project_outcomes(id, data, db)

# --- INDUSTRY PARTNERSHIPS ENDPOINTS ---
@router.post('/projects/{id}/partnerships', response_model=PartnershipResponse)
async def request_partnership_endpoint(id: int, data: PartnershipCreate, db: AsyncSession = Depends(get_db)):
    return await request_partnership(id, data, db)

@router.patch('/partnerships/{id}/status', response_model=PartnershipResponse)
async def update_partnership_status_endpoint(id: int, data: PartnershipStatusUpdate, db: AsyncSession = Depends(get_db)):
    return await update_partnership_status(id, data.status, db)

# --- DASHBOARD ENDPOINT ---
@router.get('/dashboard', response_model=DashboardStats)
async def get_dashboard_endpoint(db: AsyncSession = Depends(get_db)):
    return await get_dashboard_summary(db)
"""
