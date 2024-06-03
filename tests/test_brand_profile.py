import json

base_api_url = "/api"

##########################
# TEST - BRAND PROFILE
########################## 
def do_check_brand_profile_availability(client, headers, payload):
    """
    CHECK BRAND PROFILE AVAILABILITY
    """
    response = client.post(base_api_url + "/brand-profile/availability", headers=headers, json=payload)
    return response

def do_add_brand_profile(client, headers, payload):
    """
    ADD BRAND PROFILE
    """
    response = client.post(base_api_url + "/brand-profile", headers=headers, json=payload)
    return response

def do_get_brand_profile(client, headers, brand_profile_id):
    """
    GET BRAND PROFILE
    """
    response = client.get(base_api_url + f"/brand-profile/{brand_profile_id}", headers=headers)
    return response

def do_update_brand_profile(client, headers, brand_profile_id, payload):
    """
    UPDATE BRAND PROFILE
    """
    response = client.put(base_api_url + f"/brand-profile/{brand_profile_id}", headers=headers, json=payload)
    return response

def do_delete_brand_profile(client, headers, brand_profile_id):
    """
    DELETE BRAND PROFILE
    """
    response = client.delete(base_api_url + f"/brand-profile/{brand_profile_id}", headers=headers)
    return response

def do_get_brand_profile_list(client, headers):
    """
    GET BRAND PROFILE LIST
    """
    response = client.get(base_api_url + "/brand-profiles", headers=headers)
    return response

def do_get_plans_by_brand_profile(client, headers, brand_profile_id):
    """
    GET PLANS BY BRAND PROFILE
    """
    response = client.get(base_api_url + f"/brand-profile/{brand_profile_id}/plans", headers=headers)
    return response

##########################
# TEST CASES
########################## 
brand_profile_id = None

def test_add_brand_profile(client, content_team_headers):
    """
    Test: Add Brand Profile
    """
    payload = {
        "external_brand_profile_id": "1",
        "brand_name": "qoqo",
        "plan_list": [
            {
                "plan_name": "plan1",
                "external_plan_id": "1",
                "menu_group_id_list": [1, 2]
            }
        ]
    }
    response = do_add_brand_profile(client, content_team_headers, payload)
    assert response.status_code == 200

    response_json = response.get_json()
    assert response_json["status"] == "successful"
    assert response_json["action"] == "add_brand_profile"

    global brand_profile_id
    response_data = response_json["data"]
    brand_profile_id = response_data["brand_profile_id"]


def test_brand_profile_availability(client, content_team_headers):
    """
    Test: Check Brand Profile Availability
    """
    payload = {
        "external_brand_profile_id": "1"
    }
    response = do_check_brand_profile_availability(client, content_team_headers, payload)
    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json["status"] == "successful"
    assert response_json["action"] == "check_brand_profile_availability"

    response_data = response_json["data"]
    assert response_data["availability_p"] == 0

def test_get_brand_profile(client, content_team_headers):
    """
    Test: Get Brand Profile
    """
    response = do_get_brand_profile(client, content_team_headers, brand_profile_id)
    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json["status"] == "successful"
    assert response_json["action"] == "get_brand_profile"

    response_data = response_json["data"]
    assert response_data["brand_name"] == "qoqo"

def test_update_brand_profile(client, content_team_headers):
    """
    Test: Update Brand Profile
    """
    payload = {
        "external_brand_profile_id": "2",
        "brand_name": "tolpin"
    }
    response = do_update_brand_profile(client, content_team_headers, brand_profile_id, payload)
    assert response.status_code == 200
    response_json = json.loads(response.data)

    assert response_json["status"] == "successful"
    assert response_json["action"] == "update_brand_profile"

    """
    Test: Get Brand Profile
    """
    response = do_get_brand_profile(client, content_team_headers, brand_profile_id)
    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json["status"] == "successful"
    assert response_json["action"] == "get_brand_profile"

    response_data = response_json["data"]
    assert response_data["brand_name"] == "tolpin"

def test_get_brand_profile_list(client, content_team_headers):
    """
    Test: Get Brand Profile List
    """
    response = do_get_brand_profile_list(client, content_team_headers)
    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json["status"] == "successful"
    assert response_json["action"] == "get_brand_profiles"
    response_data = response_json["data"]
    assert len(response_data) == 1, "Brand Profile List should have 1 item."

def test_delete_brand_profile(client, content_team_headers):
    """
    Test: Delete Brand Profile
    """
    response = do_delete_brand_profile(client, content_team_headers, brand_profile_id)
    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json["status"] == "successful"
    assert response_json["action"] == "delete_brand_profile"

    """
    Test: Get Brand Profile List
    """
    response = do_get_brand_profile_list(client, content_team_headers)
    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json["status"] == "successful"
    assert response_json["action"] == "get_brand_profiles"
    response_data = response_json["data"]
    assert len(response_data) == 0, "Brand Profile List should have 0 item."

def test_get_plans_by_brand_profile(client, content_team_headers):
    """
    Test: Add Brand Profile
    """
    payload = {
        "external_brand_profile_id": "1",
        "brand_name": "qoqo",
        "plan_list": [
            {
                "plan_name": "plan1",
                "external_plan_id": "1",
                "menu_group_id_list": [1, 2]
            }
        ]
    }
    response = do_add_brand_profile(client, content_team_headers, payload)
    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json["status"] == "successful"
    assert response_json["action"] == "add_brand_profile"
    response_data = response_json["data"]
    brand_profile_id = response_data["brand_profile_id"]
    assert brand_profile_id