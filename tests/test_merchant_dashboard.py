import json
base_api_url = "/api"

##############
# TEST - MERCHANT DAHSBOARD
##############

def do_get_merchant_dashboard_info(client, headers, merchant_id):
    """
    Get Merchant Dashboard Info
    """
    response = client.get(f'{base_api_url}/merchant/{merchant_id}/dashboard', headers=headers)
    return response

def do_get_merchant_dashboard_info_v2(client, headers):
    """
    Get Merchant Dashboard Info V2
    """
    response = client.get(f'{base_api_url}/merchant/dashboard', headers=headers)
    return response

def do_get_merchant_transaction_history(client, headers, merchant_id):
    """
    Get Merchant Transaction History Info
    """
    response = client.get(f'{base_api_url}/merchant/{merchant_id}/transaction_history', headers=headers)
    return response

def do_get_merchant_transaction_history_v2(client, headers):
    """
    Get Merchant Transaction History Info V2
    """
    response = client.get(f'{base_api_url}/merchant/transaction_history', headers=headers)
    return response


##############
# TEST-CASE
##############


def test_get_merchant_dashboard_info(client, headers):
    """
    Test get merchant dashboard info
    """
    response = do_get_merchant_dashboard_info(client, headers, 1)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert "data" in j

def test_get_merchant_dashboard_info_v2(client, headers):
    """
    Test get merchant dashboard info V2
    """
    response = do_get_merchant_dashboard_info_v2(client, headers)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert "data" in j

def test_get_merchant_transaction_history(client, headers):
    """
    Test get merchant history info
    """
    response = do_get_merchant_transaction_history(client, headers, 1)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert "data" in j

def test_get_merchant_transaction_history_v2(client, headers):
    """
    Test get merchant history info V2
    """
    response = do_get_merchant_transaction_history_v2(client, headers)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert "data" in j
