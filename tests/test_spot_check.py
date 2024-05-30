import json

base_api_url = "/api"

def do_spot_check(client, headers, payload):
    """
    Spot Check
    """
    response = client.post(base_api_url + "/spot-check", headers=headers, json=payload)
    return response

def do_get_spot_checks(client, headers, payload):
    """
    Get Spot Check
    """
    response = client.post(base_api_url + "/spot-checks", headers=headers, json=payload)
    return response

def do_get_spot_check(client, headers, spot_check_id):
    """
    Get Spot Check
    """
    response = client.get(base_api_url + "/spot-check/"+ str(spot_check_id), headers=headers)
    return response

################
# TEST CASES
################
spot_check_id = None

def test_spot_check(client, headers):
    """
    Test spot check
    """
    payload = {
        "facility_id": 1,
        "spot_check_timestamp": "2021-01-01 00:00:00",
        "stock_item_list": [
            {
                "stock_item_id": 1,
                "theoretical_quantity": 10,
                "spot_check_quantity": 8,
                "measurement_id": 1,
                "spot_check_notes": "Missing 2 items"
            },
            {
                "stock_item_id": 2,
                "theoretical_quantity": 20,
                "spot_check_quantity": 18,
                "measurement_id": 1,
                "spot_check_notes": "Missing 2 items"
            }
        ]
    }

    response = do_spot_check(client, headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'add_spot_check'
    global spot_check_id
    spot_check_id = j["spot_check_id"]
    

def test_get_spot_checks(client, headers):
    """
    Test get spot checks
    """
    payload = {
        "facility_id_list": [1],
        "to_timestamp": "2021-01-01 00:00:00",
        "from_timestamp": "2021-01-01 00:00:00",
    }

    response = do_get_spot_checks(client, headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_spot_checks'
    assert len(j["data"]) > 0
    
def test_get_spot_check(client, headers):
    """
    Test get spot check
    """
    response = do_get_spot_check(client, headers, spot_check_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_spot_check'
    spot_check = j["data"]
    assert spot_check["spot_check_id"] == spot_check_id
    assert len(spot_check["stock_item_list"]) > 0