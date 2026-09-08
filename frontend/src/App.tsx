import { FormEvent, useEffect, useMemo, useState } from 'react';
import { api, Dashboard, Institution, Message, Milestone, Outcome, Partnership, Problem, Project, Routing, Team, User } from './services/api';

type View = 'citizen' | 'institutions' | 'projects' | 'teams' | 'dashboard' | 'industry' | 'government';
type RoutedOpportunity = Routing & { institution_id: number };
const categories = [['water_resources', 'Water and sanitation'], ['agriculture', 'Agriculture'], ['healthcare', 'Healthcare'], ['environment', 'Environment'], ['energy', 'Energy'], ['urban_development', 'Urban development'], ['education', 'Education'], ['accessibility', 'Accessibility'], ['public_administration', 'Public administration'], ['rural_livelihoods', 'Rural livelihoods']];

function dateText(value?: string | null) { return value ? new Date(value).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) : '—'; }
function label(value?: string | null) { return (value || 'not available').replaceAll('_', ' '); }

export default function App() {
  const [view, setView] = useState<View>('citizen');
  const [problems, setProblems] = useState<Problem[]>([]);
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [opportunities, setOpportunities] = useState<RoutedOpportunity[]>([]);
  const [selectedInstitution, setSelectedInstitution] = useState<number | ''>('');
  const [routings, setRoutings] = useState<Routing[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [projectData, setProjectData] = useState<{ milestones: Milestone[]; outcome: Outcome | null; partnerships: Partnership[]; messages: Message[] }>({ milestones: [], outcome: null, partnerships: [], messages: [] });
  const [query, setQuery] = useState('');
  const [notice, setNotice] = useState<{ kind: 'error' | 'success'; text: string } | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = async () => {
    setLoading(true); setNotice(null);
    try {
      const [p, i, pr, d, u, t] = await Promise.all([api.problems(), api.institutions(), api.projects(), api.dashboard(), api.users(), api.teams()]);
      let availableUsers = u;
      // Prototype convenience: keep the approval workflow usable even when
      // a deployment was not seeded with a government administrator.
      if (!availableUsers.some((user) => user.role === 'gov_admin')) {
        try {
          const demoAdmin = await api.createUser({ name: 'District Innovation Officer', email: 'admin.gov@prototype.local', role: 'gov_admin', institution_id: null });
          availableUsers = [...availableUsers, demoAdmin];
        } catch { /* an existing database may reject the placeholder email */ }
      }
      const routed = (await Promise.all(i.map(async (institution) => {
        try { return (await api.institutionProblems(institution.id)).map((item) => ({ ...item, institution_id: institution.id })); }
        catch { return []; }
      }))).flat().filter((item) => item.routing_status === 'accepted');
      setProblems(p); setInstitutions(i); setProjects(pr); setDashboard(d); setUsers(availableUsers); setTeams(t); setOpportunities(routed);
      if (!selectedInstitution && i[0]) setSelectedInstitution(i[0].id);
    } catch (error) { setNotice({ kind: 'error', text: error instanceof Error ? error.message : 'Unable to connect to the civic service.' }); }
    finally { setLoading(false); }
  };
  useEffect(() => { void refresh(); }, []);
  useEffect(() => {
    if (!selectedInstitution) { setRoutings([]); return; }
    api.institutionProblems(Number(selectedInstitution)).then(setRoutings).catch((e) => setNotice({ kind: 'error', text: e.message }));
  }, [selectedInstitution]);
  useEffect(() => {
    if (!selectedProject) return;
    Promise.all([api.projectMilestones(selectedProject.id), api.projectOutcomes(selectedProject.id), api.projectPartnerships(selectedProject.id), api.projectMessages(selectedProject.id)])
      .then(([milestones, outcome, partnerships, messages]) => setProjectData({ milestones, outcome, partnerships, messages }))
      .catch((e) => setNotice({ kind: 'error', text: e.message }));
  }, [selectedProject]);

  const filteredProblems = useMemo(() => problems.filter((p) => `${p.title} ${p.description} ${p.district} ${p.category}`.toLowerCase().includes(query.toLowerCase())), [problems, query]);
  const actOnRouting = async (routing: Routing, action: 'accept' | 'decline') => {
    try { await (action === 'accept' ? api.acceptRouting(routing.routing_id) : api.declineRouting(routing.routing_id)); setRoutings((items) => items.map((item) => item.routing_id === routing.routing_id ? { ...item, routing_status: action === 'accept' ? 'accepted' : 'declined' } : item)); setNotice({ kind: 'success', text: `Routing ${action}ed.` }); }
    catch (e) { setNotice({ kind: 'error', text: e instanceof Error ? e.message : 'Action failed.' }); }
  };

  return <div className="site-shell">
    <header className="gov-header">
      <div className="gov-strip"><span>Government of Jharkhand</span><span>Citizen Innovation and Solutions Portal</span></div>
      <div className="brand-row"><button className="brand" onClick={() => setView('citizen')}><span className="seal">◆</span><span><strong>Nagar Sahayak</strong><small>Community problem solving platform</small></span></button><div className="header-actions"><span className="api-status"><i /> Connected to civic service</span><button className="outline-button" onClick={() => void refresh()}>Refresh</button></div></div>
      <nav className="main-nav" aria-label="Main navigation">{([['citizen', 'Citizen services'], ['institutions', 'Institutions'], ['projects', 'Projects'], ['teams', 'Teams & proposals'], ['dashboard', 'Public dashboard'], ['industry', 'Industry workspace'], ['government', 'Government workspace']] as [View, string][]).map(([id, text]) => <button key={id} className={view === id ? 'active' : ''} onClick={() => setView(id)}>{text}</button>)}</nav>
    </header>
    <main className="page-content">
      {notice && <div className={`notice ${notice.kind}`} role="alert">{notice.text}<button onClick={() => setNotice(null)}>Dismiss</button></div>}
      {loading && <div className="loading-bar" />}
      {view === 'citizen' && <CitizenView problems={filteredProblems} query={query} setQuery={setQuery} onSubmitted={(p) => { setProblems((items) => [p, ...items]); setNotice({ kind: 'success', text: `Problem registered as CH-${p.id}.` }); }} />}
      {view === 'institutions' && <InstitutionView institutions={institutions} selected={selectedInstitution} setSelected={setSelectedInstitution} routings={routings} onAction={actOnRouting} onRegistered={(i) => setInstitutions((items) => [i, ...items])} />}
      {view === 'projects' && <ProjectsView projects={projects} selected={selectedProject} setSelected={setSelectedProject} data={projectData} />}
      {view === 'teams' && <TeamsView users={users} institutions={institutions} opportunities={opportunities} teams={teams} onUserCreated={(user) => setUsers((items) => [...items, user])} onCreated={(team, project) => { setTeams((items) => [team, ...items]); setProjects((items) => [project, ...items]); setView('projects'); setNotice({ kind: 'success', text: `Proposal ${project.title} submitted for government review.` }); }} />}
      {view === 'dashboard' && <DashboardView dashboard={dashboard} />}
      {view === 'industry' && <IndustryView institutions={institutions} projects={projects} />}
      {view === 'government' && <GovernmentView dashboard={dashboard} projects={projects} users={users} onApproved={(p) => setProjects((items) => items.map((item) => item.id === p.id ? p : item))} />}
    </main>
    <footer className="site-footer"><span>© {new Date().getFullYear()} Government of Jharkhand · Nagar Sahayak</span><span>For assistance, contact your district administration.</span></footer>
  </div>;
}

function CitizenView({ problems, query, setQuery, onSubmitted }: { problems: Problem[]; query: string; setQuery: (v: string) => void; onSubmitted: (p: Problem) => void }) {
  const [form, setForm] = useState({ title: '', description: '', category: 'water_resources', submitter_type: 'individual', district: 'Ranchi', latitude: '23.3441', longitude: '85.3096' });
  const [photo, setPhoto] = useState<File | null>(null); const [busy, setBusy] = useState(false); const [error, setError] = useState('');
  const update = (key: string, value: string) => setForm((f) => ({ ...f, [key]: value }));
  const submit = async (event: FormEvent) => { event.preventDefault(); setError(''); setBusy(true); try { const data = new FormData(); Object.entries(form).forEach(([k, v]) => data.append(k, String(v))); if (photo) data.append('photo', photo); onSubmitted(await api.submitProblem(data)); setForm({ ...form, title: '', description: '' }); setPhoto(null); } catch (e) { setError(e instanceof Error ? e.message : 'Unable to register problem.'); } finally { setBusy(false); } };
  return <><section className="page-intro"><div><p className="eyebrow">Citizen service</p><h1>Report a problem in your community</h1><p>Submit a clear description. The service classifies the issue, assigns a priority, and routes it to relevant institutions.</p></div><div className="intro-note"><strong>Already registered a problem?</strong><span>Use the search below to find its current status.</span></div></section>
    <div className="two-column"><form className="panel form-panel" onSubmit={submit}><div className="panel-heading"><h2>New problem report</h2><span>All fields marked * are required</span></div>{error && <div className="field-error">{error}</div>}<label>Short title *<input required minLength={3} maxLength={255} value={form.title} onChange={(e) => update('title', e.target.value)} placeholder="For example: Handpump not working" /></label><label>Description *<textarea required minLength={10} maxLength={10000} value={form.description} onChange={(e) => update('description', e.target.value)} placeholder="Describe what is happening, where, and who is affected." rows={5} /></label><div className="form-grid"><label>Category<select value={form.category} onChange={(e) => update('category', e.target.value)}>{categories.map(([value, text]) => <option value={value} key={value}>{text}</option>)}</select></label><label>Submitted by<select value={form.submitter_type} onChange={(e) => update('submitter_type', e.target.value)}><option value="individual">Individual citizen</option><option value="community_org">Community organisation</option><option value="pri">Gram Panchayat / PRI</option><option value="ulb">Urban local body</option><option value="govt_dept">Government department</option></select></label></div><div className="form-grid"><label>District *<input required value={form.district} onChange={(e) => update('district', e.target.value)} /></label><label>Photo evidence<input type="file" accept=".png,.jpg,.jpeg,.webp" onChange={(e) => setPhoto(e.target.files?.[0] || null)} /></label></div><details><summary>Location coordinates</summary><div className="form-grid"><label>Latitude<input required type="number" step="any" min="-90" max="90" value={form.latitude} onChange={(e) => update('latitude', e.target.value)} /></label><label>Longitude<input required type="number" step="any" min="-180" max="180" value={form.longitude} onChange={(e) => update('longitude', e.target.value)} /></label></div></details><button className="primary-button" disabled={busy}>{busy ? 'Registering…' : 'Register problem'}</button></form>
      <section className="panel"><div className="panel-heading"><h2>Registered problems</h2><span>{problems.length} records</span></div><input className="search-input" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search by title, district or category" />{problems.length === 0 ? <Empty text="No problems have been registered yet." /> : <div className="record-list">{problems.map((p) => <article className="record" key={p.id}><div className="record-top"><span className="record-code">CH-{p.id}</span><span className={`status status-${p.status}`}>{label(p.status)}</span></div><h3>{p.title || 'Untitled problem'}</h3><p>{p.description}</p><div className="record-meta"><span>{p.district}</span><span>{label(p.category)}</span><span>Priority {p.priority_score ?? '—'}</span></div></article>)}</div>}</section></div></>;
}

function InstitutionView({ institutions, selected, setSelected, routings, onAction, onRegistered }: { institutions: Institution[]; selected: number | ''; setSelected: (v: number) => void; routings: Routing[]; onAction: (r: Routing, action: 'accept' | 'decline') => void; onRegistered: (i: Institution) => void }) {
  const [showForm, setShowForm] = useState(false); const [name, setName] = useState(''); const [district, setDistrict] = useState('Ranchi'); const [type, setType] = useState('university'); const [domain, setDomain] = useState('water_resources'); const [partnerships, setPartnerships] = useState<Partnership[]>([]); const [partnershipError, setPartnershipError] = useState('');
  useEffect(() => { if (!selected) { setPartnerships([]); return; } api.institutionPartnerships(Number(selected)).then(setPartnerships).catch(() => setPartnerships([])); }, [selected]);
  const decidePartnership = async (partnership: Partnership, status: 'accepted' | 'declined') => { setPartnershipError(''); try { const updated = await api.updatePartnershipStatus(partnership.id, status); setPartnerships((items) => items.map((item) => item.id === updated.id ? updated : item)); } catch (e) { setPartnershipError(e instanceof Error ? e.message : 'Unable to update partnership.'); } };
  const register = async (e: FormEvent) => { e.preventDefault(); try { const i = await api.createInstitution({ name, district, type, domain, domains: [domain], has_incubation: false }); onRegistered(i); setShowForm(false); setName(''); } catch { /* parent refresh exposes API failures */ } };
  return <><section className="page-intro"><div><p className="eyebrow">Institution workspace</p><h1>Review routed community problems</h1><p>Institutions can review domain-matched submissions and respond to industry partnership requests.</p></div><button className="primary-button compact" onClick={() => setShowForm(!showForm)}>Register institution</button></section>{showForm && <form className="panel inline-form" onSubmit={register}><label>Name<input required value={name} onChange={(e) => setName(e.target.value)} /></label><label>Type<select value={type} onChange={(e) => setType(e.target.value)}><option value="university">University</option><option value="research_lab">Research lab</option><option value="industry">Industry</option><option value="startup">Startup</option><option value="msme">MSME</option><option value="csr">CSR organisation</option></select></label><label>District<input required value={district} onChange={(e) => setDistrict(e.target.value)} /></label><label>Primary domain<select value={domain} onChange={(e) => setDomain(e.target.value)}>{categories.map(([v, t]) => <option key={v} value={v}>{t}</option>)}</select></label><button className="primary-button">Save institution</button></form>}<section className="panel"><div className="toolbar"><label className="select-label">Institution<select value={selected} onChange={(e) => setSelected(Number(e.target.value))}><option value="">Select an institution</option>{institutions.map((i) => <option key={i.id} value={i.id}>{i.name} · {label(i.type)}</option>)}</select></label><span>{routings.length} routed records</span></div>{routings.length === 0 ? <Empty text="Choose an institution to view its routed problems." /> : <div className="record-list">{routings.map((r) => <article className="routing-card" key={r.routing_id}><div><span className="record-code">Routing #{r.routing_id}</span><span className={`status status-${r.routing_status}`}>{label(r.routing_status)}</span><h3>{r.problem.title}</h3><p>{r.problem.description}</p><small>{r.problem.district} · {label(r.problem.category)} · {r.matched_reason}</small></div><div className="action-row">{r.routing_status === 'pending' && <><button className="small-button accept" onClick={() => onAction(r, 'accept')}>Accept</button><button className="small-button decline" onClick={() => onAction(r, 'decline')}>Decline</button></>}</div></article>)}</div>}</section><section className="panel"><div className="panel-heading"><h2>Industry partnership requests</h2><span>{partnerships.length} requests</span></div>{partnershipError && <div className="field-error">{partnershipError}</div>}{partnerships.length === 0 ? <Empty text="No partnership requests for this institution." /> : <div className="record-list">{partnerships.map((partnership) => <article className="routing-card" key={partnership.id}><div><span className="record-code">Project #{partnership.project_id}</span><h3>{label(partnership.partnership_type)}</h3><p>{partnership.notes || 'No additional notes.'}</p><span className={`status status-${partnership.status}`}>{label(partnership.status)}</span></div>{partnership.status === 'requested' && <div className="action-row"><button className="small-button accept" onClick={() => decidePartnership(partnership, 'accepted')}>Accept</button><button className="small-button decline" onClick={() => decidePartnership(partnership, 'declined')}>Decline</button></div>}</article>)}</div>}</section></>;
}

function TeamsView({ users, institutions, opportunities, teams, onUserCreated, onCreated }: { users: User[]; institutions: Institution[]; opportunities: RoutedOpportunity[]; teams: Team[]; onUserCreated: (user: User) => void; onCreated: (team: Team, project: Project) => void }) {
  const [opportunityId, setOpportunityId] = useState('');
  const [facultyId, setFacultyId] = useState('');
  const [memberIds, setMemberIds] = useState<number[]>([]);
  const [title, setTitle] = useState('');
  const [proposal, setProposal] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [participantName, setParticipantName] = useState('');
  const [participantRole, setParticipantRole] = useState<'faculty' | 'student'>('faculty');
  const [participantError, setParticipantError] = useState('');
  const opportunity = opportunities.find((item) => String(item.routing_id) === opportunityId);
  const faculty = users.filter((user) => user.role === 'faculty' && (!opportunity || user.institution_id === opportunity.institution_id));
  const students = users.filter((user) => user.role === 'student');
  const existingProblemIds = new Set(teams.map((team) => team.problem_id));
  const available = opportunities.filter((item) => !existingProblemIds.has(item.problem.id));
  const toggleMember = (id: number) => setMemberIds((items) => items.includes(id) ? items.filter((item) => item !== id) : [...items, id]);
  const submit = async (event: FormEvent) => {
    event.preventDefault(); setError(''); setBusy(true);
    try {
      if (!opportunity || !facultyId) throw new Error('Choose an accepted problem and a faculty mentor.');
      const team = await api.createTeam({ problem_id: opportunity.problem.id, institution_id: opportunity.institution_id, faculty_mentor_id: Number(facultyId), member_user_ids: memberIds });
      const project = await api.createProject({ team_id: team.id, problem_id: opportunity.problem.id, title, proposal_text: proposal });
      onCreated(team, project);
    } catch (e) { setError(e instanceof Error ? e.message : 'Unable to submit the proposal.'); }
    finally { setBusy(false); }
  };
  const addParticipant = async (event: FormEvent) => {
    event.preventDefault(); setParticipantError('');
    try {
      if (!participantName.trim()) throw new Error('Enter a participant name.');
      const suffix = `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
      const user = await api.createUser({ name: participantName.trim(), role: participantRole, institution_id: opportunity?.institution_id || null, email: `${participantRole}-${suffix}@prototype.local` });
      onUserCreated(user); setParticipantName('');
    } catch (e) { setParticipantError(e instanceof Error ? e.message : 'Unable to add participant.'); }
  };
  return <><section className="page-intro"><div><p className="eyebrow">University workspace</p><h1>Form a team and propose a solution</h1><p>Select an accepted community problem, add a faculty mentor and student members, then submit a proposal for government review.</p></div></section>
    <section className="panel"><div className="panel-heading"><h2>Prototype participant setup</h2><span>No login or verification is used</span></div><p className="muted">Add a faculty mentor or student for this demonstration. Email is generated internally and is not shown.</p><form className="inline-form" onSubmit={addParticipant}><label>Name<input required value={participantName} onChange={(e) => setParticipantName(e.target.value)} placeholder="Participant name" /></label><label>Role<select value={participantRole} onChange={(e) => setParticipantRole(e.target.value as 'faculty' | 'student')}><option value="faculty">Faculty mentor</option><option value="student">Student member</option></select></label><button className="primary-button compact">Add participant</button></form>{participantError && <div className="field-error">{participantError}</div>}</section>
    <form className="panel form-panel proposal-form" onSubmit={submit}><div className="panel-heading"><h2>New solution proposal</h2><span>Only accepted institution routings are eligible</span></div>{error && <div className="field-error">{error}</div>}
      {available.length === 0 ? <div className="empty-state">No accepted problems are waiting for a team. An institution must accept a routed problem first.</div> : <>
        <label>Accepted problem *<select required value={opportunityId} onChange={(e) => { setOpportunityId(e.target.value); setFacultyId(''); }}><option value="">Choose a problem</option>{available.map((item) => <option value={item.routing_id} key={item.routing_id}>CH-{item.problem.id}: {item.problem.title} · {label(item.problem.category)} · {item.problem.district}</option>)}</select></label>
        {opportunity && <div className="selected-record"><strong>CH-{opportunity.problem.id}: {opportunity.problem.title}</strong><p>{opportunity.problem.description}</p><small>{label(opportunity.problem.category)} · {opportunity.problem.district} · {opportunity.matched_reason}</small></div>}
        <label>Faculty mentor *<select required value={facultyId} onChange={(e) => setFacultyId(e.target.value)}><option value="">Choose a faculty mentor</option>{faculty.map((user) => <option value={user.id} key={user.id}>{user.name} (User #{user.id})</option>)}</select></label>
        <fieldset><legend>Student members</legend>{students.length ? <div className="member-grid">{students.map((user) => <label key={user.id}><input type="checkbox" checked={memberIds.includes(user.id)} onChange={() => toggleMember(user.id)} />{user.name} (User #{user.id})</label>)}</div> : <small>No student users are registered yet. You can still submit with a faculty mentor.</small>}</fieldset>
        <label>Proposal title *<input required minLength={3} maxLength={255} value={title} onChange={(e) => setTitle(e.target.value)} placeholder="For example: Low-cost solar water pump monitoring system" /></label>
        <label>Proposal description *<textarea required minLength={20} maxLength={20000} rows={7} value={proposal} onChange={(e) => setProposal(e.target.value)} placeholder="Explain the proposed solution, its users, and how it addresses the accepted problem." /></label>
        <button className="primary-button" disabled={busy}>{busy ? 'Submitting…' : 'Create team and submit proposal'}</button>
      </>}
    </form></>;
}

function ProjectsView({ projects, selected, setSelected, data }: { projects: Project[]; selected: Project | null; setSelected: (p: Project | null) => void; data: { milestones: Milestone[]; outcome: Outcome | null; partnerships: Partnership[]; messages: Message[] } }) { return <><section className="page-intro"><div><p className="eyebrow">Project workspace</p><h1>Solutions in progress</h1><p>Follow approved proposals from active work through testing, deployment, and completion.</p></div></section><div className="two-column projects-layout"><section className="panel"><div className="panel-heading"><h2>Projects</h2><span>{projects.length} records</span></div>{projects.length === 0 ? <Empty text="No projects are available." /> : <div className="record-list">{projects.map((p) => <button className={`project-row ${selected?.id === p.id ? 'selected' : ''}`} key={p.id} onClick={() => setSelected(p)}><span className="record-code">PRJ-{p.id}</span><strong>{p.title}</strong><span>{label(p.stage)} · {label(p.approval_status)}</span></button>)}</div>}</section>{selected ? <section className="panel project-detail"><div className="panel-heading"><div><span className="record-code">PRJ-{selected.id}</span><h2>{selected.title}</h2></div><span className={`status status-${selected.stage}`}>{label(selected.stage)}</span></div><p>{selected.proposal_text}</p><h3>Milestones</h3>{data.milestones.length ? data.milestones.map((m) => <div className="detail-line" key={m.id}><span>{m.title}</span><span>{label(m.status)} · {dateText(m.due_date)}</span></div>) : <Empty text="No milestones recorded." />}<h3>Outcome</h3>{data.outcome ? <div className="metric-row"><b>{data.outcome.patents_filed} patents</b><b>{data.outcome.startups_created} startups</b><span>{data.outcome.impact_notes || 'Impact notes not recorded.'}</span></div> : <Empty text="No outcome recorded." />}<h3>Collaboration</h3><p>{data.partnerships.length} partnership requests · {data.messages.length} project messages</p></section> : <section className="panel"><Empty text="Select a project to view its milestones, outcomes, partnerships, and messages." /></section>}</div></>; }

function IndustryView({ institutions, projects }: { institutions: Institution[]; projects: Project[] }) {
  const eligible = institutions.filter((i) => ['industry', 'startup', 'msme', 'csr', 'research_lab'].includes(i.type));
  const [institutionId, setInstitutionId] = useState<number | ''>(eligible[0]?.id || '');
  const [partnerships, setPartnerships] = useState<Partnership[]>([]);
  const [selectedProject, setSelectedProject] = useState<number | ''>('');
  const [type, setType] = useState('funding'); const [message, setMessage] = useState('');
  useEffect(() => { if (institutionId) api.institutionPartnerships(Number(institutionId)).then(setPartnerships).catch(() => setPartnerships([])); }, [institutionId]);
  const submit = async (e: FormEvent) => { e.preventDefault(); if (!institutionId || !selectedProject) return; try { const p = await api.requestPartnership(Number(selectedProject), { industry_institution_id: Number(institutionId), partnership_type: type, notes: message }); setPartnerships((items) => [p, ...items]); setMessage(''); } catch { /* visible list remains unchanged on API failure */ } };
  return <><section className="page-intro"><div><p className="eyebrow">Industry workspace</p><h1>Fund and scale verified projects</h1><p>Review active projects, submit funding or mentorship requests, and monitor your organisation’s partnership requests.</p></div></section><section className="panel"><div className="toolbar"><label className="select-label">Your organisation<select value={institutionId} onChange={(e) => setInstitutionId(Number(e.target.value))}><option value="">Select organisation</option>{eligible.map((i) => <option key={i.id} value={i.id}>{i.name} · {label(i.type)}</option>)}</select></label><span>{partnerships.length} requests</span></div><div className="two-column"><div><h3>Projects open for collaboration</h3><div className="record-list">{projects.filter((p) => ['active', 'testing', 'deployed'].includes(p.stage)).map((p) => <article className="record" key={p.id}><h3>{p.title}</h3><p>{p.proposal_text}</p><span className="status status-active">{label(p.stage)}</span></article>)}</div></div><form className="form-panel" onSubmit={submit}><h3>Request a partnership</h3><label>Project<select required value={selectedProject} onChange={(e) => setSelectedProject(Number(e.target.value))}><option value="">Choose a project</option>{projects.filter((p) => ['active', 'testing', 'deployed'].includes(p.stage)).map((p) => <option key={p.id} value={p.id}>{p.title}</option>)}</select></label><label>Support type<select value={type} onChange={(e) => setType(e.target.value)}><option value="funding">Funding</option><option value="mentorship">Mentorship</option><option value="prototyping">Prototyping</option><option value="technology_transfer">Technology transfer</option></select></label><label>Notes<textarea rows={4} value={message} onChange={(e) => setMessage(e.target.value)} placeholder="Describe the support you can provide." /></label><button className="primary-button">Send request</button></form></div></section><section className="panel"><div className="panel-heading"><h2>Organisation requests</h2></div>{partnerships.length ? <div className="record-list">{partnerships.map((p) => <div className="detail-line" key={p.id}><span>{label(p.partnership_type)}</span><span className={`status status-${p.status}`}>{label(p.status)}</span></div>)}</div> : <Empty text="No partnership requests recorded for this organisation." />}</section></>;
}

function GovernmentView({ dashboard, projects, users, onApproved }: { dashboard: Dashboard | null; projects: Project[]; users: User[]; onApproved: (p: Project) => void }) {
  const admins = users.filter((user) => user.role === 'gov_admin');
  const [adminId, setAdminId] = useState(''); const [error, setError] = useState(''); const pending = projects.filter((p) => p.approval_status === 'pending');
  useEffect(() => { if (!adminId && admins[0]) setAdminId(String(admins[0].id)); }, [admins, adminId]);
  const decide = async (p: Project, status: 'approved' | 'rejected') => { setError(''); if (!adminId) { setError('Select a government administrator first.'); return; } try { onApproved(await api.approveProject(p.id, status, Number(adminId))); } catch (e) { setError(e instanceof Error ? e.message : 'Approval request failed.'); } };
  return <><section className="page-intro"><div><p className="eyebrow">Government workspace</p><h1>Programme oversight</h1><p>Review proposals awaiting approval and monitor delivery across districts. Authentication is not yet implemented, so this prototype uses a seeded government administrator.</p></div></section>{dashboard && <div className="metric-grid">{[['Problems', dashboard.total_problems], ['Projects', dashboard.total_projects], ['Completion', `${dashboard.completion_rate}%`], ['Partnerships', dashboard.active_industry_partnerships], ['Patents', dashboard.total_patents], ['Startups', dashboard.total_startups]].map(([n, v]) => <div className="metric-card" key={String(n)}><span>{n}</span><strong>{v}</strong></div>)}</div>}<section className="panel"><div className="toolbar"><div><h2>Approval queue</h2><span>{pending.length} proposals awaiting decision</span></div><label className="select-label">Government administrator<select value={adminId} onChange={(e) => setAdminId(e.target.value)}><option value="">Select administrator</option>{admins.map((admin) => <option value={admin.id} key={admin.id}>{admin.name} (User #{admin.id})</option>)}</select></label></div>{error && <div className="field-error">{error}</div>}{pending.length ? <div className="record-list">{pending.map((p) => <article className="routing-card" key={p.id}><div><span className="record-code">PRJ-{p.id}</span><h3>{p.title}</h3><p>{p.proposal_text}</p></div><div className="action-row"><button className="small-button accept" disabled={!adminId} onClick={() => decide(p, 'approved')}>Approve & activate</button><button className="small-button decline" disabled={!adminId} onClick={() => decide(p, 'rejected')}>Reject</button></div></article>)}</div> : <Empty text="There are no projects waiting for approval." />}</section></>;
}

function DashboardView({ dashboard }: { dashboard: Dashboard | null }) { if (!dashboard) return <Empty text="Dashboard data is unavailable." />; const cards = [['Total problems', dashboard.total_problems], ['Projects', dashboard.total_projects], ['Completed', `${dashboard.completion_rate}%`], ['Patents filed', dashboard.total_patents], ['Startups', dashboard.total_startups], ['Active partnerships', dashboard.active_industry_partnerships]]; return <><section className="page-intro"><div><p className="eyebrow">Public dashboard</p><h1>Programme activity</h1><p>Aggregated records from the civic innovation service. No figures are estimated on this page.</p></div></section><div className="metric-grid">{cards.map(([name, value]) => <div className="metric-card" key={String(name)}><span>{name}</span><strong>{value}</strong></div>)}</div><div className="two-column"><Distribution title="Problems by district" values={dashboard.problems_by_district} /><Distribution title="Projects by stage" values={dashboard.projects_by_stage} /><Distribution title="Problems by category" values={dashboard.problems_by_category} /><Distribution title="Partnerships by type" values={dashboard.partnerships_by_type} /></div></>; }
function Distribution({ title, values }: { title: string; values: Record<string, number> }) { return <section className="panel"><div className="panel-heading"><h2>{title}</h2></div>{Object.keys(values).length ? <div className="distribution">{Object.entries(values).map(([key, value]) => <div key={key}><span>{label(key)}</span><b>{value}</b><i style={{ width: `${Math.min(100, value * 12)}%` }} /></div>)}</div> : <Empty text="No records." />}</section>; }
function Empty({ text }: { text: string }) { return <div className="empty-state">{text}</div>; }
