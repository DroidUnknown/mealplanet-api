import json

base_api_url = "/api"

##########################
# TEST - FULFILLMENT TYPE
##########################
def do_get_fulfillment_types(client, headers):
    """
    Get Brands
    """
    response = client.get(base_api_url + "/fulfillment_types", headers=headers)
    return response


##########################
# TEST CASES
##########################

def test_get_fulfillment_types(client, headers):
    """
    Test get fulfillment_types
    """
    response = do_get_fulfillment_types(client, headers)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert len(j["data"]) > 0
    assert j["action"] == 'get_fulfillment_types'
