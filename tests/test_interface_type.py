from utils import jqutils
import pytest
import json

base_api_url = "/api"

##########################
# TEST - INTERFACE_TYPE
########################## 
def do_get_interface_types(client,headers):
    """
    Get Interface Types
    """
    response = client.get(base_api_url + "/interface_types", headers=headers)
    return response

def do_get_interface_type(client,headers, interface_type_id):
    """
    Get One Interface Type
    """
    response = client.get(base_api_url + "/interface_type/" +str(interface_type_id), headers=headers)
    return response

def do_add_interface_type(client,headers, payload):
    """
    Add Interface_type
    """
    response = client.post(base_api_url + "/interface_type", headers=headers, json=payload)
    return response

def do_update_interface_type(client,headers, payload):
    """
    Update Interface_type
    """
    response = client.put(base_api_url + "/interface_type", headers=headers, json=payload)
    return response

def do_delete_interface_type(client,headers, interface_type_id):
    """
    Delete Interface_type
    """
    response = client.delete(base_api_url + "/interface_type/" +str(interface_type_id), headers=headers)
    return response


##########################
# TEST CASES
########################## 

def test_get_interface_types(client,headers):
    """
    Test get interface_types
    """
    response = do_get_interface_types(client,headers)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert len(j["data"]) > 0
    assert j["action"] == 'search_interface_type_by_filter'

def test_successful_add_interface_type(client,headers):
    """
    Test add interface_type
    """
    payload = {
        "interface_type_name" : "test",
        "interface_type_description" : "test"
    }
    response = do_add_interface_type(client,headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'add_interface_type'

    assert "interface_type_id" in j
    assert jqutils.get_column_by_id(str(j["interface_type_id"]), "interface_type_name", "interface_type") == "test", "Record not created in db, please check."

def test_failed_add_interface_type_with_missing_params(client,headers):
    """
    Test add interface_type
    """
    payload = {}
    with pytest.raises(Exception):
        do_add_interface_type(client,headers, payload)

def test_update_interface_type(client,headers):
    """
    Test update interface_type
    """
    interface_type_id = jqutils.get_id_by_name("test", "interface_type_name", "interface_type")
    payload = {
        "interface_type_id" : interface_type_id,
        "interface_type_name" : "test",
        "interface_type_description" : "test upd",
    }
    response = do_update_interface_type(client,headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'update_interface_type'

    assert "interface_type_id" in j
    assert jqutils.get_column_by_id(str(j["interface_type_id"]), "interface_type_description", "interface_type") == "test upd", "Record not updated in db, please check."

def test_get_interface_type(client,headers):
    """
    Test get one interface_type
    """
    interface_type_id = jqutils.get_id_by_name("test", "interface_type_name", "interface_type")
    response = do_get_interface_type(client,headers, interface_type_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_one_interface_type'

    assert "interface_type_id" in j["data"]
    assert jqutils.get_column_by_id(str(j["data"]["interface_type_id"]), "interface_type_description", "interface_type") == "test upd", "Wrong record fetched from db, please check."


def test_delete_interface_type(client,headers):
    """
    Test delete interface_type
    """
    interface_type_id = jqutils.get_id_by_name("test", "interface_type_name", "interface_type")
    response = do_delete_interface_type(client,headers, interface_type_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'delete_interface_type'

    updated_meta_status = jqutils.get_column_by_id(str(interface_type_id), "meta_status", "interface_type")
    assert updated_meta_status == "deleted"
    with pytest.raises(Exception):
        do_get_interface_type(client,headers, interface_type_id)

