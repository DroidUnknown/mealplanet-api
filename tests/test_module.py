import json
import pytest

base_api_url = "/api"

##########################
# TEST - MODULE
##########################
def do_get_module_list(client, content_team_headers):
    """
    GET MODULE LIST
    """
    response = client.get(base_api_url + "/modules", headers=content_team_headers)
    return response

##########################
# TEST CASES
##########################
def test_get_module_list(client, content_team_headers):
    """
    Test: Get Module List
    """
    response = do_get_module_list(client, content_team_headers)
    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json["status"] == "successful"
    assert response_json["action"] == "get_modules"

    response_data = response_json["data"]
    assert len(response_data) == 3, "Module List should have 3 items."