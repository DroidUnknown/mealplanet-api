from utils import jqutils
import pytest
import json
base_api_url = "/api"

def do_add_stock_return(client, headers, data):
    url = base_api_url + "/stock_return"
    response = client.post(url, json=data, headers=headers)
    return response

def do_get_stock_return(client, headers, stock_return_id):
    url = base_api_url + f"/stock_return?stock_return_id={stock_return_id}"
    response = client.get(url, headers=headers)
    return response

def do_get_stock_returns(client, headers, data):
    url = base_api_url + "/stock_returns"
    response = client.post(url, json=data, headers=headers)
    return response

####################
# TEST CASES
####################

stock_return_id = None

def test_do_add_stock_return(client, headers):
    data = {
        "stock_return_timestamp": "2021-01-01 00:00:00",
        "facility_id": 1,
        "supplier_id": 1,
        "stock_request_id": 2,
        "stock_item_list": [
            {
                "stock_item_id": 1,
                "quantity": 2,
                "stock_item_packaging_map_id": 1,
                "return_reason_id": 1,
                "cost_per_pack": 100.00,
                "supplier_id": 1,
                "comment": "Returned 2 items"
            },
            {
                "stock_item_id": 2,
                "quantity": 2,
                "stock_item_packaging_map_id": 4,
                "return_reason_id": 1,
                "cost_per_pack": 100.00,
                "supplier_id": 1,
                "comment": "Returned 2 items"
            }
        ]
    }

    response = do_add_stock_return(client, headers, data)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'add_stock_return'
    global stock_return_id
    stock_return_id = j["stock_return_id"]
    
def test_do_get_stock_return(client, headers):
    global stock_return_id
    response = do_get_stock_return(client, headers, stock_return_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_stock_return'
    assert j["data"]["stock_return_id"] == stock_return_id
    
def test_do_get_stock_returns(client, headers):
    data = {
        "facility_id_list": None,
        "supplier_id_list": None,
        "start_date": None,
        "end_date": None
    }
    response = do_get_stock_returns(client, headers, data)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'stock_item_return'
    assert len(j["data"]) > 0