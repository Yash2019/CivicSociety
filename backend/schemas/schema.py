from pydantic import BaseModel

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
    description: str
    submitter_type: SubmitterType
    district: str
    latitude: float
    longitude: float
    category: ProblemCategory
    status: StatusType

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


    


