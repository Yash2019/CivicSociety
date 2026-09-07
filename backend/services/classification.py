
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

SUBMITTER_WEIGHTS = {
    "govt_dept": 90,
    "ulb": 85,
    "pri": 80,
    "community_org": 65,
    "individual": 50,
}

async def inputProblems(data: ProblemSchemaInput, 
                        photo: UploadFile,
                        db: AsyncSession):
    
    category = classify_issue(data.description)

    dup = await find_duplicate(data.title, data.description, category, db)
    
    submitter_key = getattr(data.submitter_type, "value", str(data.submitter_type))
    priority = SUBMITTER_WEIGHTS.get(submitter_key, 50) + 10

    problem = Problems(
        title=data.title,
        description=data.description,
        priority_score=priority,
        submitter_type=data.submitter_type,
        district=data.district,
        latitude=data.latitude,
        longitude=data.longitude,
        status=StatusType.duplicate if dup else StatusType.submitted,
        duplicate_problem=dup["duplicate_of_id"] if dup else None,
        category=category
    )

    db.add(problem)
    await db.flush()

    if not dup:
        await routeProblemtoInstitute(problem.id, db)

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    file_path = UPLOAD_DIR / f"{problem.id}_{photo.filename}"

    with file_path.open("wb") as buffer:
        buffer.write(await photo.read())

    media = ProblemMedia(
        problem_id=problem.id,
        file_url=str(file_path),
        file_type=photo.content_type or "application/octet-stream"
    )

    db.add(media)

    await db.commit()
    await db.refresh(problem)

    return problem

async def getProblems(user_id: int, db: AsyncSession):
    user_problem = select(Problems).where(Problems.submitted_by == user_id)
    result = await db.execute(user_problem)
    return result.scalars().all()

async def createYourInstitution(data:Institution, db: AsyncSession):
    create_ins = Institutions(
        name=data.name,
        type=data.type,
        domain=data.domain,
        district=data.district,
        has_incubation=data.has_incubation
    )

    db.add(create_ins)
    await db.commit()
    await db.refresh(create_ins)

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
            matched_reason="domain_matched"
        )
        db.add(routing)

    await db.flush()

async def getProblemsForInstitution(institution_id: int, db: AsyncSession):

    stmt = select(Routings.problems_id).where(Routings.institution_id == institution_id)
    result = await db.execute(stmt)
    problem_ids = result.scalars().all()
    if not problem_ids:
        return []

    stmt = select(Problems).where(Problems.id.in_(problem_ids))
    result = await db.execute(stmt)
    return result.scalars().all()

    
SUBMITTER_WEIGHTS = {
    "govt_dept": 90,
    "ulb": 85,
    "pri": 80,
    "community_org": 65,
    "individual": 40
}

def compute_priority_score(submitter_type_value: str, has_media: bool = True) -> int:
    base = SUBMITTER_WEIGHTS.get(submitter_type_value, 40)
    # Extra points for visual evidence validation
    evidence_bonus = 10 if has_media else 0
    return min(base + evidence_bonus, 100)


# ------------------------------------------------------------------------------
# 5.2 Routing Actions (Accept / Decline)
# ------------------------------------------------------------------------------
# from backend.Models.institutions import Routings
# from backend.enums import RoutingStatus

async def update_routing_status(routing_id: int, new_status: str, db: AsyncSession):
    # routing = await db.get(Routings, routing_id)
    # if not routing:
    #     raise HTTPException(status_code=404, detail="Routing record not found")
    # routing.status = new_status
    # await db.commit()
    # await db.refresh(routing)
    # return routing
    pass


# ------------------------------------------------------------------------------
# 5.3 Teams & Project Lifecycle Services
# ------------------------------------------------------------------------------
async def create_team(data: TeamCreate, db: AsyncSession):
    """
    Creates a multidisciplinary team and maps the student members.
    """
    # 1. Create team record
    new_team = Teams(
        problem_id=data.problem_id,
        institution_id=data.institution_id,
        faculty_mentor_id=data.faculty_mentor_id
    )
    db.add(new_team)
    await db.flush() # get new_team.id

    # 2. Add team members
    for user_id in data.member_user_ids:
        member = TeamMember(team_id=new_team.id, user_id=user_id)
        db.add(member)

    await db.commit()
    await db.refresh(new_team)
    return {
        "id": new_team.id,
        "problem_id": new_team.problem_id,
        "institution_id": new_team.institution_id,
        "faculty_mentor_id": new_team.faculty_mentor_id,
        "member_user_ids": data.member_user_ids
    }

