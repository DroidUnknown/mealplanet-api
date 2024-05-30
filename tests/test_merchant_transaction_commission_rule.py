import json
base_api_url = "/api"

##############
# TEST - MERCHANT TRANSACTION COMMISSION RULE
##############

def do_get_merchant_transaction_commission_rule(client, headers, payload):
    """
    Get Merchant Commission Rules
    """
    response = client.post(f'{base_api_url}/merchant_transaction', headers=headers, json=payload)
    return response

##############
# TEST-CASE
##############

def test_get_merchant_transaction_commission_rule(client, headers):
    """
    Test get merchant commission rules
    """
    payload = {
        "currency_id": 1,
        "payment_method_id": 1,
    }
    response = do_get_merchant_transaction_commission_rule(client, headers, payload)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert "data" in j