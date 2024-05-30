import json

base_api_url = "/api"

##########################
# TEST - STATION
########################## 
def do_get_stations(client, headers, merchant_id=None):
    """
    Get Stations
    """
    url = base_api_url + "/stations"
    if merchant_id:
        url += f"?merchant_id={merchant_id}"
    response = client.get(url, headers=headers)
    return response

def do_get_one_station(client, headers, station_id):
    """
    Get One Station
    """
    response = client.get(base_api_url + f"/station/{station_id}", headers=headers)
    return response

def do_add_station(client, headers, payload):
    """
    Add One Station
    """
    response = client.post(base_api_url + "/station", headers=headers, json=payload)
    return response

def do_update_station(client, headers, station_id, payload):
    """
    Update Station
    """
    response = client.put(base_api_url + f"/station/{station_id}", headers=headers, json=payload)
    return response

def do_delete_station(client, headers, station_id):
    """
    Delete Station
    """
    response = client.delete(base_api_url + f"/station/{station_id}", headers=headers)
    return response

def do_add_station_rule(client, headers, payload):
    """
    Add Station Rule
    """
    response = client.post(base_api_url + f"/station_rule", headers=headers, json=payload)
    return response

def do_update_station_rule(client, headers, station_rule_id, payload):
    """
    Update Station Rule
    """
    response = client.put(base_api_url + f"/station_rule/{station_rule_id}", headers=headers, json=payload)
    return response

def do_delete_station_rule(client, headers, station_rule_id):
    """
    Delete Station Rule
    """
    response = client.delete(base_api_url + f"/station_rule/{station_rule_id}", headers=headers)
    return response

##########################
# TEST CASES
##########################
station_id = None
station_rule_id = None

def test_add_station(client, headers):
    """
    Test Add Station
    """
    payload = {
        "facility_id": 1,
        "station_name": None,
        "station_description": None,
        "station_access_code": None,
        "preparation_station_p": 1,
        "dispatch_station_p": 0,
        "station_rule_list": [{
            "rule_type": "preparation",
            "station_rule_expression": "facility(1)"
        }],
        "username": "default-001",
        "password": "123456",
    }
    response = do_add_station(client, headers, payload)
    assert response.status_code == 200
    response_body = response.json
    assert response_body["status"] == "successful"
    assert response_body["action"] == "add_station"
    assert response_body["data"]["station_id"]
    assert response_body["data"]["station_code"]
    
    global station_id
    station_id = response_body["data"]["station_id"]

def test_get_stations(client, headers):
    """
    Test Get Stations
    """
    merchant_id = 1
    response = do_get_stations(client, headers, merchant_id)
    assert response.status_code == 200
    response_body = response.json
    assert response_body["status"] == "successful"
    assert response_body["action"] == "get_stations"
    assert len(response_body["data"]) > 0

def test_get_one_station(client, headers):
    """
    Test Get One Station
    """
    response = do_get_one_station(client, headers, station_id)
    assert response.status_code == 200
    response_body = response.json
    assert response_body["status"] == "successful"
    assert response_body["action"] == "get_one_station"
    assert response_body["data"]["station_id"] == station_id
    assert len(response_body["data"]["station_rule_list"]) > 0
    
    global station_rule_id
    station_rule_id = response_body["data"]["station_rule_list"][0]["station_rule_id"]

def test_update_station(client, headers):
    """
    Test Update Station
    """
    payload = {
        "station_name": "Station 001",
        "station_description": "Station 001 Description",
        "station_rule": "facility(1)",
        "station_access_code": None,
        "default_p": 1,
        "preparation_station_p": 1,
        "dispatch_station_p": 1,
    }
    response = do_update_station(client, headers, station_id, payload)
    assert response.status_code == 200
    response_body = response.json
    assert response_body["status"] == "successful"
    assert response_body["action"] == "update_station"
    assert response_body["data"]["station_id"] == station_id

    response = do_get_one_station(client, headers, station_id)
    assert response.status_code == 200
    response_body = response.json
    
    assert response_body["status"] == "successful"
    assert response_body["action"] == "get_one_station"
    assert response_body["data"]["station_id"] == station_id
    assert response_body["data"]["station_name"] == payload["station_name"]
    assert response_body["data"]["station_description"] == payload["station_description"]

def test_update_station_rule(client, headers):
    """
    Test Update Station Rule
    """
    payload = {
        "rule_type": "preparation",
        "station_rule_expression": "facility(1) and item_category(1)",
    }
    response = do_update_station_rule(client, headers, station_rule_id, payload)
    assert response.status_code == 200
    response_body = response.json
    assert response_body["status"] == "successful"
    assert response_body["action"] == "update_station_rule"
    assert response_body["data"]["station_rule_id"] == station_rule_id

    response = do_get_one_station(client, headers, station_id)
    assert response.status_code == 200
    response_body = response.json
    assert response_body["status"] == "successful"
    assert response_body["action"] == "get_one_station"
    assert response_body["data"]["station_id"] == station_id
    assert response_body["data"]["station_rule_list"]
    
    station_rule_list = response_body["data"]["station_rule_list"]
    
    for station_rule in station_rule_list:
        if station_rule["station_rule_id"] == station_rule_id:
            assert station_rule["station_rule_expression"] == payload["station_rule_expression"]
            break

def test_add_station_rule(client, headers):
    """
    Test Add Station Rule
    """
    payload = {
        "station_id": station_id,
        "station_rule_list": [{
            "rule_type": "dispatch",
            "station_rule_expression": "facility(1) and item_category(1)",
        }]
    }
    response = do_add_station_rule(client, headers, payload)
    assert response.status_code == 200
    response_body = response.json
    assert response_body["status"] == "successful"
    assert response_body["action"] == "add_station_rule"
    assert len(response_body["data"]["station_rule_id_list"]) == 1
    
    global station_rule_id
    station_rule_id = response_body["data"]["station_rule_id_list"][0]

    response = do_get_one_station(client, headers, station_id)
    assert response.status_code == 200
    response_body = response.json
    assert response_body["status"] == "successful"
    assert response_body["action"] == "get_one_station"
    assert response_body["data"]["station_id"] == station_id
    assert response_body["data"]["station_rule_list"]
    
    station_rule_list = response_body["data"]["station_rule_list"]
    
    for station_rule in station_rule_list:
        if station_rule["station_rule_id"] == station_rule_id:
            assert station_rule["station_rule_expression"] == payload["station_rule_list"][0]["station_rule_expression"]
            break

def test_delete_station_rule(client, headers):
    """
    Test Delete Station Rule
    """
    response = do_delete_station_rule(client, headers, station_rule_id)
    assert response.status_code == 200
    response_body = response.json
    assert response_body["status"] == "successful"
    assert response_body["action"] == "delete_station_rule"
    assert response_body["data"]["station_rule_id"] == station_rule_id

def test_delete_station(client, headers):
    """
    Test Delete Station
    """
    response = do_delete_station(client, headers, station_id)
    assert response.status_code == 200
    response_body = response.json
    assert response_body["status"] == "successful"
    assert response_body["action"] == "delete_station"
    assert response_body["data"]["station_id"] == station_id