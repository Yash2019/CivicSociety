import io
import uuid
import pytest

def test_milestone_lifecycle(client):
    projects = client.get('/projects').json()
    project_id = projects[0]['id']

    # Add milestone
    title = f'Phase 2 Prototype Testing {uuid.uuid4().hex[:6]}'
    m_payload = {
        'title': title,
        'description': 'Stress testing the membrane in high salinity wells',
        'due_date': '2026-11-30'
    }
    create_res = client.post(f'/projects/{project_id}/milestones', json=m_payload)
    assert create_res.status_code == 200
    m_data = create_res.json()
    assert m_data['title'] == title
    assert m_data['status'] == 'pending'
    assert m_data['completed_at'] is None
    milestone_id = m_data['id']

    # List project milestones
    list_res = client.get(f'/projects/{project_id}/milestones')
    assert list_res.status_code == 200
    assert any(m['id'] == milestone_id for m in list_res.json())

    # Update milestone to in_progress
    up_res1 = client.patch(f'/milestones/{milestone_id}/status', json={'status': 'in_progress'})
    assert up_res1.status_code == 200
    assert up_res1.json()['status'] == 'in_progress'

    # Complete milestone
    up_res2 = client.patch(f'/milestones/{milestone_id}/status', json={'status': 'completed'})
    assert up_res2.status_code == 200
    assert up_res2.json()['status'] == 'completed'
    assert up_res2.json()['completed_at'] is not None

    # Error handling
    err_proj = client.post('/projects/99999999/milestones', json=m_payload)
    assert err_proj.status_code == 404

    err_m = client.patch('/milestones/99999999/status', json={'status': 'completed'})
    assert err_m.status_code == 404


def test_deliverable_upload_and_retrieval(client):
    projects = client.get('/projects').json()
    project_id = projects[0]['id']

    file_content = b'%PDF-1.4 Mock Deliverable Report Content'
    file = ('validation_report.pdf', io.BytesIO(file_content), 'application/pdf')

    data = {
        'doc_type': 'test_report'
    }

    # Upload deliverable without milestone
    res = client.post(f'/projects/{project_id}/deliverables', data=data, files={'file': file})
    assert res.status_code == 200
    deliv_data = res.json()
    assert deliv_data['project_id'] == project_id
    assert deliv_data['doc_type'] == 'test_report'
    assert 'file_url' in deliv_data
    deliv_id = deliv_data['id']

    # Get project deliverables
    list_res = client.get(f'/projects/{project_id}/deliverables')
    assert list_res.status_code == 200
    assert any(d['id'] == deliv_id for d in list_res.json())

    # Verify static file download
    from pathlib import Path
    filename = Path(deliv_data['file_url']).name
    media_res = client.get(f'/media/{filename}')
    assert media_res.status_code == 200
    assert media_res.content == file_content

    # Error: upload for non-existent project
    file2 = ('validation_report2.pdf', io.BytesIO(file_content), 'application/pdf')
    err_res = client.post('/projects/99999999/deliverables', data=data, files={'file': file2})
    assert err_res.status_code == 404
