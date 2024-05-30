import json

base_api_url = "/api"

#------------------------------------------------------------------------------------------------------

def do_get_loyalty_rewards_for_merchant(client, headers, merchant_id):
    """
    Get loyalty rewards for merchant
    """
    response = client.get(base_api_url + f"/merchant/{merchant_id}/loyalty-rewards", headers=headers)
    return response

def do_get_loyalty_rewards_for_customer(client, headers, customer_id):
    """
    Get loyalty rewards for customer
    """
    response = client.get(base_api_url + f"/customer/{customer_id}/loyalty-rewards", headers=headers)
    return response

def do_add_loyalty_reward(client, headers, data):
    """
    Add loyalty reward
    """
    cand_headers = headers.copy()
    cand_headers["Content-Type"] = "multipart/form-data"
    response = client.post(base_api_url + "/loyalty-reward", headers=cand_headers, data=data)
    return response

def do_get_loyalty_reward(client, headers, loyalty_reward_id):
    """
    Get loyalty reward
    """
    response = client.get(base_api_url + f"/loyalty-reward/{loyalty_reward_id}", headers=headers)
    return response

def do_update_loyalty_reward(client, headers, loyalty_reward_id, data):
    """
    Update loyalty reward
    """
    cand_headers = headers.copy()
    cand_headers["Content-Type"] = "multipart/form-data"
    response = client.put(base_api_url + f"/loyalty-reward/{loyalty_reward_id}", headers=cand_headers, data=data)
    return response

def do_delete_loyalty_reward(client, headers, loyalty_reward_id):
    """
    Delete loyalty reward
    """
    response = client.delete(base_api_url + f"/loyalty-reward/{loyalty_reward_id}", headers=headers)
    return response

############
# GLOBALS
############
loyalty_reward_id = None

##########################
# TEST - Loyalty Reward
##########################

def test_add_loyalty_reward(client, user_headers):
    """
    Test add loyalty reward
    """
    with open('tests/testdata/test_images/menu-chocolate-cake.jpg', 'rb') as image_data:
        data = {
            "merchant_id": 1,
            "loyalty_reward_name": "Test Loyalty Reward",
            "loyalty_reward_description": "Test Loyalty Reward Description",
            "loyalty_reward_type_id": 1,
            "loyalty_reward_value": 10,
            "expiry_duration": None,
            "expiry_duration_measurement_id": None,
            "loyalty_reward_image": image_data
        }
        response = do_add_loyalty_reward(client, user_headers, data)
        assert response.status_code == 200
    
    response_data = json.loads(response.data)
    assert response_data["action"] == "add_loyalty_reward"
    assert response_data["status"] == "successful"
    
    data = response_data["data"]
    assert data["loyalty_reward_id"] is not None
    
    global loyalty_reward_id
    loyalty_reward_id = data["loyalty_reward_id"]

def test_get_loyalty_rewards_for_merchant(client, user_headers):
    """
    Test get loyalty rewards for merchant
    """
    merchant_id = 1
    response = do_get_loyalty_rewards_for_merchant(client, user_headers, merchant_id)
    assert response.status_code == 200
    
    response_data = json.loads(response.data)
    assert response_data["action"] == "get_loyalty_rewards_for_merchant"
    assert response_data["status"] == "successful"
    
    data = response_data["data"]
    assert len(data) > 0

def test_get_loyalty_rewards_for_customer(client, user_headers):
    """
    Test get loyalty rewards for customer
    """
    customer_id = 1
    response = do_get_loyalty_rewards_for_customer(client, user_headers, customer_id)
    assert response.status_code == 200
    
    response_data = json.loads(response.data)
    assert response_data["action"] == "get_loyalty_rewards_for_customer"
    assert response_data["status"] == "successful"
    
    data = response_data["data"]
    assert len(data) > 0

def test_get_loyalty_reward(client, user_headers):
    """
    Test get loyalty reward
    """
    global loyalty_reward_id
    response = do_get_loyalty_reward(client, user_headers, loyalty_reward_id)
    assert response.status_code == 200
    
    response_data = json.loads(response.data)
    assert response_data["action"] == "get_loyalty_reward"
    assert response_data["status"] == "successful"
    
    data = response_data["data"]
    assert data["loyalty_reward_id"] == loyalty_reward_id

def test_update_loyalty_reward(client, user_headers):
    """
    Test update loyalty reward
    """
    global loyalty_reward_id
    data = {
        "loyalty_reward_name": "Test Loyalty Reward Updated",
        "loyalty_reward_description": "Test Loyalty Reward Description Updated",
        "loyalty_reward_type_id": 1,
        "loyalty_reward_value": 20,
        "expiry_duration": None,
        "expiry_duration_measurement_id": None,
    }
    response = do_update_loyalty_reward(client, user_headers, loyalty_reward_id, data)
    assert response.status_code == 200
    
    response_data = json.loads(response.data)
    assert response_data["action"] == "update_loyalty_reward"
    assert response_data["status"] == "successful"
    
    data = response_data["data"]
    assert data["loyalty_reward_id"] == loyalty_reward_id

def test_delete_loyalty_reward(client, user_headers):
    """
    Test delete loyalty reward
    """
    global loyalty_reward_id
    response = do_delete_loyalty_reward(client, user_headers, loyalty_reward_id)
    assert response.status_code == 200
    
    response_data = json.loads(response.data)
    assert response_data["action"] == "delete_loyalty_reward"
    assert response_data["status"] == "successful"
    
    data = response_data["data"]
    assert data["loyalty_reward_id"]
    
    loyalty_reward_id = None