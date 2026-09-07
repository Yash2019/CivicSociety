# Societal Innovation Collaboration Portal — Build Plan

Stack: FastAPI (backend) + PostgreSQL + HTML/CSS/JS (frontend)

---

## 1. Requirement → Feature Traceability

I re-read the problem statement line by line. Here's every bullet from "Expected Solution," mapped to what I'm actually building, so nothing gets missed.

| Problem statement requirement | What covers it in this plan |
|---|---|
| Citizens/community groups/PRIs/ULBs/govt depts submit challenges | `problems` table + `submitter_type` field distinguishing individual vs PRI vs ULB vs govt dept |
| Multimedia evidence, geo location, supporting docs | `problem_media` table (photo/video/document) + `latitude`/`longitude`/`district` on `problems` |
| AI-enabled auto-categorization | `classify_problem()` service — keyword-based first, swappable for LLM call |
| Prioritization | `priority_score` field on `problems`, computed from a simple rule (e.g. submitter type weight + votes/upvotes if you add them) |
| Deduplication | `duplicate_of_problem_id` field + a `find_duplicates()` service using text similarity against recent same-category problems |
| Routing to universities by expertise/incubation/faculty specialization | `routings` table + `route_problem()` matching `institution.domains` to `problem.category` |
| University reviews challenges | `GET /institutions/{id}/problems` (via routings) |
| Multidisciplinary team formation | `teams` + `team_members` (multiple users per team, no discipline restriction) |
| Faculty mentor assignment | `faculty_mentor_id` on `teams` |
| Project workflow management | `projects.stage` state machine (proposed → active → testing → deployed → completed) |
| Solution proposal submission | `projects` created from an accepted routing, with a description/proposal field |
| Industry/startup/MSME/CSR/research lab participation | `industry_partnerships` table with `partnership_type` (mentorship/funding/prototyping/technology_transfer) |
| Mentorship, co-development, funding, prototyping, technology transfer | Covered by `partnership_type` enum above — each is just a type + status, not separate systems |
| Milestone/deliverable tracking | `milestones` table linked to `projects` |
| Approvals | `approval_status` field on `projects` (pending/approved/rejected) + `approved_by_user_id` |
| Documentation | `deliverables` table storing file URLs against a project/milestone |
| Testing outcomes, implementation status | Captured as project `stage` transitions + notes field on milestones |
| IP generation, patents, startups created | `project_outcomes` table (patents_filed, startups_created, ip_generated) |
| Dashboard: submissions, participation, thematic trends, completion rates, outcomes, district-wise impact | `GET /dashboard` — aggregate SQL queries grouped by category, district, stage, institution |
| Notification/communication system across all stakeholders | `notifications` table (system-generated, one-way) + `messages` table (project-level comments/threads, two-way) |

Nothing in the "Expected Solution" section is left unmapped. Two things are explicitly **simplified for a working demo rather than skipped**, noted honestly below so you can say this to judges instead of getting caught off guard.

### What's real vs. simplified (say this upfront, don't let judges "catch" it)
- **"AI-enabled classification/dedup"** — real logic (keyword rules + text similarity), not a trained ML model. This is a legitimate engineering choice for an MVP and is easy to defend: "rule-based now, designed so the classifier function can be swapped for a trained model without touching the rest of the system."
- **Notifications are in-app, not SMS/WhatsApp/email** — same reasoning: the `notifications` table is provider-agnostic, so adding a real channel later is a service swap, not a redesign.

---

## 2. Database Schema

