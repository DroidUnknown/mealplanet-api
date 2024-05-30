import json
import pytest

base_api_url = "/api"

##########################
# TEST - MERCHANT_ROLES
##########################
def do_get_merchant_roles(client, headers, args=""):
    """
    Get merchant_roles
    """
    response = client.get(base_api_url + f"/merchant_roles{args}", headers=headers)
    return response

def do_get_merchant_role(client, headers, merchant_role_id):
    """
    Get one merchant_role
    """
    response = client.get(base_api_url + f"/merchant_role/{merchant_role_id}", headers=headers)
    return response

def do_add_merchant_role(client, headers, payload):
    """
    Add merchant_role
    """
    response = client.post(base_api_url + "/merchant_role", headers=headers, json=payload)
    return response

def do_update_merchant_role(client, headers, merchant_role_id, payload):
    """
    Update merchant_role
    """
    response = client.put(base_api_url + f"/merchant_role/{merchant_role_id}", headers=headers, json=payload)
    return response

def do_delete_merchant_role(client, headers, merchant_role_id):
    """
    Delete merchant_role
    """
    response = client.delete(base_api_url + f"/merchant_role/{merchant_role_id}", headers=headers)
    return response

##########################
# FIXTURES
##########################

@pytest.fixture(scope="module", autouse=True)
def merchant_role_id(client, headers):
    """
    Add merchant_role
    """
    payload = {
        "merchant_id": 1,
        "merchant_role_name": "Test merchant_role",
        "merchant_role_description": "Test merchant_role description",
        "policy_id_list": [1]
    }
    response = do_add_merchant_role(client, headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    return j["merchant_role_id"]

##########################
# TEST CASES
##########################
    
def test_get_merchant_roles(client, headers):
    """
    Test get merchant_roles
    """
    response = do_get_merchant_roles(client, headers,"?merchant_id=1")
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'  
    
def test_get_merchant_role(client, headers, merchant_role_id):
    """
    Test get merchant_role
    """
    response = do_get_merchant_role(client, headers, merchant_role_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    
def test_update_merchant_role(client, headers, merchant_role_id):
    """
    Test update merchant_role
    """
    payload = {
        "merchant_role_name": "Test merchant_role Updated",
        "merchant_role_description": "Test merchant_role description Updated",
        "policy_id_list": [1]
    }
    response = do_update_merchant_role(client, headers, merchant_role_id, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    
def test_delete_merchant_role(client, headers,merchant_role_id):
    """
    Test delete merchant_role
    """
    response = do_delete_merchant_role(client, headers,merchant_role_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'