from utils import jqutils
import pytest
import json

base_api_url = "/api"

##########################
# TEST - Processes
########################## 
def do_get_processes(client,headers):
    """
    Get processes
    """
    response = client.get(base_api_url + "/processes", headers=headers)
    return response



########################
# TEST CASES
########################

def test_get_processes(client,headers):
    """
    Test get processes
    """
    response = do_get_processes(client,headers)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
