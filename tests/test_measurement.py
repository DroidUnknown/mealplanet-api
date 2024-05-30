from utils import jqutils
import pytest
import json

base_api_url = "/api"

##########################
# TEST - MEASUREMENT
########################## 
def do_get_measurements(client,headers):
    """
    Get Measurements
    """
    response = client.get(base_api_url + "/measurements", headers=headers)
    return response

def do_get_measurement(client,headers, measurement_id):
    """
    Get One Measurement
    """
    response = client.get(base_api_url + "/measurement/" +str(measurement_id), headers=headers)
    return response

def do_add_measurement(client,headers, payload):
    """
    Add Measurement
    """
    response = client.post(base_api_url + "/measurement", headers=headers, json=payload)
    return response

def do_update_measurement(client,headers, payload):
    """
    Update Measurement
    """
    response = client.put(base_api_url + "/measurement", headers=headers, json=payload)
    return response

def do_delete_measurement(client,headers, measurement_id):
    """
    Delete Measurement
    """
    response = client.delete(base_api_url + "/measurement/" +str(measurement_id), headers=headers)
    return response


##########################
# TEST CASES
########################## 

def test_get_measurements(client,headers):
    """
    Test get measurements
    """
    response = do_get_measurements(client,headers)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert "measurements_list" in j

def test_successful_add_measurement(client,headers):
    """
    Test add measurement
    """
    payload = {
        "measurement_name" : "test",
        "measurement_description" : "test",
        "abbreviation" : "test",
    }
    response = do_add_measurement(client,headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'

    assert "measurement_id" in j
    assert jqutils.get_column_by_id(str(j["measurement_id"]), "abbreviation", "measurement") == "test", "Record not created in db, please check."

def test_failed_add_measurement_with_missing_params(client,headers):
    """
    Test add measurement
    """
    payload = {}
    with pytest.raises(Exception):
        do_add_measurement(client,headers, payload)

def test_update_measurement(client,headers):
    """
    Test update measurement
    """
    measurement_id = jqutils.get_id_by_name("test", "measurement_name", "measurement")
    payload = {
        "measurement_id" : measurement_id,
        "measurement_name" : "test",
        "measurement_description" : "test upd",
        "abbreviation" : "tupd",
    }
    response = do_update_measurement(client,headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'

    assert "measurement" in j
    assert jqutils.get_column_by_id(str(j["measurement"]["measurement_id"]), "abbreviation", "measurement") == "tupd", "Record not updated in db, please check."

def test_get_measurement(client,headers):
    """
    Test get one measurement
    """
    measurement_id = jqutils.get_id_by_name("test", "measurement_name", "measurement")
    response = do_get_measurement(client,headers, measurement_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert "measurement" in j


def test_delete_measurement(client,headers):
    """
    Test delete measurement
    """
    measurement_id = jqutils.get_id_by_name("test", "measurement_name", "measurement")
    response = do_delete_measurement(client,headers, measurement_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'

    updated_meta_status = jqutils.get_column_by_id(str(measurement_id), "meta_status", "measurement")
    assert updated_meta_status == "deleted"
    with pytest.raises(Exception):
        do_get_measurement(client,headers, measurement_id)

