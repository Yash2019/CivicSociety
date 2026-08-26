from fastapi import APIRouter, Depends, 
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.db import get_db
from backend.schemas.schema import ProblemSchemaInput, ProblemSchemaOutput
from backend.services.classification import inputProblems

router = APIRouter()

@router.post('/PostProblems', response_model=ProblemSchemaOutput)
async def Problems_endpoint(data: ProblemSchemaInput, db: AsyncSession = Depends(get_db)):
    return await inputProblems(data, db)