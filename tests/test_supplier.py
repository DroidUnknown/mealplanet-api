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
import string

base_api_url = "/api"

def do_add_supplier(client,headers,data):
    response = client.post(base_api_url + '/supplier', json=data, headers=headers)
    return response

def do_update_supplier(client,headers,data,supplier_id):
    response = client.put(base_api_url + '/supplier/'+ str(supplier_id), json=data, headers=headers)
    return response
    
def do_get_supplier(client,headers,supplier_id):
    response = client.get(base_api_url + '/supplier/'+ str(supplier_id), headers=headers)
    return response
        
def do_get_supplier_list(client, headers, merchant_id):
    response = client.get(base_api_url + f'/suppliers?merchant_id={merchant_id}', headers=headers)
    return response

def do_delete_supplier(client,headers,supplier_id):
    response = client.delete(base_api_url + '/supplier/'+ str(supplier_id), headers=headers)
    return response

##############
# TESTS
##############


def test_do_add_supplier(client,headers):

    data = {
        "organization_id": 1,
        "supplier_name": "XYZ",
        "supplier_description": "XYZ",
        "supplier_contact_name": "XYZ",
        "supplier_contact_email": "XYZ",
        "supplier_contact_phone_nr": "XYZ",
        "supplier_address_line_1": "XYZ",
        "supplier_address_line_2": "XYZ",
        "supplier_trn_id": "XYZ",
        "city_id": 1,
        "country_id": 1
    }

    response = do_add_supplier(client,headers,data)
    j = json.loads(response.data)
    status = j['status']
    assert status == 'successful'

def test_do_update_supplier(client,headers):

    data = {
        "organization_id": 1,
        "supplier_name": "WXYZ",
        "supplier_description": "WXYZ",
        "supplier_contact_name": "WXYZ",
        "supplier_contact_email": "WXYZ",
        "supplier_contact_phone_nr": "WXYZ",
        "supplier_address_line_1": "WXYZ",
        "supplier_address_line_2": "WXYZ",
        "supplier_trn_id": "WXYZ",
        "city_id": 1,
        "country_id": 1
    }

    response = do_update_supplier(client,headers,data,1)
    j = json.loads(response.data)
    status = j['status']
    assert status == 'successful'

def test_do_get_supplier(client,headers):

    response = do_get_supplier(client,headers,1)
    j = json.loads(response.data)
    status = j['status']
    assert status == 'successful'

def test_do_get_supplier_list(client, headers):

    response = do_get_supplier_list(client, headers, 1)
    j = json.loads(response.data)
    status = j['status']
    assert status == 'successful'

def test_do_delete_supplier(client,headers):

    response = do_delete_supplier(client,headers,1)
    j = json.loads(response.data)
    status = j['status']
    assert status == 'successful'




            
