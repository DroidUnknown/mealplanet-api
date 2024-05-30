import json

base_api_url = "/api"

##########################
# TEST - SERVICE
########################## 
def do_get_services(client, headers):
    """
    Get Services
    """
    response = client.get(base_api_url + "/services", headers=headers)
    return response

def do_get_services_by_merchant(client, headers, merchant_id):
    """
    Get Services By Merchant
    """
    response = client.get(f"{base_api_url}/merchant/{merchant_id}/services", headers=headers)
    return response

def do_update_service_for_merchant(client, headers, merchant_id, payload):
    """
    Update Service For Merchant
    """
    response = client.put(f"{base_api_url}/merchant/{merchant_id}/service", headers=headers, json=payload)
    return response

##########################
# TEST CASES
########################## 
def test_get_services(client, headers):
    """
    Test get services
    """
    response = do_get_services(client, headers)
    assert response.status_code == 200
    response_body = json.loads(response.data)
    
    assert response_body["status"] == 'successful'
    assert response_body["action"] == 'get_services'
    
    data = response_body["data"]
    assert len(data) > 0, "No services found"

def test_get_services_by_merchant(client, headers):
    """
    Test get services by merchant
    """
    merchant_id = 1
    response = do_get_services_by_merchant(client, headers, merchant_id)
    assert response.status_code == 200
    response_body = json.loads(response.data)
    
    assert response_body["status"] == 'successful'
    assert response_body["action"] == 'get_services_by_merchant'
    
    data = response_body["data"]
    assert len(data) > 0, "No services found"

def test_update_service_for_merchant(client, headers):
    """
    Test update service for merchant
    """
    merchant_id = 1
    payload = {
        "service_id": 3,
        "enabled_p": 1,
        "billing_suspend_p": 0,
        "billing_type": "monthly",
        "rate_fixed_amount": 0,
        "rate_dynamic_amount": 10,
        "discount_amount": 0,
        "discount_value": 0,
        "discount_percentage_p": 0,
        "currency_id": 1,
        "all_facility_p": 1,
        "facility_id_list": []
    }
    response = do_update_service_for_merchant(client, headers, merchant_id, payload)
    assert response.status_code == 200
    response_body = json.loads(response.data)
    
    assert response_body["status"] == 'successful'
    assert response_body["action"] == 'update_service_for_merchant'
    
    data = response_body["data"]
    assert data["merchant_service_map_id"], "No merchant service map id found"