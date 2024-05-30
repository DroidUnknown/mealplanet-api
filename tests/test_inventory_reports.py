import json
from datetime import datetime, timedelta

base_api_url = "/api"

##########################
# TEST - INVENTORY REPORTS
##########################
def do_get_inventory_overview(client, headers, payload):
    response = client.post(base_api_url + '/inventory-report/inventory-overview', headers=headers, json=payload)
    return response

def do_get_stock_item_purchase(client, headers, payload):
    response = client.post(base_api_url + '/inventory-report/stock-item-purchase', headers=headers, json=payload)
    return response

def do_get_stock_item_purchase_by_supplier(client, headers, payload):
    response = client.post(base_api_url + '/inventory-report/stock-item-purchase-by-supplier', headers=headers, json=payload)
    return response

def do_get_stock_item_transfer(client, headers, payload):
    response = client.post(base_api_url + '/inventory-report/stock-item-transfer', headers=headers, json=payload)
    return response

def do_get_stock_item_transfer_detail(client, headers, payload):
    response = client.post(base_api_url + '/inventory-report/stock-item-transfer-detail', headers=headers, json=payload)
    return response

def do_get_stock_adjustment(client, headers, payload):
    response = client.post(base_api_url + '/inventory-report/stock-adjustment', headers=headers, json=payload)
    return response

def do_get_stock_adjustment_detail(client, headers, payload):
    response = client.post(base_api_url + '/inventory-report/stock-adjustment-detail', headers=headers, json=payload)
    return response

def do_get_stock_level(client, headers, payload):
    response = client.post(base_api_url + '/inventory-report/stock-level', headers=headers, json=payload)
    return response

def do_get_stock_consumption(client, headers, payload):
    response = client.post(base_api_url + '/inventory-report/stock-consumption', headers=headers, json=payload)
    return response

def do_get_stock_consumption_detail(client, headers, payload):
    response = client.post(base_api_url + '/inventory-report/stock-consumption-detail', headers=headers, json=payload)
    return response

def do_get_stock_wastage(client, headers, payload):
    response = client.post(base_api_url + '/inventory-report/stock-wastage', headers=headers, json=payload)
    return response

def do_get_stock_wastage_detail(client, headers, payload):
    response = client.post(base_api_url + '/inventory-report/stock-wastage-detail', headers=headers, json=payload)
    return response

def do_get_master_pricing_list(client, headers, payload):
    response = client.post(base_api_url + '/inventory-report/master-pricing-list', headers=headers, json=payload)
    return response

##########################
# TEST CASES
##########################

def test_do_get_inventory_overview(client, user_headers):
    payload = {
        "facility_id": 1,
        "stock_category_id_list": [],
        "start_date": "2021-01-01",
        "end_date": "2051-12-31"
    }
    response = do_get_inventory_overview(client, user_headers, payload)
    assert response.status_code == 200
    
    response_body = json.loads(response.data)
    assert response_body["status"] == 'successful'
    assert response_body["action"] == 'get_inventory_overview'
    
    data = response_body["data"]
    response_data = data["data"]
    assert len(response_data) > 0
    
    response_currency = data["currency"]
    assert response_currency["currency_id"] == 1
    assert response_currency["currency_alpha_3"] == 'AED'
    
