from utils import jqutils
import pytest
import json
base_api_url = "/api"

def do_get_stock_consumptions(client,headers,facility_id):
        
    """
    Get Stock Consumptions
    """
    response = client.get(base_api_url + "/facility/"+str(facility_id)+"/stock_item_consumptions?supplier_id=1", headers=headers)
    return response

def do_stock_item_request(client,headers,data):
        
    """
    Stock Item Request
    """

    response = client.post(base_api_url + "/stock_item_request", headers=headers, json=data)
    return response

def do_stock_item_receiving(client,headers,data):
            
    """
    Stock Item Receiving
    """

    response = client.post(base_api_url + "/stock_request_receiving", headers=headers, json=data)
    return response

def do_stock_request_approval(client,headers,data):
            
    """
    Stock Request Approval
    """

    response = client.put(base_api_url + "/stock_request_approval", headers=headers, json=data)
    return response

def do_stock_request_send(client,headers,data):
    
    """
    Stock Request Send
    """
    response = client.post(base_api_url + "/stock_request_send", headers=headers ,json=data)
    return response
    
def do_bulk_upload_stock_item(client,headers,data):
            
    """
    Add Stock Item
    """

    response = client.post(base_api_url + "/stock_item/bulk_upload", headers=headers, json=data)
    return response

def do_add_stock_item(client,headers,data):
            
    """
    Add Stock Item
    """

    response = client.post(base_api_url + "/stock_item", headers=headers, json=data)
    return response

def do_update_stock_item(client,headers,data,stock_item_id):
            
    """
    Update Stock Item
    """

    response = client.put(base_api_url + "/stock_item/" + str(stock_item_id), headers=headers, json=data)
    return response

def do_delete_stock_item(client,headers,stock_item_id):
            
    """
    Delete Stock Item
    """

    response = client.delete(base_api_url + "/stock_item/" + str(stock_item_id), headers=headers)
    return response
    

def do_get_stock_item(client,headers,stock_item_id):
            
    """
    Get Stock Item
    """

    response = client.get(base_api_url + "/stock_item/" + str(stock_item_id), headers=headers)
    return response

def do_get_stock_parent_stock_items(client,headers):
    
    """
    Get Stock Parent Stock Items
    """
    
    response = client.get(base_api_url + "/stock_items?master_p=1", headers=headers)
    return response

def do_get_stock_item_list(client,headers):
    
    """
    Get Stock Item List
    """
        
    response = client.get(base_api_url + "/stock_items", headers=headers)
    return response

def do_get_stock_requests(client,headers,data):
    
    """
    Get Stock Requests
    """
    response = client.post(base_api_url + "/stock_requests", headers=headers, json=data)
    return response

def do_get_stock_request(client,headers,stock_request_code):
    
    """
    Get Stock Request
    """
    #put in argument for stock_request_code
    
    response = client.get(base_api_url + f"/stock_request?stock_request_code={stock_request_code}", headers=headers)
    return response
    
def do_add_stock_wasatge(client,headers,data):
    
    """
    Add Stock Wastage
    """
    response = client.post(base_api_url + "/stock_wastage", headers=headers, json=data)
    return response

def do_get_stock_wastages(client,headers,data):
    
    """
    Get Stock Wastages
    """
    response = client.post(base_api_url + "/stock_item_wastages", headers=headers, json=data)
    return response
    
def do_get_stock_wastage_details(client,headers,data):
    
    """
    Get Stock Wastage Details
    """
    response = client.post(base_api_url + "/stock_wastage_detail", headers=headers, json=data)
    return response

def do_get_stock_request_invoices(client,headers,data):
    
    """
    Get Stock Item Supplier Invoices
    """
    response = client.post(base_api_url + "/stock_request_get_invoice", headers=headers, json=data)
    return response

def do_update_stock_request_status(client,headers,data):
        
    """
    Update Stock Request Status
    """
    response = client.post(base_api_url + "/stock_request_status_update", headers=headers, json=data)
    return response

def do_dispatch_stock_request(client,headers,data):
    
    """
    Dispatch Stock Request
    """
    response = client.post(base_api_url + "/stock_request_dispatching", headers=headers, json=data)
    return response

def do_get_stock_consumption_by_departments(client,headers,facility_id):
    
    """
    Get Stock Consumption By Departments
    """
    response = client.get(base_api_url + f"/department/{facility_id}/stock_item_consumptions", headers=headers)
    return response

def do_get_stock_consumption_for_single_department(client,headers,facility_id,department_id):
    
    """
    Get Stock Consumption For Single Department
    """
    response = client.get(base_api_url + f"/department/{facility_id}/stock_item_consumptions/{department_id}", headers=headers)
    return response

