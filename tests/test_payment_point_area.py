from utils import jqutils
from sqlalchemy import text
import pytest
import json

base_api_url = "/api"

##########################
# TEST - PAYMENT_POINT_AREA
########################## 
def do_get_payment_point_areas(client,user_headers):
    """
    Get Payment Point Areas
    """
    response = client.get(base_api_url + "/payment_point_areas", headers=user_headers)
    return response

def do_get_payment_point_area(client,user_headers, payment_point_area_id):
    """
    Get One Payment Point Area
    """
    response = client.get(base_api_url + "/payment_point_area/" +str(payment_point_area_id), headers=user_headers)
    return response

def do_add_payment_point_area(client,user_headers, payload):
    """
    Add Payment_point_area
    """
    response = client.post(base_api_url + "/payment_point_area", headers=user_headers, json=payload)
    return response

def do_update_payment_point_area(client,user_headers, payload):
    """
    Update Payment_point_area
    """
    response = client.put(base_api_url + "/payment_point_area", headers=user_headers, json=payload)
    return response

def do_delete_payment_point_area(client,user_headers, payment_point_area_id):
    """
    Delete Payment_point_area
    """
    response = client.delete(base_api_url + "/payment_point_area/" +str(payment_point_area_id), headers=user_headers)
    return response

def do_get_payment_point_areas_by_user_id(client,user_headers, user_id):
    """
    Get Payment Point Areas by user id
    """
    response = client.get(base_api_url + "/user/" + str(user_id) + "/payment_point_areas", headers=user_headers)
    return response


##########################
# TEST CASES
########################## 

def test_get_payment_point_areas(client,user_headers):
    """
    Test get payment_point_areas
    """
    response = do_get_payment_point_areas(client,user_headers)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert len(j["data"]) > 0
    assert j["action"] == 'search_payment_point_area_by_filter'

def test_successful_add_payment_point_area(client,user_headers):
    """
    Test add payment_point_area
    """
    payload = {
        "parent_payment_point_area_id": None,
        "payment_point_area_type_id": 1,
        "merchant_id": 1,
        "payment_point_area_name": "test",
        "payment_point_area_description": "desc"
    }
    response = do_add_payment_point_area(client,user_headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'add_payment_point_area'

    assert "payment_point_area_id" in j
    assert jqutils.get_column_by_id(str(j["payment_point_area_id"]), "payment_point_area_name", "payment_point_area") == "test", "Record not created in db, please check."

def test_successful_add_payment_point_area_for_second_merchant_as_admin(client,headers):
    """
    Test add payment_point_area
    """
    payload = {
        "parent_payment_point_area_id": None,
        "payment_point_area_type_id": 1,
        "merchant_id": 2,
        "payment_point_area_name": "second test",
        "payment_point_area_description": "desc"
    }
    response = do_add_payment_point_area(client,headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'add_payment_point_area'

    assert "payment_point_area_id" in j
    assert jqutils.get_column_by_id(str(j["payment_point_area_id"]), "payment_point_area_name", "payment_point_area") == "second test", "Record not created in db, please check."

def test_failed_add_payment_point_area_with_missing_params(client,user_headers):
    """
    Test add payment_point_area
    """
    payload = {}
    with pytest.raises(Exception):
        do_add_payment_point_area(client,user_headers, payload)

def test_update_payment_point_area(client,user_headers):
    """
    Test update payment_point_area
    """
    payment_point_area_id = jqutils.get_id_by_name("test", "payment_point_area_name", "payment_point_area")
    payload = {
        "payment_point_area_id": payment_point_area_id,
        "parent_payment_point_area_id": None,
        "payment_point_area_type_id": 1,
        "merchant_id": 1,
        "payment_point_area_name": "test upd",
        "payment_point_area_description": "desc upd"

    }
    response = do_update_payment_point_area(client,user_headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'update_payment_point_area'

    assert "payment_point_area_id" in j
    assert jqutils.get_column_by_id(str(j["payment_point_area_id"]), "payment_point_area_name", "payment_point_area") == "test upd", "Record not updated in db, please check."

def test_get_payment_point_area(client,user_headers):
    """
    Test get one payment_point_area
    """
    payment_point_area_id = jqutils.get_id_by_name("test upd", "payment_point_area_name", "payment_point_area")
    response = do_get_payment_point_area(client,user_headers, payment_point_area_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_one_payment_point_area'

    assert "payment_point_area_id" in j["data"]
    assert jqutils.get_column_by_id(str(j["data"]["payment_point_area_id"]), "payment_point_area_name", "payment_point_area") == "test upd", "Wrong record fetched from db, please check."


def test_get_payment_point_areas_by_user(client,user_headers):
    """
    Test get payment_point_areas by user
    """
    response = do_get_payment_point_areas_by_user_id(client,user_headers, user_headers.get("X-User-Id"))
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert len(j["payment_point_area_list"]) > 0
    assert j["action"] == 'get_payment_point_areas_by_user_id'

def test_get_payment_point_areas_by_user_from_different_merchant(client,user_headers):
    """
    Test add payment_point_area
    """
    db_engine = jqutils.get_db_engine()

    query = text("""
        SELECT user_id, merchant_id
        FROM user_merchant_map
        WHERE merchant_id <> :merchant_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, merchant_id=1, meta_status="active").fetchone()
        assert result, "No user found for different merchant"
        different_user_id = result["user_id"]

    with pytest.raises(Exception):
        response = do_get_payment_point_areas_by_user_id(client,user_headers, different_user_id)

def test_get_payment_point_areas_by_user_from_different_merchant_as_admin(client,headers):
    """
    Test get payment_point_areas by user
    """
    db_engine = jqutils.get_db_engine()

    query = text("""
        SELECT user_id, merchant_id
        FROM user_merchant_map
        WHERE merchant_id <> :merchant_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, merchant_id=1, meta_status="active").fetchone()
        assert result, "No user found for different merchant"
        different_user_id = result["user_id"]

    response = do_get_payment_point_areas_by_user_id(client,headers, different_user_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert len(j["payment_point_area_list"]) > 0
    assert j["action"] == 'get_payment_point_areas_by_user_id'

def test_delete_payment_point_area(client,user_headers):
    """
    Test delete payment_point_area
    """
    payment_point_area_id = jqutils.get_id_by_name("test upd", "payment_point_area_name", "payment_point_area")
    response = do_delete_payment_point_area(client,user_headers, payment_point_area_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'delete_payment_point_area'

    updated_meta_status = jqutils.get_column_by_id(str(payment_point_area_id), "meta_status", "payment_point_area")
    assert updated_meta_status == "deleted"
    with pytest.raises(Exception):
        do_get_payment_point_area(client,user_headers, payment_point_area_id)