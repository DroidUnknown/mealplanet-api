import json
import pytest

from sqlalchemy import text
from utils import jqutils

base_api_url = "/api"

##########################
# TEST - PLAN
##########################  
def do_check_plan_name_availability(client, headers, payload):
    """
    Check plan availability
    """
    response = client.post(base_api_url + "/plan/availability", headers=headers, json=payload)
    return response

def do_add_plan(client, content_team_headers, payload):
    """
    Add plan
    """
    response = client.post(base_api_url + "/plan", headers=content_team_headers, json=payload)
    return response

def do_get_plan(client, content_team_headers, plan_id):
    """
    Get plan
    """
    response = client.get(base_api_url + f"/plan/{plan_id}", headers=content_team_headers)
    return response

def do_update_plan(client, content_team_headers, plan_id, payload):
    """
    Update plan
    """
    response = client.put(base_api_url + f"/plan/{plan_id}", headers=content_team_headers, json=payload)
    return response

def do_get_plans(client, content_team_headers, brand_profile_id_list=[]):
    """
    Get plans
    """
    request_url = base_api_url + "/plans"
    if brand_profile_id_list:
        request_url += "?brand_profile_id_list=" + ",".join(map(str, brand_profile_id_list))
    response = client.get(request_url, headers=content_team_headers)
    return response

def do_get_menu_groups_by_plan(client, content_team_headers, plan_id):
    """
    Get menu groups by plan
    """
    response = client.get(base_api_url + f"/plan/{plan_id}/menu-groups", headers=content_team_headers)
    return response

def do_delete_plan(client, content_team_headers, plan_id):
    """
    Delete plan
    """
    response = client.delete(base_api_url + f"/plan/{plan_id}", headers=content_team_headers)
    return response

##########################
# GLOBALS
##########################
brand_profile_id = 3
plan_id = None

##########################
# FIXTURES
##########################
@pytest.fixture(scope="module", autouse=True)
def existing_plan_count():
    db_engine = jqutils.get_db_engine()
    
    query = text("""
        SELECT COUNT(1) AS cnt
        FROM plan
        WHERE brand_profile_id = :brand_profile_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, brand_profile_id=brand_profile_id, meta_status="active").fetchone()
        return result["cnt"]

##########################
# TEST CASES
########################## 
def test_add_plan(client, content_team_headers):
    """
    Test: Add Plan
    """
    payload = {
        "brand_profile_id": brand_profile_id,
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
        "brand_profile_id": brand_profile_id
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
    assert response_data["brand_profile_id"] == brand_profile_id
    assert len(response_data["menu_group_list"]) == 2

def test_update_plan(client, content_team_headers):
    """
    Test: Update Plan
    """
    payload = {
        "plan_name": "Breakfast",
        "brand_profile_id": brand_profile_id,
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

def test_get_plans(client, content_team_headers, existing_plan_count):
    """
    Test: Get plans
    """
    brand_profile_id_list = [brand_profile_id]
    response = do_get_plans(client, content_team_headers, brand_profile_id_list)
    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json["status"] == "successful"
    assert response_json["action"] == "get_plans"

    response_data = response_json["data"]
    assert len(response_data) == 1, f"Brand profiles list should be only have 1 item."
    
    brand_profile = response_data[0]
    expected_plan_count = existing_plan_count + 1
    assert len(brand_profile["plan_list"]) == expected_plan_count, f"Plan list should have {expected_plan_count} items."

def test_delete_plan(client, content_team_headers, existing_plan_count):
    """
    Test: Delete Plan
    """
    response = do_delete_plan(client, content_team_headers, plan_id)
    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json["status"] == "successful"
    assert response_json["action"] == "delete_plan"

    """
    Test: Get Plans
    """
    brand_profile_id_list = [brand_profile_id]
    response = do_get_plans(client, content_team_headers, brand_profile_id_list)
    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json["status"] == "successful"
    assert response_json["action"] == "get_plans"

    response_data = response_json["data"]
    assert len(response_data) == existing_plan_count, f"Plans should have {existing_plan_count} items."