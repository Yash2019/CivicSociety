import uuid
import pytest

def test_project_outcomes_upsert_and_get(client):
    projects = client.get('/projects').json()
    project_id = projects[0]['id']

    payload = {
        'patents_filed': 3,
        'startups_created': 1,
        'ip_generated': 'Advanced Desalination Flow Valve IP',
        'impact_notes': 'Provides clean water to 12,000 residents across coastal blocks'
    }

    # Record / upsert outcome
    post_res = client.post(f'/projects/{project_id}/outcomes', json=payload)
    assert post_res.status_code == 200
    res_data = post_res.json()
    assert res_data['patents_filed'] == 3
    assert res_data['startups_created'] == 1
    assert res_data['ip_generated'] == payload['ip_generated']

    # Get outcome
    get_res = client.get(f'/projects/{project_id}/outcomes')
    assert get_res.status_code == 200
    assert get_res.json()['patents_filed'] == 3

    # Update outcome
    update_payload = {
        'patents_filed': 4,
        'startups_created': 2,
        'ip_generated': 'Advanced Desalination Flow Valve v2',
        'impact_notes': 'Expanded to 20,000 residents'
    }
    up_res = client.post(f'/projects/{project_id}/outcomes', json=update_payload)
    assert up_res.status_code == 200
    assert up_res.json()['patents_filed'] == 4
    assert up_res.json()['startups_created'] == 2

    # Error handling
    err_res = client.post('/projects/99999999/outcomes', json=payload)
    assert err_res.status_code == 404


def test_industry_partnerships_lifecycle(client):
    projects = client.get('/projects').json()
    project_id = projects[0]['id']

    insts = client.get('/institutions').json()
    industry_inst = next((i for i in insts if i['type'] in ['industry', 'csr', 'msme', 'startup']), insts[-1])
    inst_id = industry_inst['id']

    # Request partnership
    part_payload = {
        'industry_institution_id': inst_id,
        'partnership_type': 'prototyping',
        'notes': 'Providing rapid prototyping lab equipment and PCB manufacturing'
    }
    req_res = client.post(f'/projects/{project_id}/partnerships', json=part_payload)
    assert req_res.status_code == 200
    part_data = req_res.json()
    assert part_data['status'] == 'requested'
    assert part_data['partnership_type'] == 'prototyping'
    partnership_id = part_data['id']

    # List project partnerships
    p_parts = client.get(f'/projects/{project_id}/partnerships')
    assert p_parts.status_code == 200
    assert any(p['id'] == partnership_id for p in p_parts.json())

    # List institution partnerships
    i_parts = client.get(f'/institutions/{inst_id}/partnerships')
    assert i_parts.status_code == 200
    assert any(p['id'] == partnership_id for p in i_parts.json())

    # Accept partnership
    acc_res = client.patch(f'/partnerships/{partnership_id}/status', json={'status': 'accepted'})
    assert acc_res.status_code == 200
    assert acc_res.json()['status'] == 'accepted'

    # Error handling
    err_p = client.post('/projects/99999999/partnerships', json=part_payload)
    assert err_p.status_code == 404

    err_i = client.post(f'/projects/{project_id}/partnerships', json={**part_payload, 'industry_institution_id': 99999999})
    assert err_i.status_code == 404

    err_stat = client.patch('/partnerships/99999999/status', json={'status': 'accepted'})
    assert err_stat.status_code == 404
