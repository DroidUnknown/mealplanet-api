import json

base_api_url = "/api"

##########################
# TEST - BRANDS
##########################
def do_create_menu_publish_request(client, headers, payload):
    """
    Create menu publish request
    """
    response = client.post(base_api_url + "/menu_publish_request", headers=headers, json=payload)
    return response

def do_bulk_create_menu_publish_request(client, headers, payload):
    """
    Bulk create menu publish request
    """
    response = client.post(base_api_url + "/bulk_menu_publish_request", headers=headers, json=payload)
    return response

def do_publish_menu_publish_request(client, headers, menu_publish_request_id, payload):
    """
    Publish menu publish request
    """
    response = client.post(base_api_url + f"/menu_publish_request/{menu_publish_request_id}/publish", headers=headers, json=payload)
    return response

def do_get_menu_publish_requests(client, headers):
    """
    Get menu publish requests
    """
    response = client.get(base_api_url + f"/menu_publish_requests", headers=headers)
    return response

def do_get_menu_publish_request(client, headers, menu_publish_request_id):
    """
    Get one menu publish request
    """
    response = client.get(base_api_url + f"/menu_publish_request/{menu_publish_request_id}", headers=headers)
    return response

##########################
# GLOBALS
##########################
menu_publish_request_id = None

##########################
# TEST CASES
##########################

def test_create_menu_publish_request(client, user_headers):
    """
    Test create menu publish request    
    """

    payload = {
        "auto_publish_p": False,
        "branch_id": 2,
        "request_detail_list": [
            {
                "item_branch_map_id_list": [1],
                "change_list": [
                    {
                        "change_scope": "item",
                        "change_type": "edit",
                        "column_name": "item_name",
                        "old_value": "akkawi cheese",
                        "new_value": "akkawi cheese (packed)"
                    }
                ]
            }
        ]
    }
    response = do_create_menu_publish_request(client, user_headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'create_menu_publish_request'

def test_bulk_create_menu_publish_request(client, user_headers):
    """
    Test bulk create menu publish request    
    """
    payload = {
        "auto_publish_p": False,
        "menu_publish_request_list": [{
            "branch_id": 2,
            "request_detail_list": [
                {
                    "item_branch_map_id_list": [1],
                    "change_list": [
                        {
                            "change_scope": "item",
                            "change_type": "edit",
                            "column_name": "item_name",
                            "old_value": "akkawi cheese",
                            "new_value": "akkawi cheese (packed)"
                        }
                    ]
                }
            ]
        }]
    }
    response = do_bulk_create_menu_publish_request(client, user_headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'bulk_create_menu_publish_request'

def test_get_menu_publish_requests(client, user_headers):
    """
    Test get menu publish requests
    """
    response = do_get_menu_publish_requests(client, user_headers)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_menu_publish_requests'
    
    menu_publish_request_list = j["data"]["menu_publish_request_list"]
    assert len(menu_publish_request_list) > 0, "no menu publish requests found"
    
    global menu_publish_request_id
    menu_publish_request_id = menu_publish_request_list[0]["menu_publish_request_id"]

def test_get_menu_publish_request(client, user_headers):
    """
    Test get one menu publish request
    """
    assert menu_publish_request_id is not None, "menu_publish_request_id is not set"
    response = do_get_menu_publish_request(client, user_headers, menu_publish_request_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_menu_publish_request'