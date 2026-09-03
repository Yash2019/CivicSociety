from fastapi import APIRouter, Depends, UploadFile, Form, File
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.db import get_db
from backend.schemas.schema import ProblemSchemaInput, ProblemSchemaOutput, InstitutionResponse, Institution
from backend.services.classification import inputProblems, getProblems, createYourInstitution, getProblemsForInstitution
from backend.enums import SubmitterType, InstitutionDomain, InstitutionType

router = APIRouter()

@router.post('/PostProblems', response_model=ProblemSchemaOutput)
async def Problems_endpoint(
    title: str = Form(...),
    description: str = Form(...),
    submitter_type: SubmitterType = Form(...),
    district: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    photo: UploadFile = File(...),

    db: AsyncSession = Depends(get_db),
    ):


    data = ProblemSchemaInput(
            title=title,
            description=description,
            submitter_type=submitter_type,
            district=district,
            latitude=latitude,
            longitude=longitude,
    )

    return await inputProblems(data, photo, db)

@router.get('/get_problem{user_id}', response_model=ProblemSchemaOutput)
async def get_problem_endpoint(user_id: int, db: AsyncSession = Depends(get_db)):
    return await getProblems(user_id, db)

@router.post('/create_instituion', response_model=InstitutionResponse)
async def create_instition_endpoint(
    name: str = Form(...),
    type: InstitutionType = Form(...),
    domain: InstitutionDomain = Form(...),
    district: str = Form(...),
    has_incubation: bool = Form(...),
    db: AsyncSession = Depends(get_db),
):
    data = Institution(
        name=name,
        type=type,
        domain=domain,
        district=district,
        has_incubation=has_incubation,
    )
    return await createYourInstitution(data, db)

@router.get('/institutions/{id}/problems', response_model=list[ProblemSchemaInput])
async def route_institute_endpoint(id: int, db: AsyncSession = Depends(get_db)):
    return await getProblemsForInstitution(id, db)
