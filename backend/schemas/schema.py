from pydantic import BaseModel, ConfigDict

from backend.enums import SubmitterType, StatusType, ProblemCategory, InstitutionDomain, InstitutionType

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


    


