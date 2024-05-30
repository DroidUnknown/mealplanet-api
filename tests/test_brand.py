import json
from utils import jqutils

base_api_url = "/api"

##########################
# TEST - BRANDS
##########################
def do_get_brands(client, headers):
    """
    Get Brands
    """
    response = client.get(base_api_url + "/brands", headers=headers)
    return response

def do_get_brand(client, headers, brand_id):
    """
    Get Brand
    """
    response = client.get(base_api_url + f"/brand/{brand_id}", headers=headers)
    return response

def do_get_item_categories_by_brand(client, headers, brand_id):
    """
    Get Item Categories By Brand
    """
    response = client.get(base_api_url + f"/brand/{brand_id}/item_categories", headers=headers)
    return response

def do_add_item_category_for_brand(client, headers, brand_id, payload):
    """
    Add Item Category For Brand
    """
    response = client.post(base_api_url + f"/brand/{brand_id}/item_category", headers=headers, json=payload)
    return response

def do_get_items_by_brand(client, headers, brand_id):
    """
    Get Items By Brand
    """
    response = client.get(base_api_url + f"/brand/{brand_id}/items", headers=headers)
    return response

def do_get_brand_iblinkmarketplace_config(client, headers, brand_code):
    """
    Get Brand Iblinkmarketplace Config
    """
    response = client.get(base_api_url + f"/brand/{brand_code}/iblinkmarketplace-config", headers=headers)
    return response

##########################
# TEST CASES
##########################

def test_get_brands(client, headers):
    """
    Test get brands
    """
    response = do_get_brands(client, headers)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert len(j["data"]) > 0
    assert j["action"] == 'get_brands'

def test_get_brand(client, headers):
    """
    Test get brand by id
    """
    brand_id = 1
    response = do_get_brand(client, headers, brand_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["data"]["brand_id"] == brand_id
    assert j["action"] == 'get_brand'

def test_get_items_by_brand(client, headers):
    """
    Test get items by brand
    """
    response = do_get_brands(client, headers)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert len(j["data"]) > 0
    assert j["action"] == 'get_brands'
    brand_id = j["data"][0]["brand_id"]
    response = do_get_items_by_brand(client, headers, brand_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert len(j["data"]) >= 0
    assert j["action"] == 'get_items_by_brand'

def test_do_get_brand_iblinkmarketplace_config(client, headers):
    """
    Test get brand iblinkmarketplace config
    """
    response = do_get_brands(client, headers)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert len(j["data"]) > 0
    assert j["action"] == 'get_brands'
    brand_code = j["data"][0]["brand_code"]
    
    response = do_get_brand_iblinkmarketplace_config(client, headers, brand_code)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_brand_iblinkmarketplace_config'