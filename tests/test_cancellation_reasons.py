import json
base_api_url = "/api"

###############################
# TEST - Cancellation Reasons
###############################

def do_get_cancellation_reasons(client, headers):
    """
    Get Cancellation Reasons
    """
    response = client.get(f'{base_api_url}/cancellation-reasons', headers=headers)
    return response

##############
# TEST-CASE
##############

def test_get_cancellation_reasons(client, headers):
    """
    Test get cancellation_reasons
    """
    response = do_get_cancellation_reasons(client, headers)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
