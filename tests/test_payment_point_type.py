from utils import jqutils
import pytest
import json

base_api_url = "/api"

##########################
# TEST - PAYMENT_POINT_TYPE
########################## 
def do_get_payment_point_types(client,headers):
    """
    Get Interface Types
    """
    response = client.get(base_api_url + "/payment_point_types", headers=headers)
    return response

def do_get_payment_point_type(client,headers, payment_point_type_id):
    """
    Get One Interface Type
    """
    response = client.get(base_api_url + "/payment_point_type/" +str(payment_point_type_id), headers=headers)
    return response

def do_add_payment_point_type(client,headers, payload):
    """
    Add Payment_point_type
    """
    response = client.post(base_api_url + "/payment_point_type", headers=headers, json=payload)
    return response

def do_update_payment_point_type(client,headers, payload):
    """
    Update Payment_point_type
    """
    response = client.put(base_api_url + "/payment_point_type", headers=headers, json=payload)
    return response

def do_delete_payment_point_type(client,headers, payment_point_type_id):
    """
    Delete Payment_point_type
    """
    response = client.delete(base_api_url + "/payment_point_type/" +str(payment_point_type_id), headers=headers)
    return response


##########################
# TEST CASES
########################## 

def test_get_payment_point_types(client,headers):
    """
    Test get payment_point_types
    """
    response = do_get_payment_point_types(client,headers)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert len(j["data"]) > 0
    assert j["action"] == 'search_payment_point_type_by_filter'

def test_successful_add_payment_point_type(client,headers):
    """
    Test add payment_point_type
    """
    payload = {
        "payment_point_type_name" : "test",
        "payment_point_type_description" : "test"
    }
    response = do_add_payment_point_type(client,headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'add_payment_point_type'

    assert "payment_point_type_id" in j
    assert jqutils.get_column_by_id(str(j["payment_point_type_id"]), "payment_point_type_name", "payment_point_type") == "test", "Record not created in db, please check."

def test_failed_add_payment_point_type_with_missing_params(client,headers):
    """
    Test add payment_point_type
    """
    payload = {}
    with pytest.raises(Exception):
        do_add_payment_point_type(client,headers, payload)

def test_update_payment_point_type(client,headers):
    """
    Test update payment_point_type
    """
    payment_point_type_id = jqutils.get_id_by_name("test", "payment_point_type_name", "payment_point_type")
    payload = {
        "payment_point_type_id" : payment_point_type_id,
        "payment_point_type_name" : "test",
        "payment_point_type_description" : "test upd",
    }
    response = do_update_payment_point_type(client,headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'update_payment_point_type'

    assert "payment_point_type_id" in j
    assert jqutils.get_column_by_id(str(j["payment_point_type_id"]), "payment_point_type_description", "payment_point_type") == "test upd", "Record not updated in db, please check."

def test_get_payment_point_type(client,headers):
    """
    Test get one payment_point_type
    """
    payment_point_type_id = jqutils.get_id_by_name("test", "payment_point_type_name", "payment_point_type")
    response = do_get_payment_point_type(client,headers, payment_point_type_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_one_payment_point_type'

    assert "payment_point_type_id" in j["data"]
    assert jqutils.get_column_by_id(str(j["data"]["payment_point_type_id"]), "payment_point_type_description", "payment_point_type") == "test upd", "Wrong record fetched from db, please check."


def test_delete_payment_point_type(client,headers):
    """
    Test delete payment_point_type
    """
    payment_point_type_id = jqutils.get_id_by_name("test", "payment_point_type_name", "payment_point_type")
    response = do_delete_payment_point_type(client,headers, payment_point_type_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'delete_payment_point_type'

    updated_meta_status = jqutils.get_column_by_id(str(payment_point_type_id), "meta_status", "payment_point_type")
    assert updated_meta_status == "deleted"
    with pytest.raises(Exception):
        do_get_payment_point_type(client,headers, payment_point_type_id)

