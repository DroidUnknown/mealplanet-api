import json
from tests import test_brand_profile

base_api_url = "/api"

##########################
# TEST - PLAN
########################## 
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
    response = client.get(base_api_url + "/plan", headers=content_team_headers)
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

def test_plan(client, content_team_headers):
    """
    Test: Add Plan
    """
    payload = {
        "external_plan_id": "111",
        "brand_profile_id": 2,
        "plan_name": "Lunch",
    }
    response = do_add_plan(client, content_team_headers, payload)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    plan_id = response_data["plan_id"]

    """
    Test: Get Plan
    """
    response = do_get_plan(client, content_team_headers, plan_id)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data["plan_name"] == "Lunch"

    """
    Test: Update Plan
    """
    payload = {
        "plan_name": "Breakfast"
    }
    response = do_update_plan(client, content_team_headers, plan_id, payload)
    assert response.status_code == 200
    
    """
    Test: Get Plan
    """
    response = do_get_plan(client, content_team_headers, plan_id)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data["plan_name"] == "Breakfast"

    """
    Test: Get Plan List
    """
    response = do_get_plan_list(client, content_team_headers)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert len(response_data) == 1, "Plan List should have 1 item."

    """
    Test: Delete Plan
    """
    response = do_delete_plan(client, content_team_headers, plan_id)
    assert response.status_code == 200

    """
    Test: Get Plan List
    """
    response = client.get(base_api_url + "/plan", headers=content_team_headers)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert len(response_data) == 0, "Plan List should have 0 item."
    
    """
    Test: Add Plan
    """
    payload = {
        "external_plan_id": "111",
        "brand_profile_id": 2,
        "plan_name": "Lunch",
    }
    response = do_add_plan(client, content_team_headers, payload)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    plan_id = response_data["plan_id"]

    """
    Test: Get Menu Groups by Plan
    """
    response = test_brand_profile.do_get_plans_by_brand_profile(client, content_team_headers, 2)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert len(response_data) == 1, "Plan List should have 1 item."