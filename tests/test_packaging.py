from utils import jqutils
import pytest
import json

base_api_url = "/api"

##########################
# TEST - Packaging
########################## 
def do_get_packagings(client,headers):
    """
    Get Packagings
    """
    response = client.get(base_api_url + "/packagings", headers=headers)
    return response



########################
# TEST CASES
########################

def test_get_packagings(client,headers):
    """
    Test get packagings
    """
    response = do_get_packagings(client,headers)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
