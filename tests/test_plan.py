import json
import pytest

base_api_url = "/api"

##########################
# TEST - PLAN
##########################  
def do_check_plan_name_availability(client, headers, payload):
    """
    CHECK PLAN AVAILABILITY
    """
    response = client.post(base_api_url + "/plan/availability", headers=headers, json=payload)
    return response

def do_add_plan(client, content_team_headers, payload):
    """
    ADD PLAN
    """
    response = client.post(base_api_url + "/plan", headers=content_team_headers, json=payload)
    return response

def do_get_plan(client, content_team_headers, plan_id):
    """
    GET PLAN
    """
    response = client.get(base_api_url + f"/plan/{plan_id}", headers=content_team_headers)
    return response

def do_update_plan(client, content_team_headers, plan_id, payload):
    """
    UPDATE PLAN
    """
    response = client.put(base_api_url + f"/plan/{plan_id}", headers=content_team_headers, json=payload)
    return response

def do_delete_plan(client, content_team_headers, plan_id):
    """
    DELETE PLAN
    """
    response = client.delete(base_api_url + f"/plan/{plan_id}", headers=content_team_headers)
    return response

def do_get_plan_list(client, content_team_headers):
    """
    GET PLAN LIST
    """
    response = client.get(base_api_url + "/plans", headers=content_team_headers)
    return response

def do_get_menu_groups_by_plan(client, content_team_headers, plan_id):
    """
    GET MENU-GROUPS BY PLAN
    """
    response = client.get(base_api_url + f"/plan/{plan_id}/menu-group", headers=content_team_headers)
    return response

##########################
# TEST CASES
########################## 
plan_id = None

def test_add_plan(client, content_team_headers):
    """
    Test: Add Plan
    """
    payload = {
        "brand_profile_id": 2,
        "plan_name": "Lunch",
        "external_plan_id": "111",
        "menu_group_id_list": [1, 2]
    }
    response = do_add_plan(client, content_team_headers, payload)
    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json["status"] == "successful"
    assert response_json["action"] == "add_plan"

    global plan_id
    response_data = response_json["data"]
    assert "plan_id" in response_data, "plan_id is missing"
    plan_id = response_data["plan_id"]

def test_check_plan_name_availability(client, content_team_headers):
    """
    Test: Check Plan Name Availability
    """
    payload = {
        "plan_name": "Lunch",
        "brand_profile_id": 2
    }
    response = do_check_plan_name_availability(client, content_team_headers, payload)
    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json["status"] == "successful"
    assert response_json["action"] == "check_plan_name_availability"

    response_data = response_json["data"]
    assert response_data["availability_p"] == 0

def test_get_plan(client, content_team_headers):
    """
    Test: Get Plan
    """
    response = do_get_plan(client, content_team_headers, plan_id)
    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json["status"] == "successful"
    assert response_json["action"] == "get_plan"

    response_data = response_json["data"]
    assert response_data["plan_id"] == plan_id
    assert response_data["plan_name"] == "Lunch"
    assert response_data["external_plan_id"] == "111"
    assert response_data["brand_profile_id"] == 2
    assert len(response_data["menu_group_list"]) == 2

def test_update_plan(client, content_team_headers):
    """
    Test: Update Plan
    """
    payload = {
        "plan_name": "Breakfast",
        "brand_profile_id": 2,
        "external_plan_id": "111",
        "menu_group_id_list": [3]
    }
    response = do_update_plan(client, content_team_headers, plan_id, payload)
    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json["status"] == "successful"
    assert response_json["action"] == "update_plan"
    
    """
    Test: Get Plan
    """
    response = do_get_plan(client, content_team_headers, plan_id)
    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json["status"] == "successful"
    assert response_json["action"] == "get_plan"

    response_data = response_json["data"]
    assert response_data["plan_name"] == "Breakfast"

def test_get_plan_list(client, content_team_headers):
    """
    Test: Get Plan List
    """
    response = do_get_plan_list(client, content_team_headers)
    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json["status"] == "successful"
    assert response_json["action"] == "get_plans"

    response_data = response_json["data"]
    assert len(response_data) == 3

def test_delete_plan(client, content_team_headers):
    """
    Test: Delete Plan
    """
    response = do_delete_plan(client, content_team_headers, plan_id)
    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json["status"] == "successful"
    assert response_json["action"] == "delete_plan"

    """
    Test: Get Plan List
    """
    response = client.get(base_api_url + "/plans", headers=content_team_headers)
    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json["status"] == "successful"
    assert response_json["action"] == "get_plans"

    response_data = response_json["data"]
    assert len(response_data) == 2