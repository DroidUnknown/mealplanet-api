from utils import jqutils
import pytest
import json
base_api_url = "/api"

def do_add_dining_area(client,headers,data):

    """
    Add Dining Area
    """
    response = client.post(base_api_url + "/dining_area", headers=headers, json=data)
    return response

def do_update_dining_area(client,headers,data,id):

    """
    Update Dining Area
    """
    response = client.put(base_api_url + "/dining_area/" + str(id), headers=headers, json=data)
    return response

def do_delete_dining_area(client,headers,id):

    """
    Update Dining Area
    """
    response = client.delete(base_api_url + "/dining_area/" + str(id), headers=headers)
    return response
     
def do_get_dining_area(clinet,headers,id):

    """
    Get Dining Area
    """
    response = clinet.get(base_api_url + "/dining_area/" + str(id), headers=headers)
    return response

def do_search_dining_area(client,headers):

    """
    Search Dining Area
    """
    response = client.get(base_api_url + "/dining_areas", headers=headers)
    return response

####################
# TEST CASES
####################

def test_add_dining_area(client,headers):
    data={
    "facility_id":1,    
    "dining_area_name" : "dine 1",
    "dining_area_description" : "dine 1",
    "dining_area_sequence_number" : 1
    }
    response = do_add_dining_area(client,headers,data)
    j = json.loads(response.data)
    assert j["status"] == 'successful'

def test_add_dining_area_v2(client,headers):
    data={
    "facility_id":1,    
    "dining_area_name" : "dine 2",
    "dining_area_description" : "dine 2",
    "dining_area_sequence_number" : 2
    }
    response = do_add_dining_area(client,headers,data)
    j = json.loads(response.data)
    assert j["status"] == 'successful'

def test_update_dining_area(client,headers):
    data={
    "facility_id":1,    
    "dining_area_name" : "dine 45",
    "dining_area_description" : "dine 45",
    "dining_area_sequence_number" : 1
    }
    response = do_update_dining_area(client,headers,data,1)
    j = json.loads(response.data)
    assert j["status"] == 'successful'

def test_delete_dining_area(client,headers):
    
    response = do_delete_dining_area(client,headers,1)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    
def test_get_dining_area(client,headers):

    response = do_get_dining_area(client,headers,1)
    j = json.loads(response.data)
    assert j["status"] == 'successful'

def test_search_dining_area(client,headers):

    response = do_search_dining_area(client,headers)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
      