import io
import uuid
from unittest.mock import patch
import pytest

def test_list_problems(client):
    response = client.get('/problems')
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

def test_get_problem_by_id(client):
    problems = client.get('/problems').json()
    problem_id = problems[0]['id']
    response = client.get(f'/problems/{problem_id}')
    assert response.status_code == 200
    assert response.json()['id'] == problem_id

def test_get_problem_not_found(client):
    response = client.get('/problems/99999999')
    assert response.status_code == 404

def test_get_problems_by_user(client):
    users = client.get('/users').json()
    user_id = users[0]['id']
    response = client.get(f'/problems/user/{user_id}')
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@patch('backend.services.classification.classify_issue', return_value='water_resources')
def test_submit_problem_with_photo(mock_classify, client):
    users = client.get('/users').json()
    user_id = users[0]['id']
    u1 = uuid.uuid4().hex
    u2 = uuid.uuid4().hex

    file_content = b'fake image byte stream'
    file = ('test_water_photo.png', io.BytesIO(file_content), 'image/png')

    data = {
        'title': f'Brand new distinct issue {u1}',
        'description': f'Completely unique scenario {u1} regarding freshwater supply {u2}',
        'submitter_type': 'pri',
        'district': 'Dakshina Kannada',
        'latitude': 12.87,
        'longitude': 74.88,
        'submitted_by': str(user_id)
    }

    response = client.post('/PostProblems', data=data, files={'photo': file})
    assert response.status_code == 200
    res = response.json()
    assert res['title'] == data['title']
    assert res['category'] == 'water_resources'
    assert res['priority_score'] == 90
    assert res['status'] in ['routed', 'submitted']
    assert 'id' in res

@patch('backend.services.classification.classify_issue', return_value='energy')
def test_submit_problem_individual_no_photo(mock_classify, client):
    users = client.get('/users').json()
    user_id = users[0]['id']
    unique_suffix = uuid.uuid4().hex[:8]

    data = {
        'title': f'Voltage fluctuation {unique_suffix}',
        'description': f'Frequent power brownouts damaging appliances in rural block {unique_suffix}',
        'submitter_type': 'individual',
        'district': 'Bengaluru',
        'latitude': 12.97,
        'longitude': 77.59,
        'submitted_by': str(user_id)
    }

    response = client.post('/PostProblems', data=data)
    assert response.status_code == 200
    res = response.json()
    assert res['priority_score'] == 40
    assert res['category'] == 'energy'

@patch('backend.services.classification.classify_issue', return_value='agriculture')
def test_deduplication_detection(mock_classify, client):
    users = client.get('/users').json()
    user_id = users[0]['id']
    code_a = uuid.uuid4().hex
    code_b = uuid.uuid4().hex

    desc = f'Unprecedented agronomy emergency code {code_a} impacting soil and yields {code_b}'
    title = f'Soil Emergency {code_a}'
    data1 = {
        'title': title,
        'description': desc,
        'submitter_type': 'individual',
        'district': 'Pune',
        'latitude': 18.52,
        'longitude': 73.85,
        'submitted_by': str(user_id)
    }

    res1 = client.post('/PostProblems', data=data1)
    assert res1.status_code == 200
    original_id = res1.json()['id']
    assert res1.json()['status'] != 'duplicate'

    data2 = {
        'title': title,
        'description': desc,
        'submitter_type': 'individual',
        'district': 'Pune',
        'latitude': 18.52,
        'longitude': 73.85,
        'submitted_by': str(user_id)
    }

    res2 = client.post('/PostProblems', data=data2)
    assert res2.status_code == 200
    dup_res = res2.json()
    assert dup_res['status'] == 'duplicate'
    assert dup_res['duplicate_problem'] == original_id

def test_routing_accept_and_decline(client):
    insts = client.get('/institutions').json()
    routing_id = None
    for inst in insts:
        probs = client.get(f"/institutions/{inst['id']}/problems").json()
        if probs:
            routing_id = probs[0]['routing_id']
            break

    if routing_id is not None:
        acc = client.post(f'/routings/{routing_id}/accept')
        assert acc.status_code == 200
        assert acc.json()['status'] == 'accepted'

        dec = client.post(f'/routings/{routing_id}/decline')
        assert dec.status_code == 200
        assert dec.json()['status'] == 'declined'

    err = client.post('/routings/99999999/accept')
    assert err.status_code == 404
