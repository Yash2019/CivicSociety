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