import json
import pytest

base_api_url = "/api"

##########################
# TEST - PLAN
##########################  
def do_check_plan_availability(client, headers, payload):
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
first_plan_id = None

@pytest.mark.dependency()
def test_add_plan(client, content_team_headers):
    """
    Test: Add Plan
    """
    payload = [
        {
            "external_plan_id": "111",
            "brand_profile_id": 2,
            "plan_name": "Lunch",
        },
        {
            "external_plan_id": "112",
            "brand_profile_id": 2,
            "plan_name": "Dinner",
        }
    ]
    response = do_add_plan(client, content_team_headers, payload)
    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json["status"] == "successful"
    assert response_json["action"] == "add_plan"

    global first_plan_id
    response_json = response_json["data"]
    plan_id_list = response_json["plan_id_list"]
    first_plan_id = plan_id_list[0]

    response = do_check_plan_availability(client, content_team_headers, {"external_plan_id": "111"})
    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json["status"] == "successful"
    assert response_json["action"] == "check_plan_availability"

    response_data = response_json["data"]
    assert response_data["availability_p"] == 0

def test_get_plan(client, content_team_headers):
    """
    Test: Get Plan
    """
    response = do_get_plan(client, content_team_headers, first_plan_id)
    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json["status"] == "successful"
    assert response_json["action"] == "get_plan"

    response_data = response_json["data"]
    assert response_data, "Data is empty"
    assert response_data["plan_id"] == first_plan_id
    assert response_data["plan_name"] == "Lunch"

def test_update_plan(client, content_team_headers):
    """
    Test: Update Plan
    """
    payload = {
        "external_plan_id": "111",
        "brand_profile_id": 2,
        "plan_name": "Breakfast"
    }
    response = do_update_plan(client, content_team_headers, first_plan_id, payload)
    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json["status"] == "successful"
    assert response_json["action"] == "update_plan"
    
    """
    Test: Get Plan
    """
    response = do_get_plan(client, content_team_headers, first_plan_id)
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
    assert len(response_data) == 2

def test_delete_plan(client, content_team_headers):
    """
    Test: Delete Plan
    """
    response = do_delete_plan(client, content_team_headers, first_plan_id)
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
    assert len(response_data) == 1