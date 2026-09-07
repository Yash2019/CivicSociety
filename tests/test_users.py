import uuid
import pytest

def test_list_users(client):
    response = client.get('/users')
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert 'id' in data[0]
    assert 'name' in data[0]
    assert 'email' in data[0]
    assert 'role' in data[0]

def test_create_user_success(client):
    unique_email = f'tester_{uuid.uuid4().hex[:8]}@example.com'
    payload = {
        'name': 'Test User',
        'email': unique_email,
        'role': 'student',
        'institution_id': None
    }
    response = client.post('/users', json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data['email'] == unique_email
    assert data['name'] == 'Test User'
    assert data['role'] == 'student'
    assert 'id' in data

def test_get_user_by_id(client):
    unique_email = f'fetch_{uuid.uuid4().hex[:8]}@example.com'
    res = client.post('/users', json={'name': 'Fetch Me', 'email': unique_email, 'role': 'citizen'})
    user_id = res.json()['id']

    response = client.get(f'/users/{user_id}')
    assert response.status_code == 200
    assert response.json()['id'] == user_id
    assert response.json()['email'] == unique_email

def test_create_duplicate_email(client):
    unique_email = f'dup_{uuid.uuid4().hex[:8]}@example.com'
    client.post('/users', json={'name': 'User 1', 'email': unique_email, 'role': 'citizen'})
    dup_res = client.post('/users', json={'name': 'User 2', 'email': unique_email, 'role': 'citizen'})
    assert dup_res.status_code == 400
    assert 'already exists' in dup_res.json()['detail'].lower()

def test_get_user_not_found(client):
    response = client.get('/users/99999999')
    assert response.status_code == 404

def test_create_user_invalid_institution(client):
    response = client.post('/users', json={
        'name': 'Invalid Inst',
        'email': f'invalid_{uuid.uuid4().hex[:8]}@example.com',
        'role': 'faculty',
        'institution_id': 99999999
    })
    assert response.status_code == 404

def test_create_user_with_zero_institution_id(client):
    response = client.post('/users', json={
        'name': 'Swagger Default User',
        'email': f'swagger_{uuid.uuid4().hex[:8]}@example.com',
        'role': 'citizen',
        'institution_id': 0
    })
    assert response.status_code == 200
    assert response.json()['institution_id'] is None
