import uuid
import pytest

def test_project_discussion_messages(client):
    projects = client.get('/projects').json()
    project_id = projects[0]['id']

    users = client.get('/users').json()
    user = users[0]

    unique_text = f'Field test report review scheduled for tomorrow {uuid.uuid4().hex[:6]}'
    msg_payload = {
        'sender_user_id': user['id'],
        'message_text': unique_text
    }

    # Post message
    post_res = client.post(f'/projects/{project_id}/messages', json=msg_payload)
    assert post_res.status_code == 200
    msg_data = post_res.json()
    assert msg_data['project_id'] == project_id
    assert msg_data['sender_user_id'] == user['id']
    assert msg_data['message_text'] == unique_text
    assert msg_data['sender_name'] == user['name']

    # Get messages
    get_res = client.get(f'/projects/{project_id}/messages')
    assert get_res.status_code == 200
    messages = get_res.json()
    assert any(m['message_text'] == unique_text for m in messages)

    # Error handling
    err_p = client.post('/projects/99999999/messages', json=msg_payload)
    assert err_p.status_code == 404

    err_u = client.post(f'/projects/{project_id}/messages', json={'sender_user_id': 99999999, 'message_text': 'test'})
    assert err_u.status_code == 404

    err_get = client.get('/projects/99999999/messages')
    assert err_get.status_code == 404


def test_dashboard_stats_aggregation(client):
    response = client.get('/dashboard')
    assert response.status_code == 200
    data = response.json()

    # Validate all expected keys from DashboardStats schema
    assert 'total_problems' in data
    assert 'problems_by_status' in data
    assert 'problems_by_category' in data
    assert 'problems_by_district' in data
    assert 'problems_by_submitter_type' in data
    assert 'total_projects' in data
    assert 'projects_by_stage' in data
    assert 'completion_rate' in data
    assert 'total_patents' in data
    assert 'total_startups' in data
    assert 'active_industry_partnerships' in data
    assert 'partnerships_by_type' in data
    assert 'participating_institutions_count' in data

    # Validate types
    assert isinstance(data['total_problems'], int)
    assert isinstance(data['problems_by_status'], dict)
    assert isinstance(data['problems_by_category'], dict)
    assert isinstance(data['problems_by_district'], dict)
    assert isinstance(data['problems_by_submitter_type'], dict)
    assert isinstance(data['total_projects'], int)
    assert isinstance(data['projects_by_stage'], dict)
    assert isinstance(data['completion_rate'], (int, float))
    assert isinstance(data['total_patents'], int)
    assert isinstance(data['total_startups'], int)
    assert isinstance(data['active_industry_partnerships'], int)
    assert isinstance(data['partnerships_by_type'], dict)
    assert isinstance(data['participating_institutions_count'], int)

    assert data['total_problems'] >= 0
    assert data['total_projects'] >= 0
