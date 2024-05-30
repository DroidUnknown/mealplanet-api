import json

from datetime import datetime

base_api_url = "/api"

############################
# TEST - DAILY SALES
############################

def do_get_daily_sales(client, headers):
    """
    Get Daily Sales
    """

    payload = {
        "start_date": datetime.now().strftime("%Y-%m-%d 00:00:00"),
        "end_date": datetime.now().strftime("%Y-%m-%d 23:59:59"),
        "group_by": "default"
    }
    response = client.post(f'{base_api_url}/daily_sales', headers=headers, json=payload)
    return response

############################
# TEST - MENU PERFORMANCE
############################

def do_get_menu_performance(client, headers):
    """
    Get Menu Performance
    """

    payload = {
        "start_date": datetime.now().strftime("%Y-%m-%d 00:00:00"),
        "end_date": datetime.now().strftime("%Y-%m-%d 23:59:59"),
        "country_id": 1
    }
    response = client.post(f'{base_api_url}/menu_performance', headers=headers, json=payload)
    return response

def do_get_modifier_performance(client, headers):
    """
    Get Modifier Performance
    """

    payload = {
        "start_date": datetime.now().strftime("%Y-%m-%d 00:00:00"),
        "end_date": datetime.now().strftime("%Y-%m-%d 23:59:59"),
        "country_id": 1
    }
    response = client.post(f'{base_api_url}/modifier_performance', headers=headers, json=payload)
    return response

def do_get_item_combination_performance(client, headers):
    """
    Get Item Combination Performance
    """

    payload = {
        "start_date": datetime.now().strftime("%Y-%m-%d 00:00:00"),
        "end_date": datetime.now().strftime("%Y-%m-%d 23:59:59"),
        "country_id": 1
    }
    response = client.post(f'{base_api_url}/item_combination_performance', headers=headers, json=payload)
    return response

def do_get_item_performance(client, headers, item_id):
    """
    Get Item Performance
    """

    payload = {
        "start_date": datetime.now().strftime("%Y-%m-%d 00:00:00"),
        "end_date": datetime.now().strftime("%Y-%m-%d 23:59:59"),
        "country_id": 1
    }
    response = client.post(f'{base_api_url}/item/{item_id}/performance', headers=headers, json=payload)
    return response

##############
# TEST-CASE
##############

def test_get_daily_sales(client, headers):
    """
    Test get Daily Sales
    """
    response = do_get_daily_sales(client, headers)
    j = json.loads(response.data)
    assert j["status"] == 'successful'


# def test_get_menu_performance(client, headers):
#     """
#     Test get Menu Performance
#     """
#     response = do_get_menu_performance(client, headers)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'

# def test_get_modifier_performance(client, headers):
#     """
#     Test get Modifier Performance
#     """
#     response = do_get_modifier_performance(client, headers)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'

# def test_get_item_combination_performance(client, headers):
#     """
#     Test get Item Combination Performance
#     """
#     response = do_get_item_combination_performance(client, headers)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'