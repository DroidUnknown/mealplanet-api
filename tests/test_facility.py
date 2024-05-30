import json
from random import randint

base_api_url = "/api"

##########################
# TEST - FACILITIES
##########################
def do_get_facilities(client, headers, args):
    """
    Get facilities
    """
    response = client.get(base_api_url + f"/facilities{args}", headers=headers)
    return response

def do_get_facility(client, headers, facility_id):
    """
    Get one facility
    """
    response = client.get(f'{base_api_url}/facility/{facility_id}', headers=headers)
    return response

def do_update_facility(client, headers, facility_id, data):
    """
    Update facility
    """
    response = client.put(f'{base_api_url}/facility/{facility_id}', headers=headers, json=data)
    return response

def do_add_user_to_facility(client,headers,facility_id,data):
    """
    Add user to facility
    """
    response = client.post(f'{base_api_url}/facility/{facility_id}/user', headers=headers, json=data)
    return response

def do_delete_user_facility(client,headers,data):
    """
    Delete user facility
    """
    response = client.delete(f'{base_api_url}/facility/user', headers=headers, json=data)
    return response

def do_add_facility_fulfillment_type_map(client,headers,data):
    """
    Add facility fulfillment type map
    """
    response = client.post(f'{base_api_url}/facility_fulfillment_type_map', headers=headers, json=data)
    return response    

def do_get_facility_fulfillment_type_map(client,headers,facility_fulfillment_type_map_id):
    """
    Get facility fulfillment type map
    """
    response = client.get(f'{base_api_url}/facility_fulfillment_type_map/{facility_fulfillment_type_map_id}', headers=headers)
    return response

def do_get_facility_fulfillment_type_map_by_merchant(client,headers):
    """
    Get facility fulfillment type map by merchant
    """
    response = client.get(f'{base_api_url}/facility_fulfillment_type_map', headers=headers)
    return response

def do_delete_facility_fulfillment_type_map(client,headers,facility_fulfillment_type_map_id):
    """
    Delete facility fulfillment type map
    """
    response = client.delete(f'{base_api_url}/facility_fulfillment_type_map/{facility_fulfillment_type_map_id}', headers=headers)
    return response

def do_get_facility_access_code(client, headers, facility_id):
    """
    Get facility access code
    """
    response = client.get(f'{base_api_url}/facility/{facility_id}/access_code', headers=headers)
    return response

def do_validate_facility_access_code(client, headers, query_string):
    """
    Validate facility access code
    """
    response = client.get(f'{base_api_url}/validate_access_code', headers=headers, query_string=query_string)
    return response

def do_facility_soft_login(client, headers, data):
    """
    Do facility soft login
    """
    response = client.post(base_api_url + "/facility_soft_login", headers=headers, json=data)
    return response

##########################
# TEST CASES
##########################
facility = None

def test_get_facilities(client, headers):
    """
    Test get facilities
    """
    response = do_get_facilities(client, headers, "")
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert len(j["data"]) > 0
    assert j["action"] == 'get_facilities'

    global facility
    facility = j["data"][0]

def test_get_facility(client, headers):
    """
    Test get facility
    """
    global facility
    facility_id = facility["facility_id"]

    response = do_get_facility(client, headers, facility_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["data"]["facility_id"] == facility_id
    assert j["action"] == 'get_facility'

    facility = j["data"]

def test_update_facility(client, headers):
    """
    Test update facility
    """
    global facility
    facility_id = facility["facility_id"]

    data = {
        "facility_name": facility["facility_name"],
        "facility_code": facility["facility_code"],
        "facility_contact_name": facility["facility_contact_name"],
        "facility_contact_phone_nr": facility["facility_contact_phone_nr"],
        "facility_contact_email": facility["facility_contact_email"],
        "facility_trn_id": facility["facility_trn_id"],
        "city_id": facility["city"]["city_id"],
        "country_id": facility["country"]["country_id"],
        "timezone_offset_hours": facility["timezone_offset_hours"],
        "landline_phone_number": facility["landline_phone_number"],
        "latitude": facility["latitude"],
        "longitude": facility["longitude"],
        "address_line_1": facility["address_line_1"],
        "address_line_2": facility["address_line_2"],
        "delivery_range_km": facility["delivery_range_km"],
        "kitchen_display_system_enabled_p": facility["kitchen_display_system_enabled_p"],
        "is_warehouse_facility_p": facility["is_warehouse_facility_p"],
        "enforce_soft_login_p": facility["enforce_soft_login_p"],
        "soft_login_timeout": facility["soft_login_timeout"],
        "supplier_id": facility["supplier"]["supplier_id"],
        "enforce_opening_balance_p": facility["enforce_opening_balance_p"],
        "enforce_closing_balance_p": facility["enforce_closing_balance_p"],
    }

    response = do_update_facility(client, headers, facility_id, data)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'update_facility'

def test_get_facilities_by_city_id(client, headers):
    """
    Test get facilities by city id
    """
    response = do_get_facilities(client, headers, "?city_id=1")
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert len(j["data"]) > 0
    assert j["action"] == 'get_facilities'

def test_do_add_user_to_facility(client,headers):
    data = {
        "user_id_list": [1,2,3,4,5]
    }
    facility_id = 4
    response = do_add_user_to_facility(client,headers,facility_id,data)
    assert response.json['status'] == 'successful'

def test_do_delete_user_facility(client,headers):
    data = {
        "facility_id": 4,
        "user_id":5
    }
    response = do_delete_user_facility(client,headers,data)
    assert response.json['status'] == 'successful'    

def test_do_add_facility_fulfillment_type_map(client,headers):
    data ={
        "facility_fulfillment_type_list": [
            {
                "facility_id": 4,
                "fulfillment_type_id": 1,
                "iblinkmarketplace_enabled_p": 1
            }
        ]
    }
    response = do_add_facility_fulfillment_type_map(client,headers,data)
    assert response.json['status'] == 'successful'

def test_do_get_facility_fulfillment_type_map(client,headers):
    facility_fulfillment_type_map_id = 2
    response = do_get_facility_fulfillment_type_map(client,headers,facility_fulfillment_type_map_id)
    assert response.json['status'] == 'successful'

def test_do_add_facility_fulfillment_type_map_by_merchant(client,user_headers):
    response = do_get_facility_fulfillment_type_map_by_merchant(client,user_headers)
    assert response.json['status'] == 'successful'

def test_do_delete_facility_fulfillment_type_map(client,headers):
    facility_fulfillment_type_map_id = 2
    response = do_delete_facility_fulfillment_type_map(client,headers,facility_fulfillment_type_map_id)
    assert response.json['status'] == 'successful'

def test_do_get_facility_access_code(client, headers):
    global facility
    facility_id = facility["facility_id"]
    response = do_get_facility_access_code(client, headers, facility_id)
    assert response.json['status'] == 'successful'

def test_do_validate_facility_access_code(client, headers):
    query_string = {
        "facility_access_code": "112233"
    }
    response = do_validate_facility_access_code(client, headers, query_string)
    assert response.json['status'] == 'successful'

def test_do_facility_soft_login(client, headers):
    data = {
        "username": "admin",
        "facility_access_code": "112233",
        "latitude": "25.25",
        "longitude": "55.55",
        "high_accuracy_gps_p": True
    }
    response = do_facility_soft_login(client, headers, data)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'facility_soft_login'
    assert j["data"]["facility_id"] == facility["facility_id"]
    assert j["data"]["facility_code"] == facility["facility_code"]
    assert j["data"]["facility_name"] == facility["facility_name"]
    assert j["data"]["session_status"] == 'logged_in'