import json
import gzip
from tests import test_branch

base_api_url = "/api"

def do_make_item_unvailable(client,headers,data):
        
    response = client.post(base_api_url + '/marketplace-menu/availability', json=data, headers=headers)
    return response

def do_get_item_unavailable(client,headers,item_availability_request_id):

    response = client.get(base_api_url + '/marketplace-menu/availability/' + str(item_availability_request_id), headers=headers)
    return response

def do_search_filter_by_merchant(client,headers):
    
    response = client.get(base_api_url + '/marketplace-menu/availability', headers=headers)
    return response

def do_delete_item_unavailable(client,headers,item_availability_request_id):

    response = client.delete(base_api_url + '/marketplace-menu/availability/' + str(item_availability_request_id), headers=headers)
    return response

def do_get_merchant_items(client, headers, merchant_id):
    """
    Get Merchant Items
    """
    response = client.get(f'{base_api_url}/merchant/{merchant_id}/item-list', headers=headers)
    return response

def do_get_merchant_item_categories(client, headers, merchant_id):
    """
    Get Merchant Item Categories
    """
    response = client.get(f'{base_api_url}/merchant/{merchant_id}/item-category-list', headers=headers)
    return response

###########
# TESTS #
###########


def test_do_make_item_unavailable(client,headers):
    data = {
        "availability_status": "out-of-stock",
        "item_id_list": [61,62,63],
        "branch_id_list": [3],
        "unavailability_reason_id": 1,
        "unavailability_reason_notes": "anything",
        "expiry_timestamp": "2021-01-01 00:00:00"
    }

    response = do_make_item_unvailable(client,headers,data)
    j = json.loads(response.data)
    status = j['status']
    assert status == 'successful'

def test_do_make_item_unavailable_V2(client,headers):

    data = {
        "availability_status": "in-stock",
        "item_id_list": [61,62],
        "branch_id_list": [3],
        "unavailability_reason_id": 1,
        "unavailability_reason_notes": "anything",
        "expiry_timestamp": "2021-01-01 00:00:00"
    }

    response = do_make_item_unvailable(client,headers,data)
    j = json.loads(response.data)
    status = j['status']
    assert status == 'successful'

def test_do_get_merchant_items(client, headers):
    merchant_id = 1
    response = do_get_merchant_items(client, headers, merchant_id)
    
    decompressed_response = gzip.decompress(response.data)

    j = json.loads(decompressed_response)
    status = j['status']
    assert status == 'successful'
    assert len(j['data']) > 0, 'No items found for merchant'
    assert j['action'] == 'get_merchant_item_list', 'Action not matching'

def test_do_get_merchant_item_categories(client, headers):
    merchant_id = 1
    response = do_get_merchant_item_categories(client, headers, merchant_id)
    
    decompressed_response = gzip.decompress(response.data)

    j = json.loads(decompressed_response)
    status = j['status']
    assert status == 'successful'
    assert len(j['data']) > 0, 'No items found for merchant'
    assert j['action'] == 'get_merchant_item_category_list', 'Action not matching'

def test_do_search_filter_by_merchant(client,headers):

    response = do_search_filter_by_merchant(client,headers)
    j = json.loads(response.data)
    status = j['status']
    assert status == 'successful'


def test_do_get_item_unavailable(client,headers):

    response = do_get_item_unavailable(client,headers,2)
    j = json.loads(response.data)
    status = j['status']
    assert status == 'successful'


def test_do_delete_item_unavailable(client,headers):
    
    response = do_delete_item_unavailable(client,headers,2)
    j = json.loads(response.data)
    status = j['status']
    assert status == 'successful'

def test_do_get_branch_menu(client,headers):
    branch_id = 2
    availability_details = True
    response = test_branch.do_get_branch_menu(client, headers, branch_id, availability_details)
    j = json.loads(response.data)
    status = j['status']
    assert status == 'successful'

