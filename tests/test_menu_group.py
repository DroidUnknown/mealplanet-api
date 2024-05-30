import json
from tests import test_plan

base_api_url = "/api"

##########################
# TEST - MENU-GROUP
########################## 
def do_add_menu_group(client, content_team_headers, payload):
    """
    ADD MENU-GROUP
    """
    response = client.post(base_api_url + "/menu-group", headers=content_team_headers, json=payload)
    return response

def do_get_menu_group(client, content_team_headers, menu_group_id):
    """
    GET MENU-GROUP
    """
    response = client.get(base_api_url + f"/menu-group/{menu_group_id}", headers=content_team_headers)
    return response

def do_update_menu_group(client, content_team_headers, menu_group_id, payload):
    """
    UPDATE MENU-GROUP
    """
    response = client.put(base_api_url + f"/menu-group/{menu_group_id}", headers=content_team_headers, json=payload)
    return response

def do_delete_menu_group(client, content_team_headers, menu_group_id):
    """
    DELETE MENU-GROUP
    """
    response = client.delete(base_api_url + f"/menu-group/{menu_group_id}", headers=content_team_headers)
    return response

def do_get_menu_group_list(client, content_team_headers):
    """
    GET MENU-GROUP LIST
    """
    response = client.get(base_api_url + "/menu-group", headers=content_team_headers)
    return response

##########################
# TEST CASES
########################## 

def test_menu_group(client, content_team_headers):
    """
    Test: Add Menu Group
    """
    payload = {
        "plan_id": "2",
        "menu_group_name": "Lunch"
    }
    response = do_add_menu_group(client, content_team_headers, payload)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    menu_group_id = response_data["menu_group_id"]

    """
    Test: Get Menu Group
    """
    response = do_get_menu_group(client, content_team_headers, menu_group_id)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data["menu Group_name"] == "Lunch"

    """
    Test: Update Menu Group
    """
    payload = {
        "menu_group_name": "Breakfast"
    }
    response = do_update_menu_group(client, content_team_headers, menu_group_id, payload)
    assert response.status_code == 200
    
    """
    Test: Get Menu Group
    """
    response = do_get_menu_group(client, content_team_headers, menu_group_id)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data["menu Group_name"] == "Breakfast"

    """
    Test: Get Menu Group List
    """
    response = do_get_menu_group_list(client, content_team_headers)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert len(response_data) == 1, "Menu Group List should have 1 item."

    """
    Test: Delete Menu Group
    """
    response = do_delete_menu_group(client, content_team_headers, menu_group_id)
    assert response.status_code == 200

    """
    Test: Get Menu Group List
    """
    response = do_get_menu_group_list(client, content_team_headers)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert len(response_data) == 0, "Menu Group List should have 0 item."
    
    """
    Test: Add Menu Group
    """
    payload = {
        "plan_id": "2",
        "menu_group_name": "Breakfast"
    }
    response = do_add_menu_group(client, content_team_headers, payload)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    menu_group_id = response_data["menu_group_id"]

    """
    Test: Get Menu Group List by Plan
    """
    response = test_plan.do_get_menu_groups_by_plan(client, content_team_headers, 2)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert len(response_data) == 1, "Menu Group List should have 1 item."
    