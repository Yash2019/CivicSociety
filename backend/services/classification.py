
from sqlalchemy.ext.asyncio import AsyncSession
from backend.schemas.schema import ProblemSchemaInput
from backend.db.db import get_db
from backend.Models.problems_db import Problems



async def inputProblems(data: ProblemSchemaInput, db: AsyncSession):
    problems = Problems(
        title= data.title,
        description= data.description,
        submitter_type= data.submitter_type,
        district=data.district,
        latitide=data.latitide,
        longitude=data.longitude,
    )

    db.add(problems)
    await db.commit()

    return problems