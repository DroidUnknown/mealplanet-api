import json
import pytest

base_api_url = "/api"

##########################
# TEST - ROLE
##########################
def do_get_role_list(client, content_team_headers):
    """
    GET ROLE LIST
    """
    response = client.get(base_api_url + "/roles", headers=content_team_headers)
    return response

##########################
# TEST CASES
##########################
def test_get_role_list(client, content_team_headers):
    """
    Test: Get Role List
    """
    response = do_get_role_list(client, content_team_headers)
    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json["status"] == "successful"
    assert response_json["action"] == "get_roles"

    response_data = response_json["data"]
    assert len(response_data) == 4, "Role List should have 3 items."