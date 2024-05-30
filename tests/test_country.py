import json
base_api_url = "/api"

##################
# TEST - COUNTRY
##################

def do_get_countries(client, headers):
    """
    Get Countries
    """
    response = client.get(f'{base_api_url}/countries', headers=headers)
    return response

##############
# TEST CASES
##############

def test_get_countries(client, headers):
    """
    Test get countries
    """
    response = do_get_countries(client, headers)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
