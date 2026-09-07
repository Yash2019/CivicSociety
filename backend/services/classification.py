from datetime import datetime, timezone
from pathlib import Path
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.schemas.schema import (
    ProblemSchemaInput,
    ProblemSchemaOutput,
    Institution,
    TeamCreate,
    ProjectCreate,
    MilestoneCreate,
    OutcomeUpsert,
    PartnershipCreate,
    MessageCreate,
    UserCreate,
)
from backend.Models.users_db import Users
from backend.Models.problems_db import Problems, ProblemMedia
from backend.Models.institutions import Institutions, Routings
from backend.Models.teams_db import Teams, Team_member as TeamMember
from backend.Models.projects_db import Projects
from backend.Models.milestones_db import Milestones
from backend.Models.projectoutcome_db import ProjectOutcomes
from backend.Models.industrypartnership_db import IndustryPartnerships
from backend.Models.deliverables_db import Deliverables
from backend.Models.messages_db import Messages

from backend.enums import (
    StatusType,
    InstitutionType,
    InstitutionDomain,
    RoutingStatus,
    ProjectStage,
    ApprovalStatus,
    MilestoneStatus,
    PartnershipType,
    PartnershipStatus,
)
from backend.trans.translation import classify_issue
from backend.services.duplication import find_duplicate


UPLOAD_DIR = Path("backend/media")

SUBMITTER_WEIGHTS = {
    "govt_dept": 90,
    "ulb": 85,
    "pri": 80,
    "community_org": 65,
    "individual": 40,
}

def compute_priority_score(submitter_type_value: str, has_media: bool = True) -> int:
    base = SUBMITTER_WEIGHTS.get(submitter_type_value, 40)
    evidence_bonus = 10 if has_media else 0
    return min(base + evidence_bonus, 100)


