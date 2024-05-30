import json
base_api_url = "/api"

##############
# TEST - PAYMENT METHOD
##############

def do_get_payment_methods(client, headers, params={}):
    """
    Get Payment Method
    """
    response = client.get(f'{base_api_url}/payment_methods', headers=headers, query_string=params)
    return response

##############
# TEST-CASE
##############

def test_get_payment_methods(client, headers):
    """
    Test get payment methods
    """
    response = do_get_payment_methods(client, headers)
    j = json.loads(response.data)
    assert j["status"] == 'successful'

def test_get_payment_methods_with_merchant_configs(client, headers):
    """
    Test get payment methods with merchant configs
    """
    params = {
        'branch_id': None,
        'fulfillment_type_id': 1,
        'order_placement_channel_id': None
    }
    response = do_get_payment_methods(client, headers, params)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    
    for one_payment_method in j["payload"]:
        if one_payment_method['payment_method_id'] == 1:
            assert one_payment_method['auto_apply_p'] == True
        else:
            assert one_payment_method['auto_apply_p'] == False

def test_get_payment_methods_with_exclusions(client, headers):
    """
    Test get payment methods with exclusions
    """
    params = {
        'branch_id': None,
        'fulfillment_type_id': 1,
        'order_placement_channel_id': None
    }
    response = do_get_payment_methods(client, headers, params)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    
    excluded_payment_method_id = 2
    
    excluded_payment_method_id_found_p = False
    for one_payment_method in j["payload"]:
        if one_payment_method['payment_method_id'] == excluded_payment_method_id:
            excluded_payment_method_id_found_p = True
            break
    
    assert excluded_payment_method_id_found_p == False