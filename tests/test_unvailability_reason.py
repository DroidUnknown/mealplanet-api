import os
import pytest
import json
import requests
import json
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.sql import text
import sys
import urllib.parse
from utils import jqsecurity, jqutils
import jwt
import random
import string
from datetime import datetime
from tests import test_customer_order

base_api_url = "/api"

def do_add_unavailability_reason(client,headers,data):

    response = client.post(base_api_url + '/unavailability_reason', json=data, headers=headers)
    return response

def do_update_unavailability_reason(client,headers,data,unavailability_reason_id):

    response = client.put(base_api_url + '/unavailability_reason/'+ str(unavailability_reason_id), json=data, headers=headers)
    return response
    
def do_get_unavailability_reason(client,headers,unavailability_reason_id):

    response = client.get(base_api_url + '/unavailability_reason/'+ str(unavailability_reason_id), headers=headers)
    return response
        
def do_get_unavailaibility_reason_list(client,headers):

    response = client.get(base_api_url + '/unavailability_reasons', headers=headers)
    return response

def do_delete_unavailability_reason(client,headers,unavailability_reason_id):

    response = client.delete(base_api_url + '/unavailability_reason/'+ str(unavailability_reason_id), headers=headers)
    return response

##############
# TESTS
##############


def test_do_add_unavailability_reason(client,headers):

    data = {
        "unavailability_reason_name": "worker left",
        "unavailability_reason_description": "worker went home"
    }

    response = do_add_unavailability_reason(client,headers,data)
    j = json.loads(response.data)
    status = j['status']
    assert status == 'successful'

def test_do_update_unavailability_reason(client,headers):

    data = {
        "unavailability_reason_name": "worker left",
        "unavailability_reason_description": "worker went on sick leave"
    }

    response = do_update_unavailability_reason(client,headers,data,5)
    j = json.loads(response.data)
    status = j['status']
    assert status == 'successful'

def test_do_get_unavailaibility_reason(client,headers):

    response = do_get_unavailability_reason(client,headers,5)
    j = json.loads(response.data)
    status = j['status']
    assert status == 'successful'

def test_do_get_unavailaibility_reason_list(client,headers):

    response = do_get_unavailability_reason(client,headers,5)
    j = json.loads(response.data)
    status = j['status']
    assert status == 'successful'

def test_do_delete_unavailability_reason(client,headers):

    response = do_delete_unavailability_reason(client,headers,5)
    j = json.loads(response.data)
    status = j['status']
    assert status == 'successful'




            
