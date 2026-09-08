const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');

export type Json = Record<string, unknown>;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = body && typeof body === 'object' && 'detail' in body ? String(body.detail) : `Request failed (${response.status})`;
    throw new Error(detail);
  }
  return body as T;
}

export interface Problem { id: number; title: string | null; description: string; priority_score: number | null; submitter_type: string; district: string; latitude: number; longitude: number; category: string | null; status: string | null; duplicate_problem: number | null; submitted_by: number | null; }
export interface Institution { id: number; name: string; type: string; domain: string | null; domains: string[]; district: string; has_incubation: boolean; }
export interface Routing { routing_id: number; routing_status: string; matched_reason: string; problem: Problem; }
export interface Project { id: number; team_id: number; problem_id: number; title: string; proposal_text: string; stage: string; approval_status: string; approved_by_user_id: number | null; created_at: string; }
export interface Milestone { id: number; project_id: number; title: string; description: string | null; due_date: string | null; status: string; completed_at: string | null; }
export interface Outcome { id: number; project_id: number; patents_filed: number; startups_created: number; ip_generated: string | null; impact_notes: string | null; }
export interface Partnership { id: number; project_id: number; industry_institution_id: number; partnership_type: string; status: string; notes: string | null; created_at: string; }
export interface Message { id: number; project_id: number; sender_user_id: number; sender_name: string | null; message_text: string; created_at: string; }
export interface Dashboard { total_problems: number; problems_by_status: Record<string, number>; problems_by_category: Record<string, number>; problems_by_district: Record<string, number>; problems_by_submitter_type: Record<string, number>; total_projects: number; projects_by_stage: Record<string, number>; completion_rate: number; total_patents: number; total_startups: number; active_industry_partnerships: number; partnerships_by_type: Record<string, number>; participating_institutions_count: number; }

export const api = {
  baseUrl: API_BASE_URL,
  problems: () => request<Problem[]>('/problems'),
  submitProblem: (data: FormData) => request<Problem>('/problems', { method: 'POST', body: data }),
  institutions: () => request<Institution[]>('/institutions'),
  institutionProblems: (id: number) => request<Routing[]>(`/institutions/${id}/problems`),
  institutionPartnerships: (id: number) => request<Partnership[]>(`/institutions/${id}/partnerships`),
  createInstitution: (data: Json) => request<Institution>('/institutions', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }),
  projects: () => request<Project[]>('/projects'),
  projectMilestones: (id: number) => request<Milestone[]>(`/projects/${id}/milestones`),
  projectOutcomes: (id: number) => request<Outcome>(`/projects/${id}/outcomes`),
  projectPartnerships: (id: number) => request<Partnership[]>(`/projects/${id}/partnerships`),
  requestPartnership: (id: number, data: Json) => request<Partnership>(`/projects/${id}/partnerships`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }),
  projectMessages: (id: number) => request<Message[]>(`/projects/${id}/messages`),
  acceptRouting: (id: number) => request<Routing>(`/routings/${id}/accept`, { method: 'POST' }),
  declineRouting: (id: number) => request<Routing>(`/routings/${id}/decline`, { method: 'POST' }),
  approveProject: (id: number, approval_status: 'approved' | 'rejected', approved_by_user_id: number) => request<Project>(`/projects/${id}/approve`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ approval_status, approved_by_user_id }) }),
  dashboard: () => request<Dashboard>('/dashboard'),
};
