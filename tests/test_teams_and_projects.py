import uuid
import pytest

def test_team_crud_and_validation(client):
    users = client.get('/users').json()
    faculty_user = next((u for u in users if u['role'] == 'faculty'), users[0])
    student_users = [u['id'] for u in users if u['role'] == 'student'][:2]
    if not student_users:
        student_users = [users[0]['id']]

    insts = client.get('/institutions').json()
    inst_id = insts[0]['id']

    probs = client.get('/problems').json()
    prob_id = probs[0]['id']

    # Successful team creation
    team_payload = {
        'problem_id': prob_id,
        'institution_id': inst_id,
        'faculty_mentor_id': faculty_user['id'],
        'member_user_ids': student_users
    }
    res = client.post('/teams', json=team_payload)
    assert res.status_code == 200
    team_data = res.json()
    assert team_data['problem_id'] == prob_id
    assert team_data['institution_id'] == inst_id
    assert team_data['faculty_mentor_id'] == faculty_user['id']
    team_id = team_data['id']

    # Get team by id
    get_res = client.get(f'/teams/{team_id}')
    assert get_res.status_code == 200
    assert get_res.json()['id'] == team_id

    # List teams
    list_res = client.get('/teams')
    assert list_res.status_code == 200
    assert any(t['id'] == team_id for t in list_res.json())

    # Validation: invalid problem
    err_prob = client.post('/teams', json={**team_payload, 'problem_id': 99999999})
    assert err_prob.status_code == 404

    # Validation: invalid institution
    err_inst = client.post('/teams', json={**team_payload, 'institution_id': 99999999})
    assert err_inst.status_code == 404

    # Validation: invalid mentor
    err_mentor = client.post('/teams', json={**team_payload, 'faculty_mentor_id': 99999999})
    assert err_mentor.status_code == 404

    # Validation: invalid member
    err_mem = client.post('/teams', json={**team_payload, 'member_user_ids': [99999999]})
    assert err_mem.status_code == 404


def test_project_lifecycle_and_approval(client):
    # Use seeded project or create one
    projects = client.get('/projects').json()
    assert len(projects) >= 1
    project = projects[0]
    project_id = project['id']

    # Get project by ID
    get_p = client.get(f'/projects/{project_id}')
    assert get_p.status_code == 200
    assert get_p.json()['id'] == project_id

    # Non-existent project
    err_p = client.get('/projects/99999999')
    assert err_p.status_code == 404

    # Update project stage to testing
    stage_res = client.patch(f'/projects/{project_id}/stage', json={'stage': 'testing'})
    assert stage_res.status_code == 200
    assert stage_res.json()['stage'] == 'testing'

    # Update project stage to deployed
    stage_res2 = client.patch(f'/projects/{project_id}/stage', json={'stage': 'deployed'})
    assert stage_res2.status_code == 200
    assert stage_res2.json()['stage'] == 'deployed'

    # Approve project with admin user
    users = client.get('/users').json()
    admin_user = next((u for u in users if u['role'] == 'gov_admin'), users[0])
    app_res = client.patch(f'/projects/{project_id}/approve', json={
        'approval_status': 'approved',
        'approved_by_user_id': admin_user['id']
    })
    assert app_res.status_code == 200
    assert app_res.json()['approval_status'] == 'approved'
    assert app_res.json()['approved_by_user_id'] == admin_user['id']

    # Approve with invalid admin ID -> 404
    err_app = client.patch(f'/projects/{project_id}/approve', json={
        'approval_status': 'approved',
        'approved_by_user_id': 99999999
    })
    assert err_app.status_code == 404
