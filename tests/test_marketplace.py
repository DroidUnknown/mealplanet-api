import json

base_api_url = "/api"

##########################
# TEST - MARKETPLACE
##########################
def do_get_marketplaces(client, headers):
    """
    Get Brands
    """
    response = client.get(base_api_url + "/marketplaces", headers=headers)
    return response


##########################
# TEST CASES
##########################

def test_get_marketplaces(client, headers):
    """
    Test get marketplaces
    """
    response = do_get_marketplaces(client, headers)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert len(j["data"]) > 0
    assert j["action"] == 'get_marketplaces'
