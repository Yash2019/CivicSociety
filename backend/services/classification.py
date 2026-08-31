
from sqlalchemy.ext.asyncio import AsyncSession
from backend.schemas.schema import ProblemSchemaInput, ProblemSchemaOutput
from backend.Models.problems_db import Problems, ProblemMedia
from pathlib import Path
from fastapi import UploadFile
from backend.enums import StatusType
from sqlalchemy import select
from backend.trans.translation import classify_issue



UPLOAD_DIR = Path("backend/media")

async def inputProblems(data: ProblemSchemaInput, 
                        photo: UploadFile,
                        db: AsyncSession):
    
    problem = Problems(
        title= data.title,
        description= data.description,
        submitter_type= data.submitter_type,
        district=data.district,
        latitude=data.latitude,
        longitude=data.longitude,
        status=StatusType.submitted,
        category = classify_issue(data.description)
    )

    db.add(problem)
    await db.flush()

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    file_path = UPLOAD_DIR / f"{problem.id}_{photo.filename}"

    with file_path.open("wb") as buffer:
        buffer.write(await photo.read())

    media = ProblemMedia(
        problem_id=problem.id,
        file_url=str(file_path),
        file_type=photo.content_type
    )

    db.add(media)

    await db.commit()
    await db.refresh(problem)

    return problem

async def getProblems(user_id: int, db: AsyncSession):
    user_problem = select(Problems).where(Problems.id == user_id)
    result = await db.execute(user_problem)

    prob = result.scalar_one_or_none()
    return prob
