import json
import pytest

from utils import jqutils
from sqlalchemy import text

base_api_url = "/api"

##########################
# TEST - menu group
########################## 
def do_check_menu_group_name_availability(client, headers, payload):
    """
    Check menu group availability
    """
    response = client.post(base_api_url + "/menu-group/availability", headers=headers, json=payload)
    return response

def do_add_menu_group(client, content_team_headers, payload):
    """
    Add menu group
    """
    response = client.post(base_api_url + "/menu-group", headers=content_team_headers, json=payload)
    return response

def do_bulk_add_menu_groups(client, content_team_headers, payload):
    """
    Bulk add menu groups
    """
    response = client.post(base_api_url + "/bulk-add-menu-groups", headers=content_team_headers, json=payload)
    return response

def do_get_menu_group(client, content_team_headers, menu_group_id):
    """
    Get menu group
    """
    response = client.get(base_api_url + f"/menu-group/{menu_group_id}", headers=content_team_headers)
    return response

def do_update_menu_group(client, content_team_headers, menu_group_id, payload):
    """
    Update menu group
    """
    response = client.put(base_api_url + f"/menu-group/{menu_group_id}", headers=content_team_headers, json=payload)
    return response

def do_get_menu_groups(client, content_team_headers):
    """
    Get menu groups
    """
    response = client.get(base_api_url + "/menu-groups", headers=content_team_headers)
    return response

def do_delete_menu_group(client, content_team_headers, menu_group_id):
    """
    Delete menu group
    """
    response = client.delete(base_api_url + f"/menu-group/{menu_group_id}", headers=content_team_headers)
    return response

##########################
# GLOBALS
########################## 
menu_group_id = None

##########################
# FIXTURES
##########################
@pytest.fixture(scope="module", autouse=True)
def existing_menu_group_count():
    db_engine = jqutils.get_db_engine()
    
    query = text("""
        SELECT COUNT(1) AS cnt
        FROM menu_group
        WHERE meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, meta_status="active").fetchone()
        return result["cnt"]

##########################
# TEST CASES
########################## 
def test_add_menu_group(client, content_team_headers):
    """
    Test: Add menu group
    """
    payload = {
        "menu_group_name": "menu-group test",
        "external_menu_group_id": "1",
    }
    response = do_add_menu_group(client, content_team_headers, payload)
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json["status"] == "successful"
    
    response_data = response_json["data"]
    assert "menu_group_id" in response_data, "menu_group_id should be present in response data."
    
    global menu_group_id
    menu_group_id = response_data["menu_group_id"]
    
    # validate that same menu group name cannot be added again
    response = do_add_menu_group(client, content_team_headers, payload)
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json["status"] == "failed"
    assert response_json["message"] == "Menu group name already in use."

def test_bulk_add_menu_groups(client, content_team_headers):
    """
    Test: Bulk add menu groups
    """
    menu_group_name_list = ["menu-group test 1", "menu-group test 2"]
    payload = {
        "menu_group_list": [
            {
                "menu_group_name": menu_group_name_list[0],
                "external_menu_group_id": "1",
            },
            {
                "menu_group_name": menu_group_name_list[1],
                "external_menu_group_id": "2",
            },
        ]
    }
    response = do_bulk_add_menu_groups(client, content_team_headers, payload)
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json["status"] == "successful"

    # validate that same menu group name cannot be added again
    response = do_bulk_add_menu_groups(client, content_team_headers, payload)
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json["status"] == "failed"
    assert response_json["message"] == "Menu group name already in use."
    
    # validate that repeated menu group names in payload are not allowed
    payload = {
        "menu_group_list": [
            {
                "menu_group_name": "menu-group test 3",
                "external_menu_group_id": "3",
            },
            {
                "menu_group_name": "menu-group test 3",
                "external_menu_group_id": "3",
            },
        ]
    }
    response = do_bulk_add_menu_groups(client, content_team_headers, payload)
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json["status"] == "failed"
    assert response_json["message"] == "Duplicate menu group names found in menu_group_list."
    
    # delete the latest entries added
    db_engine = jqutils.get_db_engine()
    
    query = text("""
        DELETE FROM menu_group
        WHERE menu_group_name IN :menu_group_name_list
    """)
    with db_engine.connect() as conn:
        results = conn.execute(query, menu_group_name_list=menu_group_name_list).rowcount
        assert results, "unable to delete the menu groups"

def test_check_menu_group_name_availability(client, content_team_headers):
    """
    Test: Check menu group name availability
    """
    payload = {
        "menu_group_name": "menu-group test"
    }
    response = do_check_menu_group_name_availability(client, content_team_headers, payload)
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json["status"] == "successful"
    
    response_data = response_json["data"]
    assert response_data["available_p"] == 0

def test_get_menu_group(client, content_team_headers):
    """
    Test: Get menu group
    """
    global menu_group_id
    
    response = do_get_menu_group(client, content_team_headers, menu_group_id)
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json["status"] == "successful"
    
    response_data = response_json["data"]
    assert response_data["menu_group_id"] == menu_group_id
    assert response_data["menu_group_name"] == "menu-group test"
    assert response_data["external_menu_group_id"] == "1"

def test_update_menu_group(client, content_team_headers):
    """
    Test: Update menu group
    """
    global menu_group_id
    
    payload = {
        "menu_group_name": "menu-group test updated",
        "external_menu_group_id": "1",
    }
    response = do_update_menu_group(client, content_team_headers, menu_group_id, payload)
    assert response.status_code == 200

    response_json = response.get_json()
    assert response_json["status"] == "successful"

    response_data = response_json["data"]
    assert response_data["menu_group_id"] == menu_group_id
    
    # validate the updated data
    response = do_get_menu_group(client, content_team_headers, menu_group_id)
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json["status"] == "successful"
    
    response_data = response_json["data"]
    assert response_data["menu_group_id"] == menu_group_id
    assert response_data["menu_group_name"] == payload["menu_group_name"]
    assert response_data["external_menu_group_id"] == payload["external_menu_group_id"]

def test_get_menu_groups(client, content_team_headers, existing_menu_group_count):
    """
    Test: Get all menu groups
    """
    response = do_get_menu_groups(client, content_team_headers)
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json["status"] == "successful"
    
    response_data = response_json["data"]
    expected_count = existing_menu_group_count + 1
    assert "menu_group_list" in response_data, "menu_group_list should be present in response data."
    
    menu_group_list = response_data["menu_group_list"]
    assert len(menu_group_list) == expected_count, f"Menu Group List should have {expected_count} item(s)."

def test_delete_menu_group(client, content_team_headers, existing_menu_group_count):
    """
    Test: Delete menu group
    """
    global menu_group_id
    
    response = do_delete_menu_group(client, content_team_headers, menu_group_id)
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json["status"] == "successful"
    
    response_data = response_json["data"]
    assert response_data["menu_group_id"] == menu_group_id

    # validate that the menu group has been deleted
    response = do_get_menu_groups(client, content_team_headers)
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json["status"] == "successful"
    
    response_data = response_json["data"]
    assert "menu_group_list" in response_data, "menu_group_list should be present in response data."
    
    menu_group_list = response_data["menu_group_list"]
    assert len(menu_group_list) == existing_menu_group_count, f"Menu Group List should have {existing_menu_group_count} item."