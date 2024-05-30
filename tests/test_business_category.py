from utils import jqutils
import pytest
import json

base_api_url = "/api"

##########################
# TEST - BUSINESS_CATEGORY
########################## 
def do_get_business_categories(client,headers):
    """
    Get Business Categories
    """
    response = client.get(base_api_url + "/business_categories", headers=headers)
    return response

def do_get_business_category(client,headers, business_category_id):
    """
    Get One Business Category
    """
    response = client.get(base_api_url + "/business_category/" +str(business_category_id), headers=headers)
    return response

def do_add_business_category(client,headers, payload):
    """
    Add Business_category
    """
    response = client.post(base_api_url + "/business_category", headers=headers, json=payload)
    return response

def do_update_business_category(client,headers, payload):
    """
    Update Business_category
    """
    response = client.put(base_api_url + "/business_category", headers=headers, json=payload)
    return response

def do_delete_business_category(client,headers, business_category_id):
    """
    Delete Business_category
    """
    response = client.delete(base_api_url + "/business_category/" +str(business_category_id), headers=headers)
    return response


##########################
# TEST CASES
########################## 

def test_get_business_categories(client,headers):
    """
    Test get business_categories
    """
    response = do_get_business_categories(client,headers)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert len(j["data"]) > 0
    assert j["action"] == 'search_business_category_by_filter'

def test_successful_add_business_category(client,headers):
    """
    Test add business_category
    """
    payload = {
        "business_category_name" : "test",
        "business_category_description" : "test"
    }
    response = do_add_business_category(client,headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'add_business_category'

    assert "business_category_id" in j
    assert jqutils.get_column_by_id(str(j["business_category_id"]), "business_category_name", "business_category") == "test", "Record not created in db, please check."

def test_failed_add_business_category_with_missing_params(client,headers):
    """
    Test add business_category
    """
    payload = {}
    with pytest.raises(Exception):
        do_add_business_category(client,headers, payload)

def test_update_business_category(client,headers):
    """
    Test update business_category
    """
    business_category_id = jqutils.get_id_by_name("test", "business_category_name", "business_category")
    payload = {
        "business_category_id" : business_category_id,
        "business_category_name" : "test",
        "business_category_description" : "test upd",
    }
    response = do_update_business_category(client,headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'update_business_category'

    assert "business_category_id" in j
    assert jqutils.get_column_by_id(str(j["business_category_id"]), "business_category_description", "business_category") == "test upd", "Record not updated in db, please check."

def test_get_business_category(client,headers):
    """
    Test get one business_category
    """
    business_category_id = jqutils.get_id_by_name("test", "business_category_name", "business_category")
    response = do_get_business_category(client,headers, business_category_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_one_business_category'

    assert "business_category_id" in j["data"]
    assert jqutils.get_column_by_id(str(j["data"]["business_category_id"]), "business_category_description", "business_category") == "test upd", "Wrong record fetched from db, please check."


def test_delete_business_category(client,headers):
    """
    Test delete business_category
    """
    business_category_id = jqutils.get_id_by_name("test", "business_category_name", "business_category")
    response = do_delete_business_category(client,headers, business_category_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'delete_business_category'

    updated_meta_status = jqutils.get_column_by_id(str(business_category_id), "meta_status", "business_category")
    assert updated_meta_status == "deleted"
    with pytest.raises(Exception):
        do_get_business_category(client,headers, business_category_id)

