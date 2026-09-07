from datetime import datetime, date
from pydantic import BaseModel, ConfigDict

from backend.enums import (
    SubmitterType,
    StatusType,
    ProblemCategory,
    InstitutionDomain,
    InstitutionType,
    RoutingStatus,
    ProjectStage,
    ApprovalStatus,
    MilestoneStatus,
    PartnershipType,
    PartnershipStatus,
)

class ProblemSchemaInput(BaseModel):
    title: str
    description: str
    submitter_type: SubmitterType
    district: str
    latitude: float
    longitude: float

class ProblemSchemaOutput(BaseModel):
    id: int
    title: str | None = None
    description: str
    priority_score: int | None = None
    submitter_type: SubmitterType
    district: str
    latitude: float
    longitude: float
    category: ProblemCategory | None = None
    status: StatusType | None = None
    duplicate_problem: int | None = None

    model_config = ConfigDict(from_attributes=True)

class Institution(BaseModel):
    name: str
    type: InstitutionType
    domain: InstitutionDomain
    district: str
    has_incubation: bool

class InstitutionResponse(BaseModel):
    id: int
    name: str
    type: InstitutionType
    domain: InstitutionDomain
    district: str
    has_incubation: bool

    model_config = ConfigDict(from_attributes=True)



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

# --- Deliverables Schemas ---
class DeliverableCreate(BaseModel):
    milestone_id: int | None = None
    doc_type: str

class DeliverableResponse(BaseModel):
    id: int
    project_id: int
    milestone_id: int | None
    file_url: str
    doc_type: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Routing Schemas ---
class RoutingStatusUpdate(BaseModel):
    status: RoutingStatus

class RoutingResponse(BaseModel):
    id: int
    problems_id: int
    institution_id: int
    matched_reason: str
    status: RoutingStatus
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- User Schemas ---
class UserCreate(BaseModel):
    name: str
    email: str
    role: str = "citizen"
    institution_id: int | None = None

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    institution_id: int | None
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