def do_get_stock_request_email(client,headers,stock_request_code):
        
        """
        Get Stock Request Email
        """
        response = client.get(base_api_url + f"/stock_request_supplier_invoices?stock_request_code={stock_request_code}", headers=headers)
        return response
    
def do_verify_stock_item_calculation(client,headers,data):
    
    """
    Verify Stock Item Calculation
    """
    response = client.post(base_api_url + "/stock_request_item_verification", headers=headers, json=data)
    return response

def do_update_stock_request_by_code(client,headers,stock_request_code,data):
    
    """
    Update Stock Request By Code
    """
    response = client.put(base_api_url + "/stock_request/stock_request_code/" + str(stock_request_code), headers=headers, json=data)
    return response

def do_create_stock_request_jobs(client,headers,stock_request_code,data):

    """
    Create Stock Request Jobs
    """
    response = client.post(base_api_url + "/stock_request/stock_request_code/" + str(stock_request_code) + "/jobs", headers=headers, json=data)
    return response

def do_update_stock_request_job_products(client,headers,stock_request_code,data):
        
    """
    Update Stock Request Job Products
    """
    response = client.put(base_api_url + "/stock_request/stock_request_code/" + str(stock_request_code) + "/products", headers=headers, json=data)
    return response

def do_get_stock_request_grn(client,headers,stock_request_code):
    
    """
    Get Stock Request GRN
    """
    response = client.get(base_api_url + f"/stock_request_receiving_note?stock_request_code={stock_request_code}", headers=headers)
    return response
    
def do_get_stock_item_snapshot(client,headers,facility_id):
    
    """
    Get Stock Snapshot
    """
    response = client.get(base_api_url + "/facility/"+str(facility_id)+"/stock_item_snapshot", headers=headers)
    return response

    
    
stock_item_id = None
###############
# TEST CASES
###############

def test_do_get_stock_consumptions(client,headers):
    
    response = do_get_stock_consumptions(client,headers,1)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    
def test_do_get_stock_item_snapshot(client,headers):
    
    response = do_get_stock_item_snapshot(client,headers,1)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    
def test_do_get_stock_request_invoices(client,headers):
    
    data = {
        "facility_id_list": [4,5,6],
    }
    
    response = do_get_stock_request_invoices(client,headers,data)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    
# def test_do_get_stock_consumption_by_departments(client,headers):
    
#     response = do_get_stock_consumption_by_departments(client,headers,1)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
    
# def test_do_get_stock_consumption_for_single_department(client,headers):
    
#     response = do_get_stock_consumption_for_single_department(client,headers,1,1)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
    
def test_do_verify_stock_item_calculation(client,headers):
    
    data = {
        
        "stock_item_list": [
            {
                "quantity": 10,
                "cost_per_pack": 100,
                "item_amount": 1000,
                "discount_value": 10,
                "percentage_p": 0,
                "discount_amount": 10,
                "payable_amount": 990,
            }
        ]
    }
    
    response = do_verify_stock_item_calculation(client,headers,data)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    
def test_do_add_stock_item(client,headers):
    data = {
        "stock_item_name_en": "test",
        "stock_item_description_en": "test",
        "default_supplier_id": 1,
        "parent_stock_item_id": 1,
        "stock_category_id": 1,
        "measurement_id": 1,
        "packaging_list": [
            {
                "packaging_id": 1,
                "packaging_measurement_id": 5,
                "packaging_quantity": 10,
                "stock_item_quantity": 100,
                "supplier_list": [
                    {
                        "supplier_id": 1,
                        "cost_per_pack": 100,
                        "currency_id": 1
                    },
                    {
                        "supplier_id": 2,
                        "cost_per_pack": 200,
                        "currency_id": 1
                    }
                ]
            }
        ]
    }
    
    response = do_add_stock_item(client,headers,data)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    global stock_item_id
    stock_item_id = j['stock_item_id']

def test_do_get_stock_item(client,headers):
    
    response = do_get_stock_item(client,headers,stock_item_id)
    j = json.loads(response.data)
    assert j["status"] == 'successful'

