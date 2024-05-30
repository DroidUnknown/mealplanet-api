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
def do_assign_order_payment_split_detail(client,headers,data):
    
    response = client.post(base_api_url + '/order_payment_split_detail', json=data, headers=headers)
    return response

def do_delete_order_payment_split_detail(client,headers,data):
    
    response = client.delete(base_api_url + '/order_payment_split_detail', json=data, headers=headers)
    return response

def do_order_payment_split_detail_searches(client,headers):
    
    response = client.get(base_api_url + '/order_payment_split_details',headers=headers)
    return response

################################
### TESTS ######################
################################

@pytest.fixture(scope="module", autouse=True)
def init_customer_order(client, user_headers):
    with open("tests/testdata/customer_orders/pos/02_menu_items_with_modifiers.json", encoding='utf-8') as f:
        transaction_payload = json.load(f)
    
    transaction_payload["merchant_code"] = 'k_131231'

    response = test_customer_order.do_calculate_order(client, user_headers, transaction_payload)
    j = json.loads(response.data)
    assert j["status"] == 'successful'

    response = test_customer_order.do_create_customer_order(client, user_headers, transaction_payload)
    j = json.loads(response.data)
    assert j["status"] == 'successful'

    customer_order_id = j["customer_order_id"]

    yield customer_order_id

def test_do_assign_order_payment_split_detail(client, user_headers, init_customer_order):
    data={
        "customer_order_id": init_customer_order,
        "split_payment_details":
        [
            {
                "payment_method_id": 1,
                "currency_id": 1,
                "payment_status": "unpaid",
                "payment_amount": 500,
                "payment_timestamp": "2021-01-01 00:00:00"
            },
            {
                "payment_method_id": 2,
                "currency_id": 1,
                "payment_status": "unpaid",
                "payment_amount": 300,
                "payment_timestamp": "2021-01-01 00:00:00"
            }
        ]
    }
    response = do_assign_order_payment_split_detail(client, user_headers, data)
    j = json.loads(response.data)
    status = j['status']
    assert status == 'successful'

# def test_do_delete_order_payment_split_detail(client, user_headers, init_customer_order):
#     data={
#         "customer_order_id": init_customer_order,
#         "payment_method_id": 2
#     }
#     response = do_delete_order_payment_split_detail(client, user_headers, data)
#     j = json.loads(response.data)
#     status = j['status']
#     assert status == 'successful'    

# def test_do_order_payment_split_detail_searches(client, user_headers):
#     response = do_order_payment_split_detail_searches(client, user_headers)
#     j = json.loads(response.data)
#     status = j['status']
#     assert status == 'successful'    

