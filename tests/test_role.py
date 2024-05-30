import json

base_api_url = "/api"

##########################
# TEST - ROLE
########################## 
def do_get_assignable_roles(client,user_headers):
    """
    Get Assignable Roles
    """
    response = client.get(base_api_url + "/assignable-roles", headers=user_headers)
    return response

##########################
# TEST CASES
########################## 

def test_get_assignable_roles(client,user_headers):
    """
    Test get assignable roles
    """
    response = do_get_assignable_roles(client,user_headers)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert len(j["role_list"]) > 0
    assert j["action"] == 'get_assignable_roles'