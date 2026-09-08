import asyncio
import sys
from pathlib import Path

# Ensure root directory is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import delete, select
from backend.db.db import SessionLocal, create_table
from backend.Models.users_db import Users
from backend.Models.institutions import Institutions, Routings
from backend.Models.problems_db import Problems, ProblemMedia
from backend.Models.teams_db import Teams, Team_member
from backend.Models.projects_db import Projects
from backend.Models.milestones_db import Milestones
from backend.Models.projectoutcome_db import ProjectOutcomes
from backend.Models.industrypartnership_db import IndustryPartnerships
from backend.Models.deliverables_db import Deliverables
from backend.Models.messages_db import Messages
from backend.enums import (
    SubmitterType,
    StatusType,
    ProblemCategory,
    InstitutionType,
    InstitutionDomain,
    RoutingStatus,
    ProjectStage,
    ApprovalStatus,
    MilestoneStatus,
    PartnershipType,
    PartnershipStatus,
)

async def seed_data(force: bool = False):
    await create_table()
    async with SessionLocal() as db:
        # Check if already seeded
        if not force:
            existing_users = await db.scalar(select(Users.id).limit(1))
            if existing_users:
                print("Database already contains data. Skipping seed.")
                return {"status": "skipped", "message": "Database already contains data. Use force=True to re-seed."}

        if force:
            # Delete dependent records first so the operation is valid on
            # PostgreSQL installations that enforce every foreign key.
            for model in (
                ProblemMedia, Messages, IndustryPartnerships, Deliverables,
                ProjectOutcomes, Milestones, Projects, Team_member, Teams,
                Routings, Problems, Users, Institutions,
            ):
                await db.execute(delete(model))
            await db.commit()

        print("Seeding users...")
        users = [
            Users(name="Ramesh Kumar", email="ramesh.citizen@example.com", role="citizen"),
            Users(name="Sarpanch Gram Panchayat", email="gp.head@gov.in", role="pri"),
            Users(name="Dr. Anita Sharma", email="anita.sharma@nitk.ac.in", role="faculty"),
            Users(name="Rahul Verma", email="rahul.v@student.nitk.ac.in", role="student"),
            Users(name="Priya Patel", email="priya.p@student.nitk.ac.in", role="student"),
            Users(name="Tech Mahindra CSR Lead", email="csr@techm.com", role="industry"),
            Users(name="District Innovation Officer", email="admin.gov@nic.in", role="gov_admin"),
        ]
        db.add_all(users)
        await db.flush()

        print("Seeding institutions...")
        institutions = [
            Institutions(
                name="National Institute of Technology Karnataka (NITK)",
                type=InstitutionType.university,
                domain=InstitutionDomain.water_resources,
                district="Dakshina Kannada",
                has_incubation=True,
            ),
            Institutions(
                name="Indian Agricultural Research Centre",
                type=InstitutionType.research_lab,
                domain=InstitutionDomain.agriculture,
                district="Pune",
                has_incubation=True,
            ),
            Institutions(
                name="Apex Clean Energy Solutions MSME",
                type=InstitutionType.msme,
                domain=InstitutionDomain.energy,
                district="Bengaluru",
                has_incubation=False,
            ),
            Institutions(
                name="HealthTech Innovations Pvt Ltd",
                type=InstitutionType.startup,
                domain=InstitutionDomain.healthcare,
                district="Hyderabad",
                has_incubation=True,
            ),
            Institutions(
                name="Tata Social CSR Foundation",
                type=InstitutionType.csr,
                domain=InstitutionDomain.water_resources,
                district="Mumbai",
                has_incubation=False,
            ),
        ]
        db.add_all(institutions)
        await db.flush()
        users[2].institution_id = institutions[0].id
        users[3].institution_id = institutions[0].id
        users[4].institution_id = institutions[0].id

        print("Seeding problems...")
        problem1 = Problems(
            title="Groundwater Contamination and Salinity in Coastal Wells",
            description="High fluoride and salt concentration affecting drinking water across 4 villages near the coastline. Needs low-cost solar desalination or filtration unit.",
            priority_score=85,
            submitted_by=users[1].id, # PRI official
            submitter_type=SubmitterType.pri,
            district="Dakshina Kannada",
            latitude=12.8700,
            longitude=74.8800,
            category=ProblemCategory.water_resources,
            status=StatusType.routed,
        )
        db.add(problem1)
        await db.flush()

        print("Seeding routing...")
        routing1 = Routings(
            problems_id=problem1.id,
            institution_id=institutions[0].id, # NITK
            matched_reason="Matched domain: water_resources with coastal district proximity",
            status=RoutingStatus.accepted,
        )
        db.add(routing1)
        await db.flush()

        print("Seeding team...")
        team1 = Teams(
            problem_id=problem1.id,
            institution_id=institutions[0].id,
            faculty_mentor_id=users[2].id, # Dr. Anita
        )
        db.add(team1)
        await db.flush()

        members = [
            Team_member(team_id=team1.id, user_id=users[3].id),
            Team_member(team_id=team1.id, user_id=users[4].id),
        ]
        db.add_all(members)

        print("Seeding project proposal...")
        project1 = Projects(
            team_id=team1.id,
            problem_id=problem1.id,
            title="Solar-Powered Low-Maintenance Membrane Desalination System",
            proposal_text="A dual-stage decentralized filtration combining renewable solar power with activated bio-carbon and reverse osmosis membranes designed for village panchayats.",
            stage=ProjectStage.active,
            approval_status=ApprovalStatus.approved,
            approved_by_user_id=users[6].id, # gov_admin
        )
        db.add(project1)
        await db.flush()

        print("Seeding milestones...")
        milestones = [
            Milestones(
                project_id=project1.id,
                title="Water Quality & Contaminant Baseline Analysis",
                description="Sample collection from 10 village borewells and lab spectroscopy report.",
                status=MilestoneStatus.completed,
            ),
            Milestones(
                project_id=project1.id,
                title="CAD Modeling and Prototype Assembly",
                description="Fabrication of 200L/day prototype with solar array integration.",
                status=MilestoneStatus.in_progress,
            ),
            Milestones(
                project_id=project1.id,
                title="Panchayat Field Testing & Validation",
                description="30-day continuous test in village school premises with water testing.",
                status=MilestoneStatus.pending,
            ),
        ]
        db.add_all(milestones)
        await db.flush()

        print("Seeding project outcomes...")
        outcome1 = ProjectOutcomes(
            project_id=project1.id,
            patents_filed=1,
            startups_created=0,
            ip_generated="Low-cost anti-fouling solar membrane bracket design",
            impact_notes="Potentially impacts 3,500 villagers with clean drinking water.",
        )
        db.add(outcome1)

        print("Seeding industry partnership...")
        partnership1 = IndustryPartnerships(
            project_id=project1.id,
            industry_institution_id=institutions[4].id, # Tata CSR
            partnership_type=PartnershipType.funding,
            status=PartnershipStatus.accepted,
            notes="Providing INR 5,00,000 pilot grant for field deployment materials.",
        )
        db.add(partnership1)

        await db.commit()
        print("Database seeded successfully!")
        return {"status": "success", "message": "Database seeded successfully with realistic demo data!"}

if __name__ == "__main__":
    asyncio.run(seed_data())