async def inputProblems(data: ProblemSchemaInput, 
                        photo: UploadFile | None,
                        db: AsyncSession):
    
    category = classify_issue(data.description)

    dup = await find_duplicate(data.title, data.description, category, db)
    
    has_photo = photo is not None and bool(getattr(photo, "filename", None))
    submitter_key = getattr(data.submitter_type, "value", str(data.submitter_type))
    priority = compute_priority_score(submitter_key, has_media=has_photo)

    submitted_by = data.submitted_by if data.submitted_by and data.submitted_by > 0 else None
    if submitted_by:
        sub_user = await db.get(Users, submitted_by)
        if not sub_user:
            raise HTTPException(status_code=404, detail=f"User {submitted_by} not found")

    problem = Problems(
        title=data.title,
        description=data.description,
        priority_score=priority,
        submitter_type=data.submitter_type,
        submitted_by=submitted_by,
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

    if has_photo and photo is not None:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        filename = photo.filename or f"photo_{int(datetime.now(timezone.utc).timestamp())}.bin"
        file_path = UPLOAD_DIR / f"{problem.id}_{filename}"

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
    user_problem = select(Problems).where(Problems.submitted_by == user_id).order_by(Problems.created_at.desc())
    result = await db.execute(user_problem)
    return result.scalars().all()


async def createYourInstitution(data: Institution, db: AsyncSession):
    domains_list = [d.strip() for d in data.domains if d.strip()] if data.domains else []
    if data.domain:
        domain_val = data.domain.value if hasattr(data.domain, "value") else str(data.domain)
        if domain_val not in domains_list:
            domains_list.append(domain_val)

    primary_domain = data.domain
    if not primary_domain and domains_list:
        try:
            primary_domain = InstitutionDomain(domains_list[0])
        except ValueError:
            primary_domain = None

    create_ins = Institutions(
        name=data.name,
        type=data.type,
        domain=primary_domain,
        domains=domains_list,
        district=data.district,
        has_incubation=data.has_incubation
    )

    db.add(create_ins)
    await db.commit()
    await db.refresh(create_ins)

    return create_ins


async def routeProblemtoInstitute(problem_id: int, db: AsyncSession):
    from sqlalchemy import or_
    problem = await db.get(Problems, problem_id)
    if not problem or not problem.category:
        return []

    cat_value = problem.category.value if hasattr(problem.category, "value") else str(problem.category)

    stmt = select(Institutions).where(
        or_(
            Institutions.domains.contains([cat_value]),
            Institutions.domain == problem.category
        )
    )
    result = await db.execute(stmt)
    institutions = result.scalars().all()

    for inst in institutions:
        routing = Routings(
            problems_id=problem.id,
            institution_id=inst.id,
            matched_reason=f"domain_matched:{cat_value}"
        )
        db.add(routing)

    if institutions:
        problem.status = StatusType.routed

    await db.flush()


async def getProblemsForInstitution(institution_id: int, db: AsyncSession):
    institution = await db.get(Institutions, institution_id)
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")

    stmt = (
        select(Routings, Problems)
        .join(Problems, Routings.problems_id == Problems.id)
        .where(Routings.institution_id == institution_id)
        .order_by(Routings.created_at.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()
    return [
        {
            "routing_id": routing.id,
            "routing_status": routing.status,
            "matched_reason": routing.matched_reason,
            "problem": problem,
        }
        for routing, problem in rows
    ]


# ------------------------------------------------------------------------------
# Routing Actions (Accept / Decline)
# ------------------------------------------------------------------------------
async def update_routing_status(routing_id: int, new_status: RoutingStatus, db: AsyncSession):
    routing = await db.get(Routings, routing_id)
    if not routing:
        raise HTTPException(status_code=404, detail="Routing record not found")
    routing.status = new_status
    await db.commit()
    await db.refresh(routing)
    return routing


# ------------------------------------------------------------------------------
# Teams & Project Lifecycle Services
# ------------------------------------------------------------------------------
async def create_team(data: TeamCreate, db: AsyncSession):
    problem = await db.get(Problems, data.problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    institution = await db.get(Institutions, data.institution_id)
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")

    mentor = await db.get(Users, data.faculty_mentor_id)
    if not mentor:
        raise HTTPException(status_code=404, detail="Faculty mentor user not found")

    valid_member_ids = [uid for uid in data.member_user_ids if uid and uid > 0]
    for user_id in valid_member_ids:
        member_user = await db.get(Users, user_id)
        if not member_user:
            raise HTTPException(status_code=404, detail=f"Member user {user_id} not found")

    new_team = Teams(
        problem_id=data.problem_id,
        institution_id=data.institution_id,
        faculty_mentor_id=data.faculty_mentor_id
    )
    db.add(new_team)
    await db.flush()

    for user_id in valid_member_ids:
        member = TeamMember(team_id=new_team.id, user_id=user_id)
        db.add(member)

    await db.commit()
    await db.refresh(new_team)
    return {
        "id": new_team.id,
        "problem_id": new_team.problem_id,
        "institution_id": new_team.institution_id,
        "faculty_mentor_id": new_team.faculty_mentor_id,
        "member_user_ids": valid_member_ids
    }


async def get_team(team_id: int, db: AsyncSession):
    team = await db.get(Teams, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    stmt = select(TeamMember.user_id).where(TeamMember.team_id == team_id)
    res = await db.execute(stmt)
    member_ids = list(res.scalars().all())
    return {
        "id": team.id,
        "problem_id": team.problem_id,
        "institution_id": team.institution_id,
        "faculty_mentor_id": team.faculty_mentor_id,
        "member_user_ids": member_ids
    }


async def list_teams(db: AsyncSession):
    stmt = select(Teams).order_by(Teams.created_at.desc())
    res = await db.execute(stmt)
    teams = res.scalars().all()
    results = []
    for t in teams:
        m_stmt = select(TeamMember.user_id).where(TeamMember.team_id == t.id)
        m_res = await db.execute(m_stmt)
        results.append({
            "id": t.id,
            "problem_id": t.problem_id,
            "institution_id": t.institution_id,
            "faculty_mentor_id": t.faculty_mentor_id,
            "member_user_ids": list(m_res.scalars().all())
        })
    return results


async def create_project(data: ProjectCreate, db: AsyncSession):
    team = await db.get(Teams, data.team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if team.problem_id != data.problem_id:
        raise HTTPException(status_code=400, detail="Team problem_id does not match project problem_id")

    routing_stmt = select(Routings).where(
        Routings.problems_id == data.problem_id,
        Routings.institution_id == team.institution_id,
        Routings.status == RoutingStatus.accepted
    )
    routing_res = await db.execute(routing_stmt)
    if not routing_res.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Cannot create project proposal: routing for this problem and institution has not been accepted yet."
        )

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
    admin = await db.get(Users, admin_id)
    if not admin:
        raise HTTPException(status_code=404, detail="Approving user not found")
    project.approval_status = approval_status
    project.approved_by_user_id = admin_id
    if approval_status == ApprovalStatus.approved and project.stage == ProjectStage.proposed:
        project.stage = ProjectStage.active
    await db.commit()
    await db.refresh(project)
    return project


# ------------------------------------------------------------------------------
# Milestones & Outcomes Services
# ------------------------------------------------------------------------------
async def add_milestone(project_id: int, data: MilestoneCreate, db: AsyncSession):
    project = await db.get(Projects, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
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
        milestone.completed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(milestone)
    return milestone


async def get_project_milestones(project_id: int, db: AsyncSession):
    project = await db.get(Projects, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    stmt = select(Milestones).where(Milestones.project_id == project_id).order_by(Milestones.due_date.asc().nulls_last())
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_project_outcomes(project_id: int, db: AsyncSession):
    project = await db.get(Projects, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    stmt = select(ProjectOutcomes).where(ProjectOutcomes.project_id == project_id)
    result = await db.execute(stmt)
    outcome = result.scalar_one_or_none()
    if not outcome:
        return {
            "id": 0,
            "project_id": project_id,
            "patents_filed": 0,
            "startups_created": 0,
            "ip_generated": None,
            "impact_notes": None
        }
    return outcome


async def upsert_project_outcomes(project_id: int, data: OutcomeUpsert, db: AsyncSession):
    project = await db.get(Projects, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
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
# Deliverables Services
# ------------------------------------------------------------------------------
async def add_deliverable(project_id: int, milestone_id: int | None, doc_type: str, file: UploadFile, db: AsyncSession):
    project = await db.get(Projects, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    valid_milestone_id = milestone_id if milestone_id and milestone_id > 0 else None
    if valid_milestone_id is not None:
        milestone = await db.get(Milestones, valid_milestone_id)
        if not milestone or milestone.project_id != project_id:
            raise HTTPException(status_code=400, detail="Milestone does not belong to this project")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = file.filename or f"deliverable_{int(datetime.now(timezone.utc).timestamp())}.bin"
    file_path = UPLOAD_DIR / f"deliverable_{project_id}_{filename}"
    with file_path.open("wb") as buffer:
        buffer.write(await file.read())

    deliverable = Deliverables(
        project_id=project_id,
        milestone_id=valid_milestone_id,
        file_url=str(file_path),
        doc_type=doc_type
    )
    db.add(deliverable)
    await db.commit()
    await db.refresh(deliverable)
    return deliverable


async def get_project_deliverables(project_id: int, db: AsyncSession):
    project = await db.get(Projects, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    stmt = select(Deliverables).where(Deliverables.project_id == project_id)
    result = await db.execute(stmt)
    return result.scalars().all()


# ------------------------------------------------------------------------------
# Industry Partnerships Services
# ------------------------------------------------------------------------------
async def request_partnership(project_id: int, data: PartnershipCreate, db: AsyncSession):
    project = await db.get(Projects, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    institution = await db.get(Institutions, data.industry_institution_id)
    if not institution:
        raise HTTPException(status_code=404, detail="Industry institution not found")

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


async def get_project_partnerships(project_id: int, db: AsyncSession):
    project = await db.get(Projects, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    stmt = select(IndustryPartnerships).where(IndustryPartnerships.project_id == project_id)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_institution_partnerships(institution_id: int, db: AsyncSession):
    institution = await db.get(Institutions, institution_id)
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")
    stmt = select(IndustryPartnerships).where(IndustryPartnerships.industry_institution_id == institution_id)
    result = await db.execute(stmt)
    return result.scalars().all()


# ------------------------------------------------------------------------------
# Project Collaboration & Communication Thread
# ------------------------------------------------------------------------------
async def add_project_message(project_id: int, data: MessageCreate, db: AsyncSession):
    project = await db.get(Projects, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    sender = await db.get(Users, data.sender_user_id)
    if not sender:
        raise HTTPException(status_code=404, detail="Sender user not found")

    new_msg = Messages(
        project_id=project_id,
        sender_user_id=data.sender_user_id,
        message_text=data.message_text
    )
    db.add(new_msg)
    await db.commit()
    await db.refresh(new_msg)
    return {
        "id": new_msg.id,
        "project_id": new_msg.project_id,
        "sender_user_id": new_msg.sender_user_id,
        "sender_name": sender.name,
        "message_text": new_msg.message_text,
        "created_at": new_msg.created_at
    }


async def get_project_messages(project_id: int, db: AsyncSession):
    project = await db.get(Projects, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    stmt = (
        select(Messages, Users.name)
        .join(Users, Messages.sender_user_id == Users.id)
        .where(Messages.project_id == project_id)
        .order_by(Messages.created_at.asc())
    )
    result = await db.execute(stmt)
    rows = result.all()
    return [
        {
            "id": msg.id,
            "project_id": msg.project_id,
            "sender_user_id": msg.sender_user_id,
            "sender_name": sender_name,
            "message_text": msg.message_text,
            "created_at": msg.created_at
        }
        for msg, sender_name in rows
    ]


# ------------------------------------------------------------------------------
# Analytics Dashboard Aggregator
# ------------------------------------------------------------------------------
async def get_dashboard_summary(db: AsyncSession):
    total_problems = await db.scalar(select(func.count(Problems.id))) or 0

    status_res = await db.execute(select(Problems.status, func.count(Problems.id)).group_by(Problems.status))
    problems_by_status = {
        str(row[0].value if hasattr(row[0], "value") else row[0]): row[1]
        for row in status_res.all() if row[0] is not None
    }

    cat_res = await db.execute(select(Problems.category, func.count(Problems.id)).group_by(Problems.category))
    problems_by_category = {
        str(row[0].value if hasattr(row[0], "value") else row[0]): row[1]
        for row in cat_res.all() if row[0] is not None
    }

    dist_res = await db.execute(select(Problems.district, func.count(Problems.id)).group_by(Problems.district))
    problems_by_district = {
        str(row[0]): row[1]
        for row in dist_res.all() if row[0] is not None
    }

    sub_res = await db.execute(select(Problems.submitter_type, func.count(Problems.id)).group_by(Problems.submitter_type))
    problems_by_submitter_type = {
        str(row[0].value if hasattr(row[0], "value") else row[0]): row[1]
        for row in sub_res.all() if row[0] is not None
    }

    total_projects = await db.scalar(select(func.count(Projects.id))) or 0
    stage_res = await db.execute(select(Projects.stage, func.count(Projects.id)).group_by(Projects.stage))
    projects_by_stage = {
        str(row[0].value if hasattr(row[0], "value") else row[0]): row[1]
        for row in stage_res.all() if row[0] is not None
    }

    completed_count = projects_by_stage.get("completed", 0)
    completion_rate = round((completed_count / total_projects * 100), 2) if total_projects > 0 else 0.0

    total_patents = await db.scalar(select(func.coalesce(func.sum(ProjectOutcomes.patents_filed), 0))) or 0
    total_startups = await db.scalar(select(func.coalesce(func.sum(ProjectOutcomes.startups_created), 0))) or 0

    active_partnerships = await db.scalar(
        select(func.count(IndustryPartnerships.id))
        .where(IndustryPartnerships.status == PartnershipStatus.accepted)
    ) or 0

    ptype_res = await db.execute(select(IndustryPartnerships.partnership_type, func.count(IndustryPartnerships.id)).group_by(IndustryPartnerships.partnership_type))
    partnerships_by_type = {
        str(row[0].value if hasattr(row[0], "value") else row[0]): row[1]
        for row in ptype_res.all() if row[0] is not None
    }

    participating_institutions_count = await db.scalar(
        select(func.count(func.distinct(Routings.institution_id)))
    ) or 0

    return {
        "total_problems": int(total_problems),
        "problems_by_status": problems_by_status,
        "problems_by_category": problems_by_category,
        "problems_by_district": problems_by_district,
        "problems_by_submitter_type": problems_by_submitter_type,
        "total_projects": int(total_projects),
        "projects_by_stage": projects_by_stage,
        "completion_rate": completion_rate,
        "total_patents": int(total_patents),
        "total_startups": int(total_startups),
        "active_industry_partnerships": int(active_partnerships),
        "partnerships_by_type": partnerships_by_type,
        "participating_institutions_count": int(participating_institutions_count)
    }


# ------------------------------------------------------------------------------
# Users Services
# ------------------------------------------------------------------------------
async def create_user(data: UserCreate, db: AsyncSession):
    existing = await db.scalar(select(Users).where(Users.email == data.email))
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    institution_id = data.institution_id if data.institution_id and data.institution_id > 0 else None
    if institution_id:
        inst = await db.get(Institutions, institution_id)
        if not inst:
            raise HTTPException(status_code=404, detail="Institution not found")

    new_user = Users(
        name=data.name,
        email=data.email,
        role=data.role,
        institution_id=institution_id
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def get_user(user_id: int, db: AsyncSession):
    user = await db.get(Users, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


async def list_users(db: AsyncSession):
    stmt = select(Users).order_by(Users.id.asc())
    res = await db.execute(stmt)
    return res.scalars().all()
