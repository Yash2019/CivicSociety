
from sqlalchemy.ext.asyncio import AsyncSession
from backend.schemas.schema import ProblemSchemaInput, ProblemSchemaOutput, Institution
from backend.Models.problems_db import Problems, ProblemMedia
from backend.Models.institutions import Institutions, Routings
from pathlib import Path
from fastapi import UploadFile
from backend.enums import StatusType, InstitutionType, InstitutionDomain
from sqlalchemy import select
from backend.trans.translation import classify_issue
from backend.services.duplication import find_duplicate



UPLOAD_DIR = Path("backend/media")

async def inputProblems(data: ProblemSchemaInput, 
                        photo: UploadFile,
                        db: AsyncSession):
    
    category = classify_issue(data.description)

    dup = await find_duplicate(data.title, data.description, category, db)
    
    problem = Problems(
        title= data.title,
        description= data.description,
        submitter_type= data.submitter_type,
        district=data.district,
        latitude=data.latitude,
        longitude=data.longitude,
        status=StatusType.duplicate if dup else StatusType.submitted,
        duplicate_problem=dup["duplicate_of_id"] if dup else None,
        category = category
    )

    db.add(problem)
    await db.flush()

    await routeProblemtoInstitute(problem.id, db)

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

async def createYourInstitution(data:Institution, db: AsyncSession):
    create_ins = Institutions(
        name = data.name,
        type = data.type,
        domain = data.domain,
        district = data.district,
        has_incubation = data.has_incubation

    )

    db.add(create_ins)
    await db.commit()

    return create_ins


async def routeProblemtoInstitute(problem_id: int, db: AsyncSession):

    problem = await db.get(Problems, problem_id)
    if not problem or not problem.category:
        return []

    stmt = select(Institutions).where(Institutions.domain == problem.category)
    result = await db.execute(stmt)
    institutions = result.scalars().all()


    for inst in institutions:
        routing = Routings(
            problems_id=problem.id,
            institution_id=inst.id,
            matched_reason = "domain_matched"
        )

        db.add(routing)
        await db.commit()

async def getProblemsForInstitution(institution_id: int, db: AsyncSession):

    stmt = select(Routings.problems_id).where(Routings.institution_id == institution_id)
    result = await db.execute(stmt)
    problem_ids = result.scalars().all()
    if not problem_ids:
        return None


    stmt = select(Problems).where(Problems.id.in_(problem_ids))
    result = await db.execute(stmt)
    return result.scalars().all()
    

