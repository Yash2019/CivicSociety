from fastapi import APIRouter, Depends, UploadFile, Form, File
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.db import get_db
from backend.schemas.schema import ProblemSchemaInput, ProblemSchemaOutput
from backend.services.classification import inputProblems
from backend.enums import SubmitterType

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
