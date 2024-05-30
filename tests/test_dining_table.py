from utils import jqutils
import pytest
import json
base_api_url = "/api"

def do_add_dining_table(client,headers,data):

    """
    Add Dining Table
    """
    response = client.post(base_api_url + "/dining_table", headers=headers, json=data)
    return response

def do_update_dining_table(client,headers,data,id):

    """
    Update Dining Table
    """
    response = client.put(base_api_url + "/dining_table/" + str(id), headers=headers, json=data)
    return response

def do_delete_dining_table(client,headers,id):

    """
    Update Dining Table
    """
    response = client.delete(base_api_url + "/dining_table/" + str(id), headers=headers)
    return response
     
def do_get_dining_table(clinet,headers,id):

    """
    Get Dining Table
    """
    response = clinet.get(base_api_url + "/dining_table/" + str(id), headers=headers)
    return response

def do_search_dining_table(client,headers):

    """
    Search Dining Table
    """
    response = client.get(base_api_url + "/dining_tables", headers=headers)
    return response

####################
# TEST CASES
####################

def test_add_dining_table(client,headers):
    data={
    "dining_area_id":1,    
    "dining_table_name" : "dine 1",
    "dining_table_capacity" : 1,
    "dining_table_sequence_number" : 1
    }
    response = do_add_dining_table(client,headers,data)
    j = json.loads(response.data)
    assert j["status"] == 'successful'

def test_add_dining_table_v2(client,headers):
    data={
    "dining_area_id":1,    
    "dining_table_name" : "dine 2",
    "dining_table_capacity" : 7,
    "dining_table_sequence_number" : 2
    }
    response = do_add_dining_table(client,headers,data)
    j = json.loads(response.data)
    assert j["status"] == 'successful'

def test_update_dining_table(client,headers):
    data={
    "dining_area_id":1,    
    "dining_table_name" : "dine 45",
    "dining_table_capacity" : 3,
    "dining_table_sequence_number" : 1
    }
    response = do_update_dining_table(client,headers,data,1)
    j = json.loads(response.data)
    assert j["status"] == 'successful'

def test_delete_dining_table(client,headers):
    
    response = do_delete_dining_table(client,headers,1)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    
def test_get_dining_table(client,headers):

    response = do_get_dining_table(client,headers,2)
    j = json.loads(response.data)
    assert j["status"] == 'successful'

def test_search_dining_table(client,headers):

    response = do_search_dining_table(client,headers)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
      