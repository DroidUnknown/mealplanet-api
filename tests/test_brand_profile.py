import json

base_api_url = "/api"

##########################
# TEST - BRAND PROFILE
########################## 
def do_add_brand_profile(client, user_headers, payload):
    """
    ADD BRAND PROFILE
    """
    response = client.post(base_api_url + "/brand-profile", headers=user_headers, json=payload)
    return response

def do_get_brand_profile(client, user_headers, brand_profile_id):
    """
    GET BRAND PROFILE
    """
    response = client.get(base_api_url + f"/brand-profile/{brand_profile_id}", headers=user_headers)
    return response

def do_update_brand_profile(client, user_headers, brand_profile_id, payload):
    """
    UPDATE BRAND PROFILE
    """
    response = client.put(base_api_url + f"/brand-profile/{brand_profile_id}", headers=user_headers, json=payload)
    return response

def do_delete_brand_profile(client, user_headers, brand_profile_id):
    """
    DELETE BRAND PROFILE
    """
    response = client.delete(base_api_url + f"/brand-profile/{brand_profile_id}", headers=user_headers)
    return response

def do_get_brand_profile_list(client, user_headers):
    """
    GET BRAND PROFILE LIST
    """
    response = client.get(base_api_url + "/brand-profiles", headers=user_headers)
    return response

def do_get_plans_by_brand_profile(client, user_headers, brand_profile_id):
    """
    GET PLANS BY BRAND PROFILE
    """
    response = client.get(base_api_url + f"/brand-profile/{brand_profile_id}/plans", headers=user_headers)
    return response

##########################
# TEST CASES
########################## 

def test_brand_profile(client, user_headers):
    """
    Test: Add Brand Profile
    """
    payload = {
        "external_brand_profile_id": "1",
        "brand_name": "qoqo"
    }
    response = do_add_brand_profile(client, user_headers, payload)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    brand_profile_id = response_data["brand_profile_id"]

    """
    Test: Get Brand Profile
    """
    response = do_get_brand_profile(client, user_headers, brand_profile_id)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data["brand_name"] == "qoqo"

    """
    Test: Update Brand Profile
    """
    payload = {
        "brand_name": "tolpin"
    }
    response = do_update_brand_profile(client, user_headers, brand_profile_id, payload)
    assert response.status_code == 200
    
    """
    Test: Get Brand Profile
    """
    response = do_get_brand_profile(client, user_headers, brand_profile_id)
    assert response.status_code == 200

    """
    Test: Get Brand Profile List
    """
    response = do_get_brand_profile_list(client, user_headers)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert len(response_data) == 1, "Brand Profile List should have 1 item."

    """
    Test: Delete Brand Profile
    """
    response = do_delete_brand_profile(client, user_headers, brand_profile_id)
    assert response.status_code == 200

    """
    Test: Get Brand Profile List
    """
    response = do_get_brand_profile_list(client, user_headers)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert len(response_data) == 0, "Brand Profile List should have 0 item."
    
    """
    Test: Add Brand Profile
    """
    payload = {
        "external_brand_profile_id": "1",
        "brand_name": "qoqo"
    }
    response = do_add_brand_profile(client, user_headers, payload)
    assert response.status_code == 201
    response_data = json.loads(response.data)
    brand_profile_id = response_data["brand_profile_id"]