def test_do_update_stock_item(client,headers):
    data = {
        "stock_item_name_en": "test2",
        "stock_item_description_en": "test2",
        "default_supplier_id": 1,
        "parent_stock_item_id": 1,
        "stock_category_id": 1,
        "measurement_id": 1,
        "packaging_list": [
            {   
                "stock_item_packaging_map_id": 1,
                "packaging_id": 1,
                "packaging_measurement_id": 5,
                "packaging_quantity": 10,
                "stock_item_quantity": 100,
                "supplier_list": [
                    {
                        "supplier_id": 1,
                        "cost_per_pack": 100,
                        "currency_id": 1
                    },
                ]
            },
            {
                "packaging_id": 1,
                "packaging_measurement_id": 5,
                "packaging_quantity": 10,
                "stock_item_quantity": 10,
                "supplier_list": [
                    {
                        "supplier_id": 2,
                        "cost_per_pack": 100,
                        "currency_id": 1
                    },
                ]
            }
        ]
    }
    
    response = do_update_stock_item(client,headers,data,stock_item_id)
    j = json.loads(response.data)
    assert j["status"] == 'successful'

def test_do_get_stock_item_updated(client,headers):
    
    response = do_get_stock_item(client,headers,stock_item_id)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    
def test_do_delete_stock_item(client,headers):
    
    response = do_delete_stock_item(client,headers,stock_item_id)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    
# def test_do_request_stock_item(client,headers):
        
#     data = {
#         "facility_id": 1,
#         "stock_request_type": "procurement",
#         "stock_item_list": [
#             {
#                 "stock_item_id": 1,
#                 "quantity": 10,
#                 "measurement_id": 1
#             },
#             {
#                 "stock_item_id": 2,
#                 "quantity": 20,
#                 "measurement_id": 1
#             },
#             {
#                 "stock_item_id": 3,
#                 "quantity": 30,
#                 "measurement_id": 1
#             }
#         ]
#     }
    
#     response = do_stock_item_request(client,headers,data)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
#     stock_request_code = j['stock_request_code']

    # do_get_stock_request(client,headers,stock_request_code)

# def test_do_get_stock_requests(client,headers):
    
#     data = {
#         "facility_id": 1,
#         "stock_request_type": "procurement",
#     }

#     response = do_get_stock_requests(client,headers,data)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
                    
# def test_do_add_stock_item(client,headers):
#     data = {
#         "stock_item_name_en": "test",
#         "stock_item_description_en": "test",
#         "stock_item_code": "test",
#         "default_supplier_id": 1,
#         "parent_stock_item_id": 1
#     }
    
#     response = do_add_stock_item(client,headers,data)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'

# def test_do_add_stock_item_v2(client,headers):
#     data = {
#         "stock_item_name_en": "test",
#         "stock_item_description_en": "test",
#         "stock_item_code": "test",
#         "default_supplier_id": 1,
#         "parent_stock_item_id": 1
#     }
    
#     response = do_add_stock_item(client,headers,data)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'

    
# def test_do_update_stock_item(client,headers):
#     data = {
#         "stock_item_name_en": "test2",
#         "stock_item_description_en": "test2",
#         "stock_item_code": "test2",
#         "default_supplier_id": 1,
#         "parent_stock_item_id": 1
#     }
    
#     response = do_update_stock_item(client,headers,data,1)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
    
# def test_do_delete_stock_item(client,headers):
    
#     response = do_delete_stock_item(client,headers,1)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
    
# def test_do_get_stock_item(client,headers):
    
#     response = do_get_stock_item(client,headers,2)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'    
        
# def test_do_get_stock_parent_stock_items(client,headers):
        
#     response = do_get_stock_parent_stock_items(client,headers)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
    
# def test_do_get_stock_item_list(client,headers):
    
#     response = do_get_stock_item_list(client,headers)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
    
# def test_do_add_stock_wastage(client,headers):
    
#     data = {
#         "facility_id": 1,
#         "stock_wastage_type": "stock_wastage",
#         "stock_item_list": [
#             {
#                 "stock_item_id": 1,
#                 "quantity": 10,
#                 "measurement_id": 1,
#                 "wastage_reason_id": 1
#             },
#             {
#                 "stock_item_id": 2,
#                 "quantity": 20,
#                 "measurement_id": 1,
#                 "wastage_reason_id": 1
#             },
#             {
#                 "stock_item_id": 3,
#                 "quantity": 30,
#                 "measurement_id": 1,
#                 "wastage_reason_id": 1
#             }
#         ]
#     }
    
#     response = do_add_stock_wasatge(client,headers,data)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
#     stock_wastage_code = j['stock_wastage_code']
        
#     data = {
#         'facility_id': 1,
#         'stock_wastage_id': 1,
#         'stock_wastage_code': stock_wastage_code
#     }
    
#     response = do_get_stock_wastages(client,headers,data)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
    
#     data = {
#         'facility_id': 1,
#         'stock_wastage_id': 1,
#         'stock_wastage_code': stock_wastage_code
#     }
#     response = do_get_stock_wastage_details(client,headers,data)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'