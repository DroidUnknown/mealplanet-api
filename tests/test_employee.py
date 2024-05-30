import json
import pytest

base_api_url = "/api"

##########################
# TEST - EMPLOYEES
##########################
def do_get_employees(client, headers, args=""):
    """
    Get employees
    """
    response = client.get(base_api_url + f"/employees{args}", headers=headers)
    return response

def do_get_employee(client, headers, employee_id):
    """
    Get one employee
    """
    response = client.get(base_api_url + f"/employee/{employee_id}", headers=headers)
    return response

def do_add_employee(client, headers, payload):
    """
    Add employee
    """
    response = client.post(base_api_url + "/employee", headers=headers, json=payload)
    return response

def do_update_employee(client, headers, employee_id, payload):
    """
    Update employee
    """
    response = client.put(base_api_url + f"/employee/{employee_id}", headers=headers, json=payload)
    return response

def do_delete_employee(client, headers, employee_id):
    """
    Delete employee
    """
    response = client.delete(base_api_url + f"/employee/{employee_id}", headers=headers)
    return response

##########################
# FIXTURES
##########################

@pytest.fixture(scope="module", autouse=True)
def employee_id(client, headers):
    """
    Add employee
    """
    payload = {
        "merchant_id": 1,
        "employee_code": "abc_1234",
        "first_names_en": "Test",
        "last_name_en": "Employee",
        "first_names_ar": None,
        "last_name_ar": None,
        "email": None,
        "phone_nr": "1234562170",
        "personal_access_code": "1234",
        "merchant_role_id": 1,
        "facility_id_list": [1,2,3],
        "user": {
            "username": "test_employee",
            "password": "123456",
            "role_id": 1
        },
        "all_facility_access_p":1
    }
    response = do_add_employee(client, headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    return j["data"]["employee_id"]

##########################
# TEST CASES
##########################
    
def test_get_employees(client, headers):
    """
    Test get employees
    """
    response = do_get_employees(client, headers,"?merchant_id=1")
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'  
    
def test_get_employee(client, headers, employee_id):
    """
    Test get employee
    """
    response = do_get_employee(client, headers, employee_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    
def test_update_employee(client, headers, employee_id):
    """
    Test update employee
    """

    response = do_get_employee(client, headers, employee_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    
    user_id = j["data"]["user_id"]
    
    payload = {
        "merchant_id": 1,
        "employee_code": "abc_1234",
        "first_names_en": "Test",
        "last_name_en": "Employee",
        "first_names_ar": None,
        "last_name_ar": None,
        "email": None,
        "phone_nr": "1234567890",
        "personal_access_code": "1290",
        "merchant_role_id": 1,
        "facility_id_list": [1,4,9],
        "user": {
            "username": "test_employee",
            "password": "123457",
            "role_id": 2
        },
        "all_facility_access_p":0
    }
    response = do_update_employee(client, headers, employee_id, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    
def test_delete_employee(client, headers,employee_id):
    """
    Test delete employee
    """
    response = do_delete_employee(client, headers,employee_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'