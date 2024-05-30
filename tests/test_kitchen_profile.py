import json

base_api_url = "/api"

##########################
# TEST - KITCHEN PROFILE
########################## 
def do_add_kitchen_profile(client, content_team_headers, payload):
    """
    ADD KITCHEN PROFILE
    """
    response = client.post(base_api_url + "/kitchen-profile", headers=content_team_headers, json=payload)
    return response

def do_get_kitchen_profile(client, content_team_headers, kitchen_profile_id):
    """
    GET KITCHEN PROFILE
    """
    response = client.get(base_api_url + f"/kitchen-profile/{kitchen_profile_id}", headers=content_team_headers)
    return response

def do_update_kitchen_profile(client, content_team_headers, kitchen_profile_id, payload):
    """
    UPDATE KITCHEN PROFILE
    """
    response = client.put(base_api_url + f"/kitchen-profile/{kitchen_profile_id}", headers=content_team_headers, json=payload)
    return response

def do_delete_kitchen_profile(client, content_team_headers, kitchen_profile_id):
    """
    DELETE KITCHEN PROFILE
    """
    response = client.delete(base_api_url + f"/kitchen-profile/{kitchen_profile_id}", headers=content_team_headers)
    return response

def do_get_kitchen_profile_list(client, content_team_headers):
    """
    GET KITCHEN PROFILE LIST
    """
    response = client.get(base_api_url + "/kitchen-profiles", headers=content_team_headers)
    return response

##########################
# TEST CASES
########################## 

def test_kitchen_profile(client, content_team_headers):
    """
    Test: Add Kitchen profile
    """
    payload = {
        "external_kitchen_profile_id": "111",
        "brand_profile_id": 2,
        "kitchen_name": "satwa"
    }
    response = do_add_kitchen_profile(client, content_team_headers, payload)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    kitchen_profile_id = response_data["kitchen_profile_id"]

    """
    Test: Get Kitchen profile
    """
    response = do_get_kitchen_profile(client, content_team_headers, kitchen_profile_id)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data["kitchen_name"] == "satwa"

    """
    Test: Update Kitchen profile
    """
    payload = {
        "kitchen_name": "majaz"
    }
    response = do_update_kitchen_profile(client, content_team_headers, kitchen_profile_id, payload)
    assert response.status_code == 200
    
    """
    Test: Get Kitchen profile
    """
    response = do_get_kitchen_profile(client, content_team_headers, kitchen_profile_id)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data["kitchen_name"] == "majaz"

    """
    Test: Get Kitchen profile List
    """
    response = do_get_kitchen_profile_list(client, content_team_headers)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert len(response_data) == 1, "Kitchen-profile List should have 1 item."

    """
    Test: Delete Kitchen profile
    """
    response = do_delete_kitchen_profile(client, content_team_headers, kitchen_profile_id)
    assert response.status_code == 200

    """
    Test: Get Kitchen profile List
    """
    response = do_get_kitchen_profile_list(client, content_team_headers)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert len(response_data) == 0, "Kitchen-profile List should have 0 item."
    
    """
    Test: Add Kitchen profile
    """
    payload = {
        "external_kitchen_profile_id": "111",
        "brand_profile_id": 2,
        "kitchen_name": "satwa"
    }
    response = do_add_kitchen_profile(client, content_team_headers, payload)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    kitchen_profile_id = response_data["kitchen_profile_id"]