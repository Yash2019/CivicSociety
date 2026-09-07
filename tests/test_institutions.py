import uuid
import pytest

def test_list_institutions(client):
    response = client.get('/institutions')
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert 'id' in data[0]
    assert 'name' in data[0]
    assert 'type' in data[0]

def test_create_institution_json(client):
    name = f'Indian Innovation Lab {uuid.uuid4().hex[:6]}'
    payload = {
        'name': name,
        'type': 'university',
        'domain': 'energy',
        'domains': ['energy', 'environment'],
        'district': 'Bengaluru',
        'has_incubation': True
    }
    response = client.post('/institutions', json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data['name'] == name
    assert data['type'] == 'university'
    assert 'energy' in data['domains']
    assert data['has_incubation'] is True
    assert 'id' in data

def test_create_institution_form(client):
    name = f'Form MSME Lab {uuid.uuid4().hex[:6]}'
    data = {
        'name': name,
        'type': 'msme',
        'domain': 'agriculture',
        'domains': 'agriculture, rural_livelihoods',
        'district': 'Pune',
        'has_incubation': 'false'
    }
    response = client.post('/create_institution', data=data)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data['name'] == name
    assert res_data['type'] == 'msme'
    assert 'agriculture' in res_data['domains']

def test_get_institution_by_id(client):
    insts = client.get('/institutions').json()
    inst_id = insts[0]['id']
    response = client.get(f'/institutions/{inst_id}')
    assert response.status_code == 200
    assert response.json()['id'] == inst_id

def test_get_institution_not_found(client):
    response = client.get('/institutions/99999999')
    assert response.status_code == 404

def test_get_institution_routed_problems(client):
    insts = client.get('/institutions').json()
    inst_id = insts[0]['id']
    response = client.get(f'/institutions/{inst_id}/problems')
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_institution_routed_problems_not_found(client):
    response = client.get('/institutions/99999999/problems')
    assert response.status_code == 404
