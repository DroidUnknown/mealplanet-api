import json

base_api_url = "/api"

##########################
# TEST - DELIVERY PROVIDER PROFILE
########################## 
def do_add_delivery_provider_profile(client, user_headers, payload):
    """
    ADD DELIVERY PROVIDER PROFILE
    """
    response = client.post(base_api_url + "/delivery-provider-profile", headers=user_headers, json=payload)
    return response

def do_get_delivery_provider_profile(client, user_headers, delivery_provider_profile_id):
    """
    GET DELIVERY PROVIDER PROFILE
    """
    response = client.get(base_api_url + f"/delivery-provider-profile/{delivery_provider_profile_id}", headers=user_headers)
    return response

def do_update_delivery_provider_profile(client, user_headers, delivery_provider_profile_id, payload):
    """
    UPDATE DELIVERY PROVIDER PROFILE
    """
    response = client.put(base_api_url + f"/delivery-provider-profile/{delivery_provider_profile_id}", headers=user_headers, json=payload)
    return response

def do_delete_delivery_provider_profile(client, user_headers, delivery_provider_profile_id):
    """
    DELETE DELIVERY PROVIDER PROFILE
    """
    response = client.delete(base_api_url + f"/delivery-provider-profile/{delivery_provider_profile_id}", headers=user_headers)
    return response

def do_get_delivery_provider_profile_list(client, user_headers):
    """
    GET DELIVERY PROVIDER PROFILE LIST
    """
    response = client.get(base_api_url + "/delivery-provider-profiles", headers=user_headers)
    return response

##########################
# TEST CASES
########################## 

def test_delivery_provider_profile(client, user_headers):
    """
    Test: Add Delivery provider profile
    """
    payload = {
        "external_delivery_provider_profile_id": "1",
        "delivery_provider_name": "careem"
    }
    response = do_add_delivery_provider_profile(client, user_headers, payload)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    delivery_provider_profile_id = response_data["delivery_provider_profile_id"]

    """
    Test: Get Delivery provider profile
    """
    response = do_get_delivery_provider_profile(client, user_headers, delivery_provider_profile_id)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data["delivery_provider_name"] == "careem"

    """
    Test: Update Delivery provider profile
    """
    payload = {
        "delivery_provider_name": "uber"
    }
    response = do_update_delivery_provider_profile(client, user_headers, delivery_provider_profile_id, payload)
    assert response.status_code == 200
    
    """
    Test: Get Delivery provider profile
    """
    response = do_get_delivery_provider_profile(client, user_headers, delivery_provider_profile_id)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data["delivery_provider_name"] == "uber"

    """
    Test: Get Delivery provider profile List
    """
    response = do_get_delivery_provider_profile_list(client, user_headers)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert len(response_data) == 1, "Delivery provider profile List should have 1 item."

    """
    Test: Delete Delivery provider profile
    """
    response = do_delete_delivery_provider_profile(client, user_headers, delivery_provider_profile_id)
    assert response.status_code == 200

    """
    Test: Get Delivery provider profile List
    """
    response = do_get_delivery_provider_profile_list(client, user_headers)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert len(response_data) == 0, "Delivery provider profile List should have 0 item."
    
    """
    Test: Add Delivery provider profile
    """
    payload = {
        "external_delivery_provider_profile_id": "1",
        "delivery_provider_name": "careem"
    }
    response = do_add_delivery_provider_profile(client, user_headers, payload)
    assert response.status_code == 201
    response_data = json.loads(response.data)
    delivery_provider_profile_id = response_data["delivery_provider_profile_id"]