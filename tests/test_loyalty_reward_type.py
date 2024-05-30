from utils import jqutils
import pytest
import json

base_api_url = "/api"

##############################
# TEST - LOYALTY REWARD TYPE
##############################
def do_get_loyalty_reward_types(client,headers):
    """
    Get Loyalty Reward Types
    """
    response = client.get(base_api_url + "/loyalty_reward_types", headers=headers)
    return response

def do_get_loyalty_reward_type(client,headers, loyalty_reward_type_id):
    """
    Get One Loyalty Reward Type
    """
    response = client.get(base_api_url + "/loyalty_reward_type/" +str(loyalty_reward_type_id), headers=headers)
    return response

def do_add_loyalty_reward_type(client,headers, payload):
    """
    Add loyalty_reward_type
    """
    response = client.post(base_api_url + "/loyalty_reward_type", headers=headers, json=payload)
    return response

def do_update_loyalty_reward_type(client,headers, payload):
    """
    Update loyalty_reward_type
    """
    response = client.put(base_api_url + "/loyalty_reward_type", headers=headers, json=payload)
    return response

def do_delete_loyalty_reward_type(client,headers, loyalty_reward_type_id):
    """
    Delete loyalty_reward_type
    """
    response = client.delete(base_api_url + "/loyalty_reward_type/" +str(loyalty_reward_type_id), headers=headers)
    return response


##########################
# TEST CASES
########################## 

def test_get_loyalty_reward_types(client,headers):
    """
    Test get loyalty_reward_types
    """
    response = do_get_loyalty_reward_types(client,headers)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert len(j["data"]) > 0
    assert j["action"] == 'search_loyalty_reward_type_by_filter'

def test_successful_add_loyalty_reward_type(client,headers):
    """
    Test add loyalty_reward_type
    """
    payload = {
        "loyalty_reward_type_name" : "test",
        "loyalty_reward_type_description" : "test"
    }
    response = do_add_loyalty_reward_type(client,headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'add_loyalty_reward_type'

    assert "loyalty_reward_type_id" in j
    assert jqutils.get_column_by_id(str(j["loyalty_reward_type_id"]), "loyalty_reward_type_name", "loyalty_reward_type") == "test", "Record not created in db, please check."

def test_failed_add_loyalty_reward_type_with_missing_params(client,headers):
    """
    Test add loyalty_reward_type
    """
    payload = {}
    with pytest.raises(Exception):
        do_add_loyalty_reward_type(client,headers, payload)

def test_update_loyalty_reward_type(client,headers):
    """
    Test update loyalty_reward_type
    """
    loyalty_reward_type_id = jqutils.get_id_by_name("test", "loyalty_reward_type_name", "loyalty_reward_type")
    payload = {
        "loyalty_reward_type_id" : loyalty_reward_type_id,
        "loyalty_reward_type_name" : "test",
        "loyalty_reward_type_description" : "test upd",
    }
    response = do_update_loyalty_reward_type(client,headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'update_loyalty_reward_type'

    assert "loyalty_reward_type_id" in j
    assert jqutils.get_column_by_id(str(j["loyalty_reward_type_id"]), "loyalty_reward_type_description", "loyalty_reward_type") == "test upd", "Record not updated in db, please check."

def test_get_loyalty_reward_type(client,headers):
    """
    Test get one loyalty_reward_type
    """
    loyalty_reward_type_id = jqutils.get_id_by_name("test", "loyalty_reward_type_name", "loyalty_reward_type")
    response = do_get_loyalty_reward_type(client,headers, loyalty_reward_type_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_one_loyalty_reward_type'

    assert "loyalty_reward_type_id" in j["data"]
    assert jqutils.get_column_by_id(str(j["data"]["loyalty_reward_type_id"]), "loyalty_reward_type_description", "loyalty_reward_type") == "test upd", "Wrong record fetched from db, please check."


def test_delete_loyalty_reward_type(client,headers):
    """
    Test delete loyalty_reward_type
    """
    loyalty_reward_type_id = jqutils.get_id_by_name("test", "loyalty_reward_type_name", "loyalty_reward_type")
    response = do_delete_loyalty_reward_type(client,headers, loyalty_reward_type_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'delete_loyalty_reward_type'

    updated_meta_status = jqutils.get_column_by_id(str(loyalty_reward_type_id), "meta_status", "loyalty_reward_type")
    assert updated_meta_status == "deleted"
    with pytest.raises(Exception):
        do_get_loyalty_reward_type(client,headers, loyalty_reward_type_id)

