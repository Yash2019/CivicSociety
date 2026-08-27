from pydantic import BaseModel

from backend.enums import SubmitterType, StatusType

class ProblemSchemaInput(BaseModel):
    title: str
    description: str
    submitter_type: SubmitterType
    district: str
    latitide: float
    longitude: float

class ProblemSchemaOutput(BaseModel):
    id: int
    description: str
    submitter_type: SubmitterType
    district: str
    latitide: float
    longitude: float
    Status: StatusType
    


    