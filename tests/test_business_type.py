from utils import jqutils
import pytest
import json

base_api_url = "/api"

##########################
# TEST - BUSINESS_TYPE
########################## 
def do_get_business_types(client,headers):
    """
    Get Business Types
    """
    response = client.get(base_api_url + "/business_types", headers=headers)
    return response

def do_get_business_type(client,headers, business_type_id):
    """
    Get One Business Type
    """
    response = client.get(base_api_url + "/business_type/" +str(business_type_id), headers=headers)
    return response

def do_add_business_type(client,headers, payload):
    """
    Add Business_type
    """
    response = client.post(base_api_url + "/business_type", headers=headers, json=payload)
    return response

def do_update_business_type(client,headers, payload):
    """
    Update Business_type
    """
    response = client.put(base_api_url + "/business_type", headers=headers, json=payload)
    return response

def do_delete_business_type(client,headers, business_type_id):
    """
    Delete Business_type
    """
    response = client.delete(base_api_url + "/business_type/" +str(business_type_id), headers=headers)
    return response


##########################
# TEST CASES
########################## 

def test_get_business_types(client,headers):
    """
    Test get business_types
    """
    response = do_get_business_types(client,headers)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert len(j["data"]) > 0
    assert j["action"] == 'search_business_type_by_filter'

def test_successful_add_business_type(client,headers):
    """
    Test add business_type
    """
    payload = {
        "business_type_name" : "test",
        "business_type_description" : "test"
    }
    response = do_add_business_type(client,headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'add_business_type'

    assert "business_type_id" in j
    assert jqutils.get_column_by_id(str(j["business_type_id"]), "business_type_name", "business_type") == "test", "Record not created in db, please check."

def test_failed_add_business_type_with_missing_params(client,headers):
    """
    Test add business_type
    """
    payload = {}
    with pytest.raises(Exception):
        do_add_business_type(client,headers, payload)

def test_update_business_type(client,headers):
    """
    Test update business_type
    """
    business_type_id = jqutils.get_id_by_name("test", "business_type_name", "business_type")
    payload = {
        "business_type_id" : business_type_id,
        "business_type_name" : "test",
        "business_type_description" : "test upd",
    }
    response = do_update_business_type(client,headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'update_business_type'

    assert "business_type_id" in j
    assert jqutils.get_column_by_id(str(j["business_type_id"]), "business_type_description", "business_type") == "test upd", "Record not updated in db, please check."

def test_get_business_type(client,headers):
    """
    Test get one business_type
    """
    business_type_id = jqutils.get_id_by_name("test", "business_type_name", "business_type")
    response = do_get_business_type(client,headers, business_type_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_one_business_type'

    assert "business_type_id" in j["data"]
    assert jqutils.get_column_by_id(str(j["data"]["business_type_id"]), "business_type_description", "business_type") == "test upd", "Wrong record fetched from db, please check."


def test_delete_business_type(client,headers):
    """
    Test delete business_type
    """
    business_type_id = jqutils.get_id_by_name("test", "business_type_name", "business_type")
    response = do_delete_business_type(client,headers, business_type_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'delete_business_type'

    updated_meta_status = jqutils.get_column_by_id(str(business_type_id), "meta_status", "business_type")
    assert updated_meta_status == "deleted"
    with pytest.raises(Exception):
        do_get_business_type(client,headers, business_type_id)

