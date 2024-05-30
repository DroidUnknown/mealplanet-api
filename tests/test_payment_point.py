from utils import jqutils
from sqlalchemy import text
import pytest
import json

base_api_url = "/api"

##########################
# TEST - PAYMENT_POINT
########################## 
def do_get_payment_points(client,user_headers):
    """
    Get Payment Point Areas
    """
    response = client.get(base_api_url + "/payment_points", headers=user_headers)
    return response

def do_get_payment_point(client,user_headers, payment_point_id):
    """
    Get One Payment Point Area
    """
    response = client.get(base_api_url + "/payment_point/" +str(payment_point_id), headers=user_headers)
    return response

def do_add_payment_point(client,user_headers, payload):
    """
    Add Payment_point
    """
    response = client.post(base_api_url + "/payment_point", headers=user_headers, json=payload)
    return response

def do_update_payment_point(client,user_headers, payload):
    """
    Update Payment_point
    """
    response = client.put(base_api_url + "/payment_point", headers=user_headers, json=payload)
    return response

def do_delete_payment_point(client,user_headers, payment_point_id):
    """
    Delete Payment_point
    """
    response = client.delete(base_api_url + "/payment_point/" +str(payment_point_id), headers=user_headers)
    return response

def do_payment_point_by_code(client, payment_point_code):
    """
    Get Payment Point Details
    """
    response = client.get(base_api_url + "/payment-point/code/" + payment_point_code)
    return response


##########################
# TEST CASES
########################## 

def test_get_payment_points(client,user_headers):
    """
    Test get payment_points
    """
    response = do_get_payment_points(client,user_headers)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert len(j["data"]) > 0
    assert j["action"] == 'search_payment_point_by_filter'

def test_successful_add_payment_point(client,user_headers):
    """
    Test add payment_point
    """
    payload = {
        "payment_point_area_id": 1,
        "payment_point_type_id": 1,
        "payment_point_name": "test",
        "payment_point_description": "desc",
        "interface_type_id": 1,
    }
    response = do_add_payment_point(client,user_headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'add_payment_point'

    assert "payment_point_id" in j
    assert jqutils.get_column_by_id(str(j["payment_point_id"]), "payment_point_name", "payment_point") == "test", "Record not created in db, please check."

def test_failed_add_payment_point_with_missing_params(client,user_headers):
    """
    Test add payment_point
    """
    payload = {}
    with pytest.raises(Exception):
        do_add_payment_point(client,user_headers, payload)

def test_update_payment_point(client,user_headers):
    """
    Test update payment_point
    """
    payment_point_id = jqutils.get_id_by_name("test", "payment_point_name", "payment_point")
    payload = {
        "payment_point_id": payment_point_id,
        "payment_point_area_id": 1,
        "payment_point_type_id": 1,
        "payment_point_name": "test upd",
        "payment_point_description": "desc",
        "interface_type_id": 1,
    }
    response = do_update_payment_point(client,user_headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'update_payment_point'

    assert "payment_point_id" in j
    assert jqutils.get_column_by_id(str(j["payment_point_id"]), "payment_point_name", "payment_point") == "test upd", "Record not updated in db, please check."

def test_get_payment_point(client,user_headers):
    """
    Test get one payment_point
    """
    payment_point_id = jqutils.get_id_by_name("test upd", "payment_point_name", "payment_point")
    response = do_get_payment_point(client,user_headers, payment_point_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_one_payment_point'

    assert "payment_point_id" in j["data"]
    assert jqutils.get_column_by_id(str(j["data"]["payment_point_id"]), "payment_point_name", "payment_point") == "test upd", "Wrong record fetched from db, please check."

def test_delete_payment_point(client,user_headers):
    """
    Test delete payment_point
    """
    payment_point_id = jqutils.get_id_by_name("test upd", "payment_point_name", "payment_point")
    response = do_delete_payment_point(client,user_headers, payment_point_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'delete_payment_point'

    updated_meta_status = jqutils.get_column_by_id(str(payment_point_id), "meta_status", "payment_point")
    assert updated_meta_status == "deleted"
    with pytest.raises(Exception):
        do_get_payment_point(client,user_headers, payment_point_id)

def test_payment_point_by_code(client):
    """
    Test get payment point details by code
    """
    merchant_id = 1
    db_engine = jqutils.get_db_engine()

    query = text("""
        SELECT pp.payment_point_code
        FROM payment_point pp
        JOIN payment_point_area ppa ON ppa.payment_point_area_id = pp.payment_point_area_id
        WHERE ppa.merchant_id = :merchant_id
        AND pp.meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, merchant_id=merchant_id, meta_status='active').fetchone()
        assert result, "No payment point found for merchant id: " + str(merchant_id)
        payment_point_code = result["payment_point_code"]
    
    response = do_payment_point_by_code(client, payment_point_code)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_payment_point_by_code'