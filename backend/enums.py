# backend/enums.py
from enum import Enum

class SubmitterType(str, Enum):
    individual = "individual"
    community_org = "community_org"
    pri = "pri"
    ulb = "ulb"
    govt_dept = "govt_dept"

class StatusType(str, Enum):
    submitted = "submitted"
    under_review = "under_review"
    routed = "routed"
    rejected = "rejected"
    duplicate = "duplicate"

class ProblemCategory(str, Enum):
    education = "education"
    agriculture = "agriculture"
    healthcare = "healthcare"
    water_resources = "water_resources"
    environment = "environment"
    energy = "energy"
    urban_development = "urban_development"
    accessibility = "accessibility"
    public_administration = "public_administration"
    rural_livelihoods = "rural_livelihoods"

class InstitutionType(str, Enum):
    university = 'university'
    industry = 'industry'
    startup = 'startup'
    msme = 'msme'
    csr = 'csr'
    research_lab = 'research_lab'

class InstitutionDomain(str, Enum):
    education="education"
    agriculture="agriculture"
    healthcare="healthcare"
    water_resources="water_resources"
    environment = "environment"
    energy = "energy"
    urban_development = "urban_development"
    accessibility = "accessibility"
    public_administration = "public_administration"
    rural_livelihoods = "rural_livelihoods"

class RoutingStatus(str, Enum):
    pending = 'pending'
    accepted = 'accepted'
    declined = 'declined'


class ProjectStage(str, Enum):
    proposed = "proposed"
    active = "active"
    testing = "testing"
    deployed = "deployed"
    completed = "completed"

class ApprovalStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class MilestoneStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"

class PartnershipType(str, Enum):
    mentorship = "mentorship"
    funding = "funding"
    prototyping = "prototyping"
    technology_transfer = "technology_transfer"

class PartnershipStatus(str, Enum):
    requested = "requested"
    accepted = "accepted"
    declined = "declined"



 
