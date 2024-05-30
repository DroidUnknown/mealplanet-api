import json
base_api_url = "/api"

##################
# TEST - COUNTRY
##################

def do_get_cities(client, headers):
    """
    Get cities
    """
    response = client.get(f'{base_api_url}/cities', headers=headers)
    return response

##############
# TEST CASES
##############

def test_get_cities(client, headers):
    """
    Test get cities
    """
    response = do_get_cities(client, headers)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
