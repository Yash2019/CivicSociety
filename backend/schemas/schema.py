from datetime import datetime, date
import re
from pydantic import BaseModel, ConfigDict, Field, field_validator

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
    UserRole,
    DeliverableDocType,
)

class ProblemSchemaInput(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=10, max_length=10_000)
    submitter_type: SubmitterType = SubmitterType.individual
    category: ProblemCategory | None = None
    district: str = Field(min_length=2, max_length=120)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    submitted_by: int | None = None

    @field_validator("submitted_by", mode="before")
    @classmethod
    def sanitize_submitted_by(cls, v):
        if v is not None and (v == 0 or v == "" or (isinstance(v, int) and v <= 0)):
            return None
        return v

    @field_validator("title", "description", "district")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank")
        return value

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
    submitted_by: int | None = None

    model_config = ConfigDict(from_attributes=True)

class RoutedProblemResponse(BaseModel):
    routing_id: int
    routing_status: RoutingStatus
    matched_reason: str
    problem: ProblemSchemaOutput

    model_config = ConfigDict(from_attributes=True)

class Institution(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    type: InstitutionType = InstitutionType.university
    domain: InstitutionDomain | None = None
    domains: list[InstitutionDomain] = Field(default_factory=list)
    district: str = Field(min_length=2, max_length=120)
    has_incubation: bool = False

    @field_validator("name", "district")
    @classmethod
    def strip_institution_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank")
        return value

class InstitutionResponse(BaseModel):
    id: int
    name: str
    type: InstitutionType
    domain: InstitutionDomain | None = None
    domains: list[str] = []
    district: str
    has_incubation: bool

    model_config = ConfigDict(from_attributes=True)



class TeamCreate(BaseModel):
    problem_id: int = Field(gt=0)
    institution_id: int = Field(gt=0)
    faculty_mentor_id: int = Field(gt=0)
    member_user_ids: list[int] = Field(default_factory=list)

    @field_validator("member_user_ids")
    @classmethod
    def unique_member_ids(cls, value: list[int]) -> list[int]:
        if any(user_id <= 0 for user_id in value):
            raise ValueError("Member user IDs must be positive")
        if len(value) != len(set(value)):
            raise ValueError("Member user IDs must be unique")
        return value

class TeamResponse(BaseModel):
    id: int
    problem_id: int
    institution_id: int
    faculty_mentor_id: int
    member_user_ids: list[int] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)

# --- Project Schemas ---
class ProjectCreate(BaseModel):
    team_id: int = Field(gt=0)
    problem_id: int = Field(gt=0)
    title: str = Field(min_length=3, max_length=255)
    proposal_text: str = Field(min_length=20, max_length=20_000)

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
    title: str = Field(min_length=3, max_length=255)
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
    patents_filed: int = Field(default=0, ge=0)
    startups_created: int = Field(default=0, ge=0)
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
class DeliverableResponse(BaseModel):
    id: int
    project_id: int
    milestone_id: int | None
    file_url: str
    doc_type: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Message Schemas ---
class MessageCreate(BaseModel):
    sender_user_id: int = Field(gt=0)
    message_text: str = Field(min_length=1, max_length=10_000)

    @field_validator("message_text")
    @classmethod
    def strip_message(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Message cannot be blank")
        return value

class MessageResponse(BaseModel):
    id: int
    project_id: int
    sender_user_id: int
    sender_name: str | None = None
    message_text: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Dashboard Summary Schema ---
class DashboardStats(BaseModel):
    total_problems: int
    problems_by_status: dict[str, int]
    problems_by_category: dict[str, int]
    problems_by_district: dict[str, int]
    problems_by_submitter_type: dict[str, int]
    total_projects: int
    projects_by_stage: dict[str, int]
    completion_rate: float
    total_patents: int
    total_startups: int
    active_industry_partnerships: int
    partnerships_by_type: dict[str, int]
    participating_institutions_count: int


# --- User Schemas ---
class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=3, max_length=150)
    role: UserRole = UserRole.citizen
    institution_id: int | None = None

    @field_validator("institution_id", mode="before")
    @classmethod
    def sanitize_institution_id(cls, v):
        if v is not None and (v == 0 or v == "" or (isinstance(v, int) and v <= 0)):
            return None
        return v

    @field_validator("name", "email")
    @classmethod
    def normalize_user_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank")
        return value.lower() if "@" in value else value

    @field_validator("email")
    @classmethod
    def validate_email_shape(cls, value: str) -> str:
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Enter a valid email address")
        return value

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    institution_id: int | None = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