async def create_project(data: ProjectCreate, db: AsyncSession):
    """
    Creates a solution proposal for a team solving a specific problem.
    """
    project = Projects(
        team_id=data.team_id,
        problem_id=data.problem_id,
        title=data.title,
        proposal_text=data.proposal_text,
        stage=ProjectStage.proposed,
        approval_status=ApprovalStatus.pending
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project

async def update_project_stage(project_id: int, new_stage: ProjectStage, db: AsyncSession):
    project = await db.get(Projects, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project.stage = new_stage
    await db.commit()
    await db.refresh(project)
    return project

async def approve_project(project_id: int, approval_status: ApprovalStatus, admin_id: int, db: AsyncSession):
    project = await db.get(Projects, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project.approval_status = approval_status
    project.approved_by_user_id = admin_id
    if approval_status == ApprovalStatus.approved and project.stage == ProjectStage.proposed:
        project.stage = ProjectStage.active
    await db.commit()
    await db.refresh(project)
    return project


# ------------------------------------------------------------------------------
# 5.4 Milestones & Outcomes Services
# ------------------------------------------------------------------------------
async def add_milestone(project_id: int, data: MilestoneCreate, db: AsyncSession):
    milestone = Milestones(
        project_id=project_id,
        title=data.title,
        description=data.description,
        due_date=data.due_date,
        status=MilestoneStatus.pending
    )
    db.add(milestone)
    await db.commit()
    await db.refresh(milestone)
    return milestone

async def update_milestone_status(milestone_id: int, status: MilestoneStatus, db: AsyncSession):
    milestone = await db.get(Milestones, milestone_id)
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    milestone.status = status
    if status == MilestoneStatus.completed:
        milestone.completed_at = datetime.utcnow()
    await db.commit()
    await db.refresh(milestone)
    return milestone

async def upsert_project_outcomes(project_id: int, data: OutcomeUpsert, db: AsyncSession):
    stmt = select(ProjectOutcomes).where(ProjectOutcomes.project_id == project_id)
    result = await db.execute(stmt)
    outcome = result.scalar_one_or_none()

    if not outcome:
        outcome = ProjectOutcomes(
            project_id=project_id,
            patents_filed=data.patents_filed,
            startups_created=data.startups_created,
            ip_generated=data.ip_generated,
            impact_notes=data.impact_notes
        )
        db.add(outcome)
    else:
        outcome.patents_filed = data.patents_filed
        outcome.startups_created = data.startups_created
        outcome.ip_generated = data.ip_generated
        outcome.impact_notes = data.impact_notes

    await db.commit()
    await db.refresh(outcome)
    return outcome


# ------------------------------------------------------------------------------
# 5.5 Industry Partnerships Services
# ------------------------------------------------------------------------------
async def request_partnership(project_id: int, data: PartnershipCreate, db: AsyncSession):
    partnership = IndustryPartnerships(
        project_id=project_id,
        industry_institution_id=data.industry_institution_id,
        partnership_type=data.partnership_type,
        notes=data.notes,
        status=PartnershipStatus.requested
    )
    db.add(partnership)
    await db.commit()
    await db.refresh(partnership)
    return partnership

async def update_partnership_status(partnership_id: int, status: PartnershipStatus, db: AsyncSession):
    partnership = await db.get(IndustryPartnerships, partnership_id)
    if not partnership:
        raise HTTPException(status_code=404, detail="Partnership request not found")
    partnership.status = status
    await db.commit()
    await db.refresh(partnership)
    return partnership


# ------------------------------------------------------------------------------
# 5.6 Analytics Dashboard Aggregation
# ------------------------------------------------------------------------------
async def get_dashboard_summary(db: AsyncSession):
    """
    Executes fast aggregate queries for the judge/government dashboard:
    - Problem breakdown by status, category, district
    - Project stage breakdown
    - Quantified impacts (patents, startups, partnerships)
    """
    # 1. Total Problems
    # problems_total = await db.scalar(select(func.count(Problems.id))) or 0
    # 2. Problems grouped by status
    # status_q = await db.execute(select(Problems.status, func.count(Problems.id)).group_by(Problems.status))
    # problems_by_status = {str(k.value if hasattr(k, 'value') else k): count for k, count in status_q.all()}
    
    # 3. Problems grouped by category
    # cat_q = await db.execute(select(Problems.category, func.count(Problems.id)).group_by(Problems.category))
    # problems_by_cat = {str(k.value if hasattr(k, 'value') else k): count for k, count in cat_q.all() if k}

    # 4. Total patents and startups from outcomes
    total_patents = await db.scalar(select(func.coalesce(func.sum(ProjectOutcomes.patents_filed), 0))) or 0
    total_startups = await db.scalar(select(func.coalesce(func.sum(ProjectOutcomes.startups_created), 0))) or 0

    # 5. Active partnerships
    active_partnerships = await db.scalar(
        select(func.count(IndustryPartnerships.id))
        .where(IndustryPartnerships.status == PartnershipStatus.accepted)
    ) or 0

    return {
        "total_problems": 0, # replace with problems_total
        "problems_by_status": {}, # replace with problems_by_status
        "problems_by_category": {}, # replace with problems_by_cat
        "problems_by_district": {},
        "total_projects": 0,
        "projects_by_stage": {},
        "total_patents": total_patents,
        "total_startups": total_startups,
        "active_industry_partnerships": active_partnerships
    }