```
users
  id, name, email, password_hash, role
    role ∈ {citizen, pri_ulb, govt_dept, university_admin, faculty, industry, gov_admin}
  institution_id (nullable, FK -> institutions)
  created_at

institutions
  id, name, type
    type ∈ {university, industry, startup, msme, csr, research_lab}
  domains (text[] — e.g. ["agriculture","water"])
  district
  has_incubation_center (bool)
  created_at

problems
  id, title, description, category, priority_score
  submitted_by_user_id (FK -> users)
  submitter_type ∈ {individual, community_org, pri, ulb, govt_dept}
  district, latitude, longitude
  status ∈ {submitted, under_review, routed, rejected, duplicate}
  duplicate_of_problem_id (nullable, FK -> problems)
  created_at

problem_media
  id, problem_id (FK), file_url, media_type ∈ {photo, video, document}

routings
  id, problem_id (FK), institution_id (FK)
  matched_reason (text — why this institution was picked)
  status ∈ {pending, accepted, declined}
  created_at

teams
  id, problem_id (FK), institution_id (FK), faculty_mentor_id (FK -> users)
  created_at

team_members
  team_id (FK), user_id (FK)

projects
  id, team_id (FK), problem_id (FK), title, proposal_text
  stage ∈ {proposed, active, testing, deployed, completed}
  approval_status ∈ {pending, approved, rejected}
  approved_by_user_id (nullable, FK -> users)
  created_at

milestones
  id, project_id (FK), title, description, due_date
  status ∈ {pending, in_progress, completed}
  completed_at

deliverables
  id, project_id (FK), milestone_id (nullable, FK), file_url, doc_type

project_outcomes
  id, project_id (FK, one-to-one)
  patents_filed (int), startups_created (int), ip_generated (text), impact_notes (text)

industry_partnerships
  id, project_id (FK), industry_institution_id (FK)
  partnership_type ∈ {mentorship, funding, prototyping, technology_transfer}
  status ∈ {requested, accepted, declined}
  created_at

messages
  id, project_id (FK), sender_user_id (FK), message_text, created_at

notifications
  id, user_id (FK), message, related_entity_type, related_entity_id
  read (bool), created_at
```

---

## 3. Build Order

Build in this order — each phase is independently testable and depends only on what came before.

**Phase 1 — Foundation**
- FastAPI project structure: `routers/`, `models/`, `schemas/`, `services/`
- Postgres connection, all tables above as SQLAlchemy models, Alembic migrations
- Seed script: fake institutions across categories/districts

**Phase 2 — Auth**
- `/signup`, `/login` (JWT), role stored on signup
- `require_role()` FastAPI dependency for locking routes by role

**Phase 3 — Problem submission (citizen side)**
- `POST /problems` (title, description, submitter_type, district, lat/long)
- File upload endpoint for `problem_media` (store to disk/S3, save URL)
- `classify_problem(text) -> category` — keyword-based rules
- `find_duplicates(problem)` — text similarity (TF-IDF cosine or simple keyword overlap) against recent same-category problems; flag as `duplicate` if above threshold
- `compute_priority(problem)` — simple weighted score (submitter_type weight + recency)
- `GET /problems` (citizen sees own submissions)

**Phase 4 — Routing**
- `route_problem(problem)` — match `institution.domains` to `problem.category`, create `routings` rows
- `GET /institutions/{id}/problems` (university sees routed problems)
- `POST /routings/{id}/accept` / `/decline`

**Phase 5 — Teams and projects**
- `POST /teams` (add members, assign faculty mentor)
- `POST /projects` (from accepted routing, includes proposal_text)
- `PATCH /projects/{id}/stage`
- `PATCH /projects/{id}/approve` (gov_admin role only)

**Phase 6 — Milestones and deliverables**
- `POST /projects/{id}/milestones`
- `PATCH /milestones/{id}` (status updates)
- `POST /projects/{id}/deliverables` (file upload)
- `POST /projects/{id}/outcomes` (patents, startups, IP — update as project matures)

**Phase 7 — Industry partnerships**
- `GET /projects` (industry browses active projects)
- `POST /projects/{id}/partnerships` (request to join, with type)
- `PATCH /partnerships/{id}` (university accepts/declines)

**Phase 8 — Dashboard**
- `GET /dashboard` — aggregate queries:
  - problems by category, by district, by status
  - projects by stage
  - institution participation counts
  - industry partnership counts by type
  - total patents/startups from `project_outcomes`

**Phase 9 — Communication**
- `POST /projects/{id}/messages`, `GET /projects/{id}/messages` (thread per project)
- Trigger `notifications` rows on: routing created, routing accepted, project stage change, partnership request, milestone completed
- `GET /notifications`, `PATCH /notifications/{id}/read`

**Phase 10 — Frontend wiring**
- Plain JS `fetch()` wrapper with JWT attached
- One page per role dashboard (citizen / university / industry / gov_admin) — don't build one giant page, keep role views separate so permissions stay obvious in the UI too

---

## 4. Folder Structure

```
app/
  main.py
  database.py
  models/
    user.py, institution.py, problem.py, routing.py,
    team.py, project.py, milestone.py, partnership.py, notification.py
  schemas/
    (mirrors models/, input + output schemas separated)
  routers/
    auth.py, problems.py, routings.py, teams.py, projects.py,
    partnerships.py, dashboard.py, notifications.py
  services/
    classification.py   # classify_problem, find_duplicates
    priority.py          # compute_priority
    routing.py            # route_problem
    notify.py             # helper to create notification rows
  dependencies/
    auth.py               # require_role, get_current_user
```