def test_do_get_stock_item_purchase(client, user_headers):
    payload = {
        "facility_id_list": [],
        "stock_category_id_list": [],
        "start_date": datetime.now().strftime("%Y-%m-%d"),
        "end_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    }
    response = do_get_stock_item_purchase(client, user_headers, payload)
    assert response.status_code == 200
    
    response_body = json.loads(response.data)
    assert response_body["status"] == 'successful'
    assert response_body["action"] == 'get_stock_item_purchase'
    
    data = response_body["data"]
    response_data = data["data"]
    assert len(response_data) > 0
    
    response_currency = data["currency"]
    assert response_currency["currency_id"] == 1
    assert response_currency["currency_alpha_3"] == 'aed'
    
def test_do_get_stock_item_purchase_by_supplier(client, user_headers):
    payload = {
        "stock_category_id": 1,
        "stock_item_id": 1,
        "facility_id": 1,
        "start_date": "2021-01-01",
        "end_date": "2051-12-31"
    }
    response = do_get_stock_item_purchase_by_supplier(client, user_headers, payload)
    assert response.status_code == 200
    
    response_body = json.loads(response.data)
    assert response_body["status"] == 'successful'
    assert response_body["action"] == 'get_stock_item_purchase_by_supplier'
    
    data = response_body["data"]
    response_data = data["data"]
    assert len(response_data) > 0
    
    response_currency = data["currency"]
    assert response_currency["currency_id"] == 1
    assert response_currency["currency_alpha_3"] == 'aed'
    
def test_do_get_stock_item_transfer(client, user_headers):
    payload = {
        "facility_id_list": [],
        "stock_category_id_list": [],
        "stock_item_id_list": [],
        "start_date": "2021-01-01",
        "end_date": "2051-12-31"
    }
    response = do_get_stock_item_transfer(client, user_headers, payload)
    assert response.status_code == 200
    
    response_body = json.loads(response.data)
    assert response_body["status"] == 'successful'
    assert response_body["action"] == 'get_stock_item_transfer'
    
    data = response_body["data"]
    response_data = data["data"]
    assert len(response_data) > 0
    
    response_currency = data["currency"]
    assert response_currency["currency_id"] == 1
    assert response_currency["currency_alpha_3"] == 'AED'
    
def test_do_get_stock_item_transfer_detail(client, user_headers):
    payload = {
        "stock_category_id": 1,
        "stock_item_id": 1,
        "facility_id": 1,
        "start_date": "2021-01-01",
        "end_date": "2051-12-31"
    }
    response = do_get_stock_item_transfer_detail(client, user_headers, payload)
    assert response.status_code == 200
    
    response_body = json.loads(response.data)
    assert response_body["status"] == 'successful'
    assert response_body["action"] == 'get_stock_item_transfer_detail'
    
    data = response_body["data"]
    response_data = data["data"]
    assert len(response_data) > 0
    
    response_currency = data["currency"]
    assert response_currency["currency_id"] == 1
    assert response_currency["currency_alpha_3"] == 'AED'
    
# def test_do_get_stock_adjustment(client, user_headers):
#     payload = {
#         "facility_id_list": [],
#         "stock_category_id_list": [],
#         "start_date": "2021-01-01",
#         "end_date": "2051-12-31"
#     }
#     response = do_get_stock_adjustment(client, user_headers, payload)
#     assert response.status_code == 200
    
#     response_body = json.loads(response.data)
#     assert response_body["status"] == 'successful'
#     assert response_body["action"] == 'get_stock_adjustment'
    
#     data = response_body["data"]
#     response_data = data["data"]
#     assert len(response_data) > 0
    
#     response_currency = data["currency"]
#     assert response_currency["currency_id"] == 1
#     assert response_currency["currency_alpha_3"] == 'AED'
    
# def test_do_get_stock_adjustment_detail(client, user_headers):
#     payload = {
#         "stock_category_id": 1,
#         "stock_item_id": 1,
#         "facility_id": 1,
#         "start_date": "2021-01-01",
#         "end_date": "2051-12-31"
#     }
#     response = do_get_stock_adjustment_detail(client, user_headers, payload)
#     assert response.status_code == 200
    
#     response_body = json.loads(response.data)
#     assert response_body["status"] == 'successful'
#     assert response_body["action"] == 'get_stock_adjustment_detail'
    
#     data = response_body["data"]
#     response_data = data["data"]
#     assert len(response_data) > 0
    
#     response_currency = data["currency"]
#     assert response_currency["currency_id"] == 1
#     assert response_currency["currency_alpha_3"] == 'AED'
    
def test_do_get_stock_level(client, user_headers):
    payload = {
        "facility_id_list": [],
        "stock_category_id_list": [],
        "start_date": "2021-01-01",
        "end_date": "2051-12-31"
    }
    response = do_get_stock_level(client, user_headers, payload)
    assert response.status_code == 200
    
    response_body = json.loads(response.data)
    assert response_body["status"] == 'successful'
    assert response_body["action"] == 'get_stock_level'
    
    data = response_body["data"]
    response_data = data["data"]
    assert len(response_data) > 0
    
    response_currency = data["currency"]
    assert response_currency["currency_id"] == 1
    assert response_currency["currency_alpha_3"] == 'AED'
    
def test_do_get_stock_consumption(client, user_headers):
    payload = {
        "facility_id_list": [],
        "stock_category_id_list": [],
        "start_date": "2021-01-01",
        "end_date": "2051-12-31"
    }
    response = do_get_stock_consumption(client, user_headers, payload)
    assert response.status_code == 200
    
    response_body = json.loads(response.data)
    assert response_body["status"] == 'successful'
    assert response_body["action"] == 'get_stock_consumption'
    
    data = response_body["data"]
    response_data = data["data"]
    assert len(response_data) > 0
    
    response_currency = data["currency"]
    assert response_currency["currency_id"] == 1
    assert response_currency["currency_alpha_3"] == 'AED'
    
def test_do_get_stock_consumption_detail(client, user_headers):
    payload = {
        "stock_category_id": 1,
        "stock_item_id": 1,
        "facility_id": 1,
        "start_date": "2021-01-01",
        "end_date": "2051-12-31"
    }
    response = do_get_stock_consumption_detail(client, user_headers, payload)
    assert response.status_code == 200
    
    response_body = json.loads(response.data)
    assert response_body["status"] == 'successful'
    assert response_body["action"] == 'get_stock_consumption_detail'
    
    data = response_body["data"]
    response_data = data["data"]
    assert len(response_data) > 0
    
    response_currency = data["currency"]
    assert response_currency["currency_id"] == 1
    assert response_currency["currency_alpha_3"] == 'AED'
    
def test_do_get_stock_wastage(client, user_headers):
    payload = {
        "facility_id_list": [],
        "stock_category_id_list": [],
        "start_date": "2021-01-01",
        "end_date": "2051-12-31"
    }
    response = do_get_stock_wastage(client, user_headers, payload)
    assert response.status_code == 200
    
    response_body = json.loads(response.data)
    assert response_body["status"] == 'successful'
    assert response_body["action"] == 'get_stock_wastage'
    
    data = response_body["data"]
    response_data = data["data"]
    assert len(response_data) > 0
    
    response_currency = data["currency"]
    assert response_currency["currency_id"] == 1
    assert response_currency["currency_alpha_3"] == 'AED'
    
def test_do_get_stock_wastage_detail(client, user_headers):
    payload = {
        "stock_category_id": 1,
        "stock_item_id": 1,
        "facility_id": 1,
        "start_date": "2021-01-01",
        "end_date": "2051-12-31"
    }
    response = do_get_stock_wastage_detail(client, user_headers, payload)
    assert response.status_code == 200
    
    response_body = json.loads(response.data)
    assert response_body["status"] == 'successful'
    assert response_body["action"] == 'get_stock_wastage_detail'
    
    data = response_body["data"]
    response_data = data["data"]
    assert len(response_data) > 0
    
    response_currency = data["currency"]
    assert response_currency["currency_id"] == 1
    assert response_currency["currency_alpha_3"] == 'AED'
    
def test_do_get_master_pricing_list(client, user_headers):
    payload = {
        "stock_category_id_list": [],
        "start_date": "2021-01-01",
        "end_date": "2051-12-31"
    }
    response = do_get_master_pricing_list(client, user_headers, payload)
    assert response.status_code == 200
    
    response_body = json.loads(response.data)
    assert response_body["status"] == 'successful'
    assert response_body["action"] == 'get_master_pricing_list'
    
    data = response_body["data"]
    response_data = data["data"]
    assert len(response_data) > 0
    
    response_currency = data["currency"]
    assert response_currency["currency_id"] == 1
    assert response_currency["currency_alpha_3"] == 'AED'
    