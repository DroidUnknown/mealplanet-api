from utils import jqutils
from sqlalchemy import text
import pytest
import json

base_api_url = "/api"

##########################
# TEST - CALL_STAFF_LOG
########################## 
def do_get_call_staff_logs(client,order_panel_headers):
    """
    Get Payment Point Areas
    """
    response = client.get(base_api_url + "/call_staff_logs", headers=order_panel_headers)
    return response

def do_get_call_staff_log(client,order_panel_headers, call_staff_log_id):
    """
    Get One Payment Point Area
    """
    response = client.get(base_api_url + "/call_staff_log/" +str(call_staff_log_id), headers=order_panel_headers)
    return response

def do_add_call_staff_log(client, payload):
    """
    Add Call_staff_log
    """
    response = client.post(base_api_url + "/call_staff_log", json=payload)
    return response

def do_update_call_staff_log(client,order_panel_headers, payload):
    """
    Update Call_staff_log
    """
    response = client.put(base_api_url + "/call_staff_log", headers=order_panel_headers, json=payload)
    return response

def do_delete_call_staff_log(client,order_panel_headers, call_staff_log_id):
    """
    Delete Call_staff_log
    """
    response = client.delete(base_api_url + "/call_staff_log/" +str(call_staff_log_id), headers=order_panel_headers)
    return response


##########################
# TEST CASES
########################## 

def test_successful_add_call_staff_log(client):
    """
    Test add call_staff_log
    """
    payload = {
        "payment_point_id": 1
    }
    response = do_add_call_staff_log(client, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'add_call_staff_log'

    assert "call_staff_log_id" in j
    assert jqutils.get_column_by_id(str(j["call_staff_log_id"]), "payment_point_id", "call_staff_log") == 1, "Record not created in db, please check."

def test_get_call_staff_logs(client,order_panel_headers):
    """
    Test get call_staff_logs
    """
    response = do_get_call_staff_logs(client,order_panel_headers)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert len(j["data"]) > 0
    assert j["action"] == 'search_call_staff_log_by_filter'

def test_failed_add_call_staff_log_with_missing_params(client):
    """
    Test add call_staff_log
    """
    payload = {}
    with pytest.raises(Exception):
        do_add_call_staff_log(client, payload)

def test_update_call_staff_log(client,order_panel_headers):
    """
    Test update call_staff_log
    """
    call_staff_log_id = jqutils.get_id_by_name("1", "merchant_id", "call_staff_log")
    payload = {
        "call_staff_log_id": call_staff_log_id,
        "call_staff_log_status": "completed"
    }
    response = do_update_call_staff_log(client,order_panel_headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'update_call_staff_log'

    assert "call_staff_log_id" in j
    assert int(jqutils.get_column_by_id(str(j["call_staff_log_id"]), "merchant_id", "call_staff_log")) == 1, "Record not updated in db, please check."

def test_get_call_staff_log(client,order_panel_headers):
    """
    Test get one call_staff_log
    """
    call_staff_log_id = jqutils.get_id_by_name("1", "merchant_id", "call_staff_log")
    response = do_get_call_staff_log(client,order_panel_headers, call_staff_log_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_one_call_staff_log'

    assert "call_staff_log_id" in j["data"]
    assert int(jqutils.get_column_by_id(str(j["data"]["call_staff_log_id"]), "merchant_id", "call_staff_log")) == 1, "Wrong record fetched from db, please check."

def test_delete_call_staff_log(client,order_panel_headers):
    """
    Test delete call_staff_log
    """
    call_staff_log_id = jqutils.get_id_by_name("1", "merchant_id", "call_staff_log")
    response = do_delete_call_staff_log(client,order_panel_headers, call_staff_log_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'delete_call_staff_log'

    updated_meta_status = jqutils.get_column_by_id(str(call_staff_log_id), "meta_status", "call_staff_log")
    assert updated_meta_status == "deleted"
    with pytest.raises(Exception):
        do_get_call_staff_log(client,order_panel_headers, call_staff_log_id)