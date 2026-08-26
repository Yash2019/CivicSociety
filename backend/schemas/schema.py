from pydantic import BaseModel
from backend.Models.problems_db import SubmitterType, StatusType
title, description, submitter_type, district, lat/long)
File upload endpoint for problem_media (store to disk/S3, save URL)

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
    


    