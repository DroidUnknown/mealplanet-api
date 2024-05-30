import json

from sqlalchemy import text
from utils import jqutils

base_api_url = "/api"

def do_add_department(client, headers, payload):
    url = base_api_url + '/department'
    response = client.post(url, json=payload, headers=headers)
    return response

def do_edit_department(client, headers, payload, department_id):
    url = base_api_url + '/department/' + str(department_id)
    response = client.put(url, json=payload, headers=headers)
    return response

def do_delete_department(client, headers, department_id):
    url = base_api_url + '/department/' + str(department_id)
    response = client.delete(url, headers=headers)
    return response

def do_get_department(client, headers, department_id):
    url = base_api_url + '/department/' + str(department_id)
    response = client.get(url, headers=headers)
    return response

def do_get_departments(client, headers):
    url = base_api_url + '/departments'
    response = client.get(url, headers=headers)
    return response

# GLOBALS
department_id = None

# TEST CASES

def test_add_department(client, headers):
    
    payload = {
        "department_name": "test department",
        "department_description": "test department description",
        "facility_id": 1,
    }
    response = do_add_department(client, headers, payload)
    assert response.status_code == 200
    
    response_body = json.loads(response.data)
    assert response_body['status'] == 'successful'
    assert response_body['action'] == 'add_department'
    assert response_body['data']['department_id'], 'department_id is missing'
    
    global department_id
    department_id = response_body['data']['department_id']

def test_edit_department(client, headers):
    payload = {
        "department_name": "edited department",
        "department_description": "edited department description",
        "facility_id": 1,
    }
    response = do_edit_department(client, headers, payload, department_id)
    assert response.status_code == 200
    
    response_body = json.loads(response.data)
    assert response_body['status'] == 'successful'
    assert response_body['action'] == 'edit_department'
    assert response_body['data']['department_id'], 'department_id is missing'

def test_get_department(client, headers):
    response = do_get_department(client, headers, department_id)
    assert response.status_code == 200
    
    response_body = json.loads(response.data)
    assert response_body['status'] == 'successful'
    assert response_body['action'] == 'get_department'
    assert response_body['data']['department_id'] == department_id, 'department_id is missing'

def test_get_departments(client, headers):
    response = do_get_departments(client, headers)
    assert response.status_code == 200
    
    response_body = json.loads(response.data)
    assert response_body['status'] == 'successful'
    assert response_body['action'] == 'get_departments'
    assert len(response_body['data']) > 0, 'department_list is empty'

def test_delete_department(client, headers):
    response = do_delete_department(client, headers, department_id)
    assert response.status_code == 200
    
    response_body = json.loads(response.data)
    assert response_body['status'] == 'successful'
    assert response_body['action'] == 'delete_department'
    
    db_engine = jqutils.get_db_engine()
    query = text("""
        SELECT meta_status
        FROM department
        WHERE department_id = :department_id
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, department_id=department_id).fetchone()
        assert result, "department_id not found"
        meta_status = result['meta_status']
    
    assert meta_status == 'deleted', 'meta_status is not deleted'