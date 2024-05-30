import json

base_api_url = "/api"

def do_add_discount(client,headers,data):
    """
    Add Discount
    """
    response = client.post(base_api_url + "/discount", headers=headers, json=data)
    return response

def do_update_discount(client,headers,data,discount_id):
    """
    Update Discount
    """
    response = client.put(base_api_url + "/discount/"+str(discount_id), headers=headers, json=data)
    return response

def do_get_discounts(client,headers):
    """
    Get Discounts
    """
    response = client.get(base_api_url + "/discounts", headers=headers)
    return response

def do_get_discount(client,headers,discount_id):
    """
    Get Discount
    """
    response = client.get(base_api_url + "/discount/"+str(discount_id), headers=headers)
    return response

def do_delete_discount(client,headers,discount_id):
    """
    Delete Discount
    """
    response = client.delete(base_api_url + "/discount/"+str(discount_id), headers=headers)
    return response

discount_id = None

###############
# TEST CASES
###############
def test_do_add_discount(client, user_headers):
    data = {
        "discount_name": "30% Off",
        "discount_description": "30% Off",
        "discount_display_name_en": "30% Off",
        "discount_display_name_ar": "30% Off",
        "brand_id": 1,
        "marketplace_id": 1,
        "item_id_list": [1],
        "item_category_id_list": [1],
        "discount_level": "item",
        "auto_apply_p": 0,
        "currency_id": 1,
        "percentage_p": 1,
        "discount_value": 30,
        "discount_cap_value": 100,
        "minimum_order_value": 150,
        "maximum_order_value": 1000,
        "facility_fulfillment_type_map_id_list": [1,3],
        "from_time": None,
        "to_time": None,
        "timezone": None,
    }
    response = do_add_discount(client, user_headers,data)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    
    global discount_id
    discount_id = j["data"]

def test_do_update_discount(client, user_headers):
    data = {
        "discount_name": "50% Off",
        "discount_description": "50% Off",
        "discount_display_name_en": "50% Off",
        "discount_display_name_ar": "50% Off",
        "brand_id": 1,
        "marketplace_id": 1,
        "item_id_list": [1],
        "item_category_id_list": [1],
        "discount_level": "item",
        "auto_apply_p": 1,
        "currency_id": 1,
        "percentage_p": 1,
        "auto_apply_p": 0,
        "discount_value": 30,
        "discount_cap_value": 100,
        "minimum_order_value": 150,
        "maximum_order_value": 1000,
        "facility_fulfillment_type_map_id_list": [1,3],
        "from_time": "00:00:00",
        "to_time": "23:59:59",
        "timezone": -4,
    }
    response = do_update_discount(client, user_headers, data, discount_id)
    j = json.loads(response.data)
    assert j["status"] == 'successful'

def test_do_get_discounts(client, user_headers):
    response = do_get_discounts(client, user_headers)
    j = json.loads(response.data)
    assert j["status"] == 'successful'

def test_do_get_discount(client, user_headers):
    response = do_get_discount(client, user_headers, discount_id)
    j = json.loads(response.data)
    assert j["status"] == 'successful'

def test_do_delete_discount(client, user_headers):
    response = do_delete_discount(client, user_headers, discount_id)
    j = json.loads(response.data)
    assert j["status"] == 'successful'