import json
base_api_url = "/api"

##############
# TEST - Currency
##############

def do_get_currencies(client, headers):
    """
    Get Currencies
    """
    response = client.get(f'{base_api_url}/currencies', headers=headers)
    return response

##############
# TEST-CASE
##############

def test_get_currencies(client, headers):
    """
    Test get currencies
    """
    response = do_get_currencies(client, headers)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
