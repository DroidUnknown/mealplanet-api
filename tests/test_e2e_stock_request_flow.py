import time
import json
import os
from sqlalchemy import text
from tests import test_stock_item, test_supplier, test_facility, test_stock_item, test_stock_return
from tests import test_enterprise_back_office
from utils import jqutils, my_utils

base_api_url = "/api"

def test_e2e_supplier_request_flow(client,headers):
    """
    Test E2E Stock Request Flow
    """
    response = test_facility.do_get_facilities(client, headers, "")
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert len(j["data"]) > 0
    assert j["action"] == 'get_facilities'
    
    facility_name = "test satwa 1"

    for facility in j["data"]:
        if facility["facility_name"] == facility_name:
            to_facility_id = facility["facility_id"]
            break
    
    response = test_supplier.do_get_supplier_list(client, headers, 1)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j['action'] == 'get_suppliers'
    
    for supplier in j['data']:
        if supplier['supplier_name'] == 'satwa 2':
            supplier_id = supplier['supplier_id']
            supplier_facility_id = supplier['facility_id']
            break
    
    data = {
        "facility_id": to_facility_id,
        "stock_request_type": "supplier-procurement",
        "to_facility_id" : to_facility_id,
        "from_facility_id" : supplier_facility_id,
        "supplier_id" : supplier_id,
        "expected_delivery_date": "2020-01-01 00:00:00",
        "stock_item_list": [
            {
                "stock_item_id": 1,
                "quantity": 10,
                "stock_item_packaging_map_id": 1,
                "supplier_id": supplier_id,
                "cost_per_pack": 10.00,
                "item_amount": 100.00,
                "discount_value": 0.00,
                "percentage_p": 0,
                "discount_amount": 0.00,
                "payable_amount": 100.00,
                
            },
            {
                "stock_item_id": 2,
                "quantity": 20,
                "stock_item_packaging_map_id": 4,
                "supplier_id": supplier_id,
                "cost_per_pack": 8.00,
                "item_amount": 160.00,
                "discount_value": 0.00,
                "percentage_p": 0,
                "discount_amount": 0.00,
                "payable_amount": 160.00,
            },
            {
                "stock_item_id": 3,
                "quantity": 30,
                "stock_item_packaging_map_id": 5,
                "supplier_id": supplier_id,
                "cost_per_pack": 20.00,
                "item_amount": 600.00,
                "discount_value": 0.00,
                "percentage_p": 0,
                "discount_amount": 0.00,
                "payable_amount": 600.00,
            }
        ]
    }
    
    response = test_stock_item.do_stock_item_request(client, headers, data)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    
    stock_request_code = j["stock_request_code"]
    
    response = test_stock_item.do_get_stock_request(client, headers, stock_request_code)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    

    stock_request_status = j["data"]["stock_request_status"]
    assert stock_request_status == 'pending-approval'
    approver_details = j["data"]["current_level_process_approval_map_list"]
    assert len(approver_details) > 0
    
    data = {
        "stock_request_code": stock_request_code,
        "approval_status": "approved",
        "approval_notes": "test notes",
        "approval_level": 1
    }
    
    test_stock_item.do_stock_request_approval(client,headers,data)
    
    response = test_stock_item.do_get_stock_request(client, headers, stock_request_code)
    j = json.loads(response.data)
    assert j["status"] == 'successful'

    stock_request_status = j["data"]["stock_request_status"]
    assert stock_request_status == 'approved'
    
    query = text("""
        UPDATE FACILITY
        SET facility_contact_name = :facility_contact_name,
        facility_contact_phone_nr = :facility_contact_phone_nr,
        facility_contact_email = :facility_contact_email,
        facility_trn_id = :facility_trn_id,
        address_line_1 = :address_line_1,
        address_line_2 = :address_line_2,
        timezone = :timezone
        WHERE facility_id in :facility_id_list
        AND meta_status = :meta_status
    """)
    
    db_engine = jqutils.get_db_engine()
    
    with db_engine.connect() as conn:
        result = conn.execute(query, facility_contact_name="OKISH", facility_contact_phone_nr="321-33-212", facility_contact_email="go@gmail.com", facility_trn_id="AAAA-0000", address_line_1="faciliy_123", address_line_2="nowhere", timezone=4, facility_id_list=[1,2,4,5,6], meta_status='active').rowcount
        
    data = {
        "stock_request_code": stock_request_code,
        "stock_request_status": "sent",
    }
    
    response = test_stock_item.do_update_stock_request_status(client,headers,data)
    
    response = test_stock_item.do_get_stock_request_email(client,headers,stock_request_code)
    
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    
    recipient_name = j["data"][0]["recipient_name"]
    recipient_email = j["data"][0]["recipient_email"]
    subject = j["data"][0]["subject"]
    email_body = j["data"][0]["email_body"]
    rendered_html = j["data"][0]["rendered_html"]
    
    
    data = {
        "stock_request_code": stock_request_code,
        "email_list": [
            {
                "recipient_name": "recipient_name", 
                "recipient_list": [recipient_email],
                "rendered_html": rendered_html,
                "email_body": rendered_html,
                "email_subject" : "subject"
            }
        ]
    }
    
    response = test_stock_item.do_stock_request_send(client,headers,data)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    
    #  get flow for dispatching
    
    # get stock requests
    
    data = {
        "facility_id_list": [supplier_facility_id],
        "stock_request_type": "supplier-procurement",
    }
    response = test_stock_item.do_get_stock_requests(client, headers, data)
    j = json.loads(response.data)
    assert j["status"] == 'successful'

    response = test_stock_item.do_get_stock_request(client, headers, stock_request_code)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    
    data = {
        "stock_request_code": stock_request_code,
        "facility_id_list": [4,5,6],
        'stock_activity_start_timestamp': "2020-01-01 00:00:00",
        'stock_activity_end_timestamp': "2020-01-01 00:00:00",
        'stock_activity_status': 'done',
        'stock_item_list': [
            {
                "stock_item_id": 1,
                "quantity": 10,
                "stock_item_packaging_map_id": 1,
                "supplier_id": 1,
                "cost_per_pack": 10.00,
                "item_amount": 100.00,
                "discount_value": 0.00,
                "percentage_p": 0,
                "discount_amount": 0.00,
                "payable_amount": 100.00,
            },
            {
                "stock_item_id": 2,
                "quantity": 20,
                "stock_item_packaging_map_id": 4,
                "supplier_id": 1,
                "cost_per_pack": 8.00,
                "item_amount": 160.00,
                "discount_value": 0.00,
                "percentage_p": 0,
                "discount_amount": 0.00,
                "payable_amount": 160.00,
            },
            {
                "stock_item_id": 3,
                "quantity": 30,
                "stock_item_packaging_map_id": 5,
                "supplier_id": 1,
                "cost_per_pack": 20.00,
                "item_amount": 600.00,
                "discount_value": 0.00,
                "percentage_p": 0,
                "discount_amount": 0.00,
                "payable_amount": 600.00,
            }
        ] 
    }
    
    response = test_stock_item.do_stock_item_receiving(client, headers, data)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    
    data = {
        "stock_request_code": stock_request_code,
        "stock_request_status": "completed",
    }
    response = test_stock_item.do_update_stock_request_status(client, headers, data)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    
    response = test_stock_item.do_get_stock_request_grn(client, headers, stock_request_code)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    
#     data = {
#         "stock_request_code": stock_request_code,
#         "facility_id" : 4,
#         "supplier_id" : 1,
#         "stock_return_item_list": [
#             {
#                 "stock_item_id": 1,
#                 "quantity": 10,
#                 "measurement_id": 1,
#                 "supplier_id": 1,
#             },
#             {
#                 "stock_item_id": 2,
#                 "quantity": 20,
#                 "measurement_id": 1,
#                 "supplier_id": 1,
                
#             },
#             {
#                 "stock_item_id": 3,
#                 "quantity": 30,
#                 "measurement_id": 1,
#                 "supplier_id": 1,
#             }
#         ]
#     }
    
#     response = test_stock_return.do_add_stock_return(client,headers,data)
    
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
    
#     stock_return_id = j["stock_return_id"]
    
#     response = test_stock_return.do_get_stock_return(client,headers,stock_return_id)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
    
#     data = {
#         "stock_request_code": stock_request_code,
#         "facility_id" : 4,
#         "supplier_id" : 1,
#         "stock_return_item_list": [
#             {
#                 "stock_item_id": 1,
#                 "quantity": 10,
#                 "measurement_id": 1,
#                 "supplier_id": 1,
#             },
#             {
#                 "stock_item_id": 2,
#                 "quantity": 10,
#                 "measurement_id": 1,
#                 "supplier_id": 1,
                
#             },
#             {
#                 "stock_item_id": 3,
#                 "quantity": 30,
#                 "measurement_id": 1,
#                 "supplier_id": 1,
#             }
#         ]
#     }
    
#     response = test_stock_return.do_update_stock_return(client,headers,data,stock_return_id)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
    
#     data = {
#         "facility_id_list": [4,5,6],
#         "supplier_id_list": [1],
#         "start_date": None,
#         "end_date": None,
#     }
    
#     response = test_stock_return.do_get_stock_returns(client, headers, data)
    
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
    
# def test_e2e_stock_request_flow_for_transfer(client,headers):
#     """
#     Test E2E Stock Request Flow
#     """
#     data = {
#         "facility_id": 4,
#         "stock_request_type": "stock-transfer",
#         "to_facility_id" : 5,
#         "from_facility_id" : 4, 
#         "expected_delivery_date": "2020-01-01 00:00:00",
#         "expected_delivery_date": "2020-01-01 00:00:00", 
    
#         "stock_item_list": [
#             {
#                 "stock_item_id": 1,
#                 "quantity": 10,
#                 "measurement_id": 1,
#                 "supplier_id": 1,
#                 "quantity_per_pack": 10.00,
#             },
#             {
#                 "stock_item_id": 2,
#                 "quantity": 20,
#                 "measurement_id": 1,
#                 "supplier_id": 1,
#                 "quantity_per_pack": 5.00,
#             },
#             {
#                 "stock_item_id": 3,
#                 "quantity": 30,
#                 "measurement_id": 1,
#                 "supplier_id": 1,
#                 "quantity_per_pack": 15.00,
#             }
#         ]
#     }
    
#     response = test_stock_item.do_stock_item_request(client,headers,data)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
    
#     stock_request_code = j["stock_request_code"]
    
#     query = text("""
#         UPDATE FACILITY
#         SET facility_contact_name = :facility_contact_name,
#         facility_contact_phone_nr = :facility_contact_phone_nr,
#         facility_contact_email = :facility_contact_email,
#         facility_trn_id = :facility_trn_id,
#         address_line_1 = :address_line_1,
#         address_line_2 = :address_line_2,
#         supplier_id = :supplier_id
#         WHERE facility_id in :facility_id_list
#         AND meta_status = :meta_status
#     """)
    
#     db_engine = jqutils.get_db_engine()
    
#     with db_engine.connect() as conn:
#         result = conn.execute(query, facility_contact_name="OKISH", facility_contact_phone_nr="321-33-212", facility_contact_email="go@gmail.com", facility_trn_id="AAAA-0000", address_line_1="faciliy_123", address_line_2="nowhere", facility_id_list=[4,5,6], supplier_id=2, meta_status='active').rowcount
    
        
#     # data = {
#     #     "stock_request_code": stock_request_code,
#     #     "stock_request_status": "approved",
#     #     "approval_notes": "test notes"
#     # }
    
    
#     # response = test_stock_item.do_stock_request_approval(client,headers,data)
#     # j = json.loads(response.data)
#     # assert j["status"] == 'successful'
    
#     data = {
#         "stock_request_code": stock_request_code,
#         "stock_request_status": "sent",
#     }
    
#     response = test_stock_item.do_update_stock_request_status(client,headers,data)
    
    
#     response = test_stock_item.do_get_stock_request_email(client,headers,stock_request_code)
    
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
    
#     recipient_name = j["data"][0]["recipient_name"]
#     recipient_email = j["data"][0]["recipient_email"]
#     subject = j["data"][0]["subject"]
#     email_body = j["data"][0]["email_body"]
#     rendered_html = j["data"][0]["rendered_html"]
    
    
#     data = {
#         "stock_request_code": stock_request_code,
#         "email_list": [
#             {
#                 "recipient_name": "recipient_name", 
#                 "recipient_list": [recipient_email],
#                 "rendered_html": rendered_html,
#                 "email_body": rendered_html,
#                 "email_subject" : "subject"
#             }
#         ]
#     }
    
#     response = test_stock_item.do_stock_request_send(client,headers,data)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
    
#     data = {
#         "stock_request_code": stock_request_code,
#         "facility_id_list": [4,5,6],
#         'stock_activity_start_timestamp': "2020-01-01 00:00:00",
#         'stock_activity_end_timestamp': "2020-01-01 00:00:00",
#         'stock_activity_status': 'done',
#         'stock_item_list': [
#             {
#                 "stock_item_id": 1,
#                 "quantity": 10,
#                 "measurement_id": 1,
#                 "supplier_id": 1,
#                 "quantity_per_pack": 10.00,
#             },
#             {
#                 "stock_item_id": 2,
#                 "quantity": 20,
#                 "measurement_id": 1,
#                 "supplier_id": 1,
#                 "quantity_per_pack": 5.00,
#             },
#             {
#                 "stock_item_id": 3,
#                 "quantity": 30,
#                 "measurement_id": 1,
#                 "supplier_id": 1,
#                 "quantity_per_pack": 15.00,
#             }
#         ] 
#     }
    
    
#     response = test_stock_item.do_stock_item_receiving(client,headers,data)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
    
# def test_e2e_stock_request_flow_for_warehouse_request(client,headers):
#     """
#     Test E2E Stock Request Flow
#     """
#     data = {
#         "facility_id": 1,
#         "stock_request_type": "warehouse-procurement",
#         "to_facility_id" : 2,
#         "from_facility_id" : 1, 
#         "expected_delivery_date": "2020-01-01 00:00:00",
#         "expected_delivery_date": "2020-01-01 00:00:00", 
    
#         "stock_item_list": [
#             {
#                 "stock_item_id": 1,
#                 "quantity": 10,
#                 "measurement_id": 1,
#                 "supplier_id": 1,
#                 "quantity_per_pack": 10.00,
#             },
#             {
#                 "stock_item_id": 2,
#                 "quantity": 20,
#                 "measurement_id": 1,
#                 "supplier_id": 1,
#                 "quantity_per_pack": 5.00,
#             },
#             {
#                 "stock_item_id": 3,
#                 "quantity": 30,
#                 "measurement_id": 1,
#                 "supplier_id": 1,
#                 "quantity_per_pack": 15.00,
#             }
#         ]
#     }
    
#     response = test_stock_item.do_stock_item_request(client,headers,data)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
    
#     stock_request_code = j["stock_request_code"]
    
#     query = text("""
#         UPDATE FACILITY
#         SET facility_contact_name = :facility_contact_name,
#         facility_contact_phone_nr = :facility_contact_phone_nr,
#         facility_contact_email = :facility_contact_email,
#         facility_trn_id = :facility_trn_id,
#         address_line_1 = :address_line_1,
#         address_line_2 = :address_line_2,
#         supplier_id = :supplier_id
#         WHERE facility_id in :facility_id_list
#         AND meta_status = :meta_status
#     """)
    
#     db_engine = jqutils.get_db_engine()
    
#     with db_engine.connect() as conn:
#         result = conn.execute(query, facility_contact_name="OKISH", facility_contact_phone_nr="321-33-212", facility_contact_email="go@gmail.com", facility_trn_id="AAAA-0000", address_line_1="faciliy_123", address_line_2="nowhere", facility_id_list=[4,5,6], supplier_id=2, meta_status='active').rowcount
    
        
#     # data = {
#     #     "stock_request_code": stock_request_code,
#     #     "stock_request_status": "approved",
#     #     "approval_notes": "test notes"
#     # }
    
    
#     # response = test_stock_item.do_stock_request_approval(client,headers,data)
#     # j = json.loads(response.data)
#     # assert j["status"] == 'successful'
    
#     data = {
#         "stock_request_code": stock_request_code,
#         "stock_request_status": "sent",
#     }
    
#     response = test_stock_item.do_update_stock_request_status(client,headers,data)
    
    
#     response = test_stock_item.do_get_stock_request_email(client,headers,stock_request_code)
    
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
    
#     recipient_name = j["data"][0]["recipient_name"]
#     recipient_email = j["data"][0]["recipient_email"]
#     subject = j["data"][0]["subject"]
#     email_body = j["data"][0]["email_body"]
#     rendered_html = j["data"][0]["rendered_html"]
    
    # data = {
    #     "stock_request_code": stock_request_code,
    #     "email_list": [
    #         {
    #             "recipient_name": "recipient_name", 
    #             "recipient_list": [recipient_email],
    #             "rendered_html": rendered_html,
    #             "email_body": rendered_html,
    #             "email_subject" : "subject"
    #         }
    #     ]
    # }
    
#     response = test_stock_item.do_stock_request_send(client,headers,data)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
    
    # query = text("""
    #     SELECT supplyblox_request_code
    #     FROM stock_request
    #     WHERE stock_request_code = :stock_request_code
    #     AND meta_status = :meta_status
    # """)
    # with db_engine.connect() as conn:
    #     result = conn.execute(query, stock_request_code=stock_request_code, meta_status='active').fetchone()
    #     supplyblox_request_code = result['supplyblox_request_code']
    
    # data = {
    #     "stock_request_code": stock_request_code,
    #     "facility_id_list": [4,5,6],
    #     'stock_activity_start_timestamp': "2020-01-01 00:00:00",
    #     'stock_activity_end_timestamp': "2020-01-01 00:00:00",
    #     'stock_activity_status': 'done',
    #     'stock_item_list': [
    #         {
    #             "stock_item_id": 1,
    #             "quantity": 10,
    #             "measurement_id": 1,
    #             "supplier_id": 1,
    #             "quantity_per_pack": 10.00,
    #         },
    #         {
    #             "stock_item_id": 2,
    #             "quantity": 20,
    #             "measurement_id": 1,
    #             "supplier_id": 1,
    #             "quantity_per_pack": 5.00,
    #         },
    #         {
    #             "stock_item_id": 3,
    #             "quantity": 30,
    #             "measurement_id": 1,
    #             "supplier_id": 1,
    #             "quantity_per_pack": 15.00,
    #         }
    #     ] 
    # }
    
    
#     response = test_stock_item.do_stock_item_receiving(client,headers,data)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'

#     data = {
#         "supplyblox_request_status": "in-progress"
#     }

    # response = test_stock_item.do_update_stock_request_by_code(client,headers,supplyblox_request_code,data)
    # j = json.loads(response.data)
    # assert j["status"] == 'successful'

#     data = {
#         'jobs': [
#             {
#                 'job_code': 's_07215',
#                 'job_type': 'pick_and_put',
#                 'job_name': 'satwa-1',
#                 'associated_user': 'usman',
#                 'job_start_timestamp': '2023-10-03 15:43:58',
#                 'job_end_timestamp': '2023-10-03 15:44:58',
#                 'job_status': 'done',
#                 'docs': []
#             }
#         ]
#     }

    # response = test_stock_item.do_create_stock_request_jobs(client,headers,supplyblox_request_code,data)
    # j = json.loads(response.data)
    # assert j["status"] == 'successful'

#     data = {
#         'jobs': [
#             {
#                 'job_code': 's_07215',
#                 'products': [
#                     {
#                         'product_id': 1,
#                         'product_internal_code': 'abc',
#                         'quantity': 2,
#                         'measurement_id': 15,
#                         'measurement_name': 'pack',
#                         'tote_code': 't677712'
#                     }
#                 ]
#             }
#         ]
#     }

    # response = test_stock_item.do_update_stock_request_job_products(client,headers,supplyblox_request_code,data)
    # j = json.loads(response.data)
    # assert j["status"] == 'successful'

#     data = {
#         "supplyblox_request_status": "dispatched"
#     }

    # response = test_stock_item.do_update_stock_request_by_code(client,headers,supplyblox_request_code,data)
    # j = json.loads(response.data)
    # assert j["status"] == 'successful'

#     data = {
#         "supplyblox_request_status": "done"
#     }

    # response = test_stock_item.do_update_stock_request_by_code(client,headers,supplyblox_request_code,data)
    # j = json.loads(response.data)
    # assert j["status"] == 'successful'
    
# def test_e2e_stock_request_flow_for_department_transfer(client,headers):
    
#     data = {
#         "facility_id": 1,
#         "stock_request_type": "department-transfer",
#         "supplier_id" : 1,
#         "to_facility_id" : 1,
#         "from_facility_id" : 1, 
#         "expected_delivery_date": "2020-01-01 00:00:00",
    
#         "stock_item_list": [
#             {
#                 "stock_item_id": 1,
#                 "quantity": 10,
#                 "measurement_id": 1,
#                 "from_department_id": 1,
#                 "to_department_id": 2,
#                 "supplier_id": 1,
#                 "quantity_per_pack": 10.00,
#                 "cost_per_pack": 10.00,
#             },
#             {
#                 "stock_item_id": 2,
#                 "quantity": 20,
#                 "measurement_id": 1,
#                 "from_department_id": 1,
#                 "to_department_id": 2,
#                 "supplier_id": 1,
#                 "quantity_per_pack": 5.00,
#                 "cost_per_pack": 8.00,
#             },
#             {
#                 "stock_item_id": 3,
#                 "quantity": 30,
#                 "measurement_id": 1,
#                 "from_department_id": 1,
#                 "to_department_id": 2,
#                 "supplier_id": 1,
#                 "quantity_per_pack": 15.00,
#                 "cost_per_pack": 20.00,
#             }
#         ]
#     }
    
#     response = test_stock_item.do_stock_item_request(client,headers,data)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
    
# def test_e2e_supplier_request_flow_by_department(client,headers):
#     """
#     Test E2E Stock Request Flow
#     """
#     data = {
#         "facility_id": 4,
#         "stock_request_type": "supplier-procurement",
#         "supplier_id" : 1,
#         "to_facility_id" : 4,
#         "from_facility_id" : None, 
#         "expected_delivery_date": "2020-01-01 00:00:00",
    
#         "stock_item_list": [
#             {
#                 "stock_item_id": 1,
#                 "quantity": 10,
#                 "measurement_id": 1,
#                 "supplier_id": 1,
#                 "quantity_per_pack": 10.00,
#                 "cost_per_pack": 10.00,
#                 "item_amount": 100.00,
#                 "discount_value": 10.00,
#                 "percentage_p": 0,
#                 "discount_amount": 10.00,
#                 "payable_amount": 90.00
                
#             },
#             {
#                 "stock_item_id": 2,
#                 "quantity": 20,
#                 "measurement_id": 1,
#                 "supplier_id": 1,
#                 "quantity_per_pack": 5.00,
#                 "cost_per_pack": 8.00,
#                 "item_amount": 160.00,
#                 "discount_value": 0.00,
#                 "percentage_p": 0,
#                 "discount_amount": 0.00,
#                 "payable_amount": 160.00
#             },
#             {
#                 "stock_item_id": 3,
#                 "quantity": 30,
#                 "measurement_id": 1,
#                 "supplier_id": 1,
#                 "quantity_per_pack": 15.00,
#                 "cost_per_pack": 20.00,
#                 "item_amount": 600.00,
#                 "discount_value": 0.00,
#                 "percentage_p": 0,
#                 "discount_amount": 0.00,
#                 "payable_amount": 600.00
#             }
#         ]
#     }
    
#     response = test_stock_item.do_stock_item_request(client,headers,data)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
    
#     stock_request_code = j["stock_request_code"]
    
#     print(stock_request_code)
    
#     response = test_stock_item.do_get_stock_request(client,headers,stock_request_code)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
    
#     data = {
#         "stock_request_code": stock_request_code,
#         "stock_request_status": "sent",
#     }
    
#     response = test_stock_item.do_update_stock_request_status(client,headers,data)
    
    
#     response = test_stock_item.do_get_stock_request_email(client,headers,stock_request_code)
    
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
    
#     recipient_name = j["data"][0]["recipient_name"]
#     recipient_email = j["data"][0]["recipient_email"]
#     subject = j["data"][0]["subject"]
#     email_body = j["data"][0]["email_body"]
#     rendered_html = j["data"][0]["rendered_html"]
    
    
#     data = {
#         "stock_request_code": stock_request_code,
#         "email_list": [
#             {
#                 "recipient_name": "recipient_name", 
#                 "recipient_list": [recipient_email],
#                 "rendered_html": rendered_html,
#                 "email_body": rendered_html,
#                 "email_subject" : "subject"
#             }
#         ]
#     }
    
#     response = test_stock_item.do_stock_request_send(client,headers,data)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
    
#     data = {
#         "stock_request_code": stock_request_code,
#         "facility_id_list": [4,5,6],
#         'stock_activity_start_timestamp': "2020-01-01 00:00:00",
#         'stock_activity_end_timestamp': "2020-01-01 00:00:00",
#         'stock_activity_status': 'done',
#         'department_feature_enabled_p': 1,
#         'stock_item_list': [
#             {
#                 "stock_item_id": 1,
#                 "quantity": 10,
#                 "measurement_id": 1,
#                 "supplier_id": 1,
#                 "cost_per_pack": 10.00,
#                 "to_department_id": 3,
#                 "quantity_per_pack": 10.00,
#             },
#             {
#                 "stock_item_id": 2,
#                 "quantity": 20,
#                 "measurement_id": 1,
#                 "supplier_id": 1,
#                 "cost_per_pack": 8.00,
#                 "to_department_id": 3,
#                 "quantity_per_pack": 5.00,
#             },
#             {
#                 "stock_item_id": 3,
#                 "quantity": 30,
#                 "measurement_id": 1,
#                 "supplier_id": 1,
#                 "cost_per_pack": 20.00,
#                 "to_department_id": 3,
#                 "quantity_per_pack": 15.00,
#             }
#         ] 
#     }
    
    
#     response = test_stock_item.do_stock_item_receiving(client,headers,data)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
    
#     data = {
#         "stock_request_code": stock_request_code,
#         "stock_request_status": "completed",
#     }
    
#     response = test_stock_item.do_update_stock_request_status(client,headers,data)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
    
# def test_e2e_transfer_request_flow_by_department(client,headers):
#     """
#     Test E2E Stock Request Flow
#     """
#     data = {
#         "facility_id": 4,
#         "stock_request_type": "stock-transfer",
#         "supplier_id" : 1,
#         "to_facility_id" : 5,
#         "from_facility_id" : 4, 
#         "expected_delivery_date": "2020-01-01 00:00:00",
    
#         "stock_item_list": [
#             {
#                 "stock_item_id": 1,
#                 "quantity": 10,
#                 "measurement_id": 1,
#                 "supplier_id": 1,
#                 "quantity_per_pack": 10.00,
#                 "from_department_id": 3,
#                 "cost_per_pack": 10.00,
#             },
#             {
#                 "stock_item_id": 2,
#                 "quantity": 20,
#                 "measurement_id": 1,
#                 "supplier_id": 1,
#                 "quantity_per_pack": 5.00,
#                 "from_department_id": 3,
#                 "cost_per_pack": 8.00,
#             },
#             {
#                 "stock_item_id": 3,
#                 "quantity": 30,
#                 "measurement_id": 1,
#                 "supplier_id": 1,
#                 "quantity_per_pack": 15.00,
#                 "from_department_id": 3,
#                 "cost_per_pack": 20.00,
#             }
#         ]
#     }
    
#     response = test_stock_item.do_stock_item_request(client,headers,data)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
    
#     stock_request_code = j["stock_request_code"]
    
#     print(stock_request_code)
    
#     response = test_stock_item.do_get_stock_request(client,headers,stock_request_code)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
    
#     data = {
#         "stock_request_code": stock_request_code,
#         "stock_request_status": "sent",
#     }
    
#     response = test_stock_item.do_update_stock_request_status(client,headers,data)
    
    
#     response = test_stock_item.do_get_stock_request_email(client,headers,stock_request_code)
    
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
    
#     recipient_name = j["data"][0]["recipient_name"]
#     recipient_email = j["data"][0]["recipient_email"]
#     subject = j["data"][0]["subject"]
#     email_body = j["data"][0]["email_body"]
#     rendered_html = j["data"][0]["rendered_html"]
    
    
#     data = {
#         "stock_request_code": stock_request_code,
#         "email_list": [
#             {
#                 "recipient_name": "recipient_name", 
#                 "recipient_list": [recipient_email],
#                 "rendered_html": rendered_html,
#                 "email_body": rendered_html,
#                 "email_subject" : "subject"
#             }
#         ]
#     }
    
#     response = test_stock_item.do_stock_request_send(client,headers,data)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
    
#     data = {
#         "stock_request_code": stock_request_code,
#         "facility_id_list": [4,5,6],
#         'stock_activity_start_timestamp': "2020-01-01 00:00:00",
#         'stock_activity_end_timestamp': "2020-01-01 00:00:00",
#         'stock_activity_status': 'done',
#         'department_feature_enabled_p': 1,
#         'stock_item_list': [
#             {
#                 "stock_item_id": 1,
#                 "quantity": 10,
#                 "measurement_id": 1,
#                 "supplier_id": 1,
#                 "cost_per_pack": 10.00,
#                 "from_department_id": 3,
#                 "to_department_id": 4,
#                 "quantity_per_pack": 10.00,
#             },
#             {
#                 "stock_item_id": 2,
#                 "quantity": 20,
#                 "measurement_id": 1,
#                 "supplier_id": 1,
#                 "cost_per_pack": 8.00,
#                 "from_department_id": 3,
#                 "to_department_id": 4,
#                 "quantity_per_pack": 5.00,
#             },
#             {
#                 "stock_item_id": 3,
#                 "quantity": 15,
#                 "measurement_id": 1,
#                 "supplier_id": 1,
#                 "cost_per_pack": 20.00,
#                 "from_department_id": 3,
#                 "to_department_id": 4,
#                 "quantity_per_pack": 15.00,
#             },
#             {
#                 "stock_item_id": 3,
#                 "quantity": 15,
#                 "measurement_id": 1,
#                 "supplier_id": 1,
#                 "cost_per_pack": 20.00,
#                 "from_department_id": 3,
#                 "to_department_id": 4,
#                 "quantity_per_pack": 15.00,
#             }
#         ] 
#     }
    
    
#     response = test_stock_item.do_stock_item_receiving(client,headers,data)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
    
#     data = {
#         "stock_request_code": stock_request_code,
#         "stock_request_status": "completed",
#     }
    
#     response = test_stock_item.do_update_stock_request_status(client,headers,data)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'

# def test_e2e_stock_request_flow_for_warehouse_request_by_department(client,headers):
#     """
#     Test E2E Stock Request Flow
#     """
#     data = {
#         "facility_id": 4,
#         "stock_request_type": "warehouse-procurement",
#         "supplier_id" : 1,
#         "to_facility_id" : 4,
#         "from_facility_id" : 6, 
#         "expected_delivery_date": "2020-01-01 00:00:00",
    
#         "stock_item_list": [
#             {
#                 "stock_item_id": 1,
#                 "quantity": 10,
#                 "measurement_id": 1,
#                 "supplier_id": 1,
#                 "quantity_per_pack": 10.00,
#                 "cost_per_pack": 10.00,
#             },
#             {
#                 "stock_item_id": 2,
#                 "quantity": 20,
#                 "measurement_id": 1,
#                 "supplier_id": 1,
#                 "quantity_per_pack": 5.00,
#                 "cost_per_pack": 8.00,
#             },
#             {
#                 "stock_item_id": 3,
#                 "quantity": 30,
#                 "measurement_id": 1,
#                 "supplier_id": 1,
#                 "quantity_per_pack": 15.00,
#                 "cost_per_pack": 20.00,
#             }
#         ]
#     }
    
#     response = test_stock_item.do_stock_item_request(client,headers,data)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
    
#     stock_request_code = j["stock_request_code"]
    
#     print(stock_request_code)
    
#     response = test_stock_item.do_get_stock_request(client,headers,stock_request_code)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
    
#     data = {
#         "stock_request_code": stock_request_code,
#         "stock_request_status": "sent",
#     }
    
#     response = test_stock_item.do_update_stock_request_status(client,headers,data)
    
    
#     response = test_stock_item.do_get_stock_request_email(client,headers,stock_request_code)
    
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
    
#     recipient_name = j["data"][0]["recipient_name"]
#     recipient_email = j["data"][0]["recipient_email"]
#     subject = j["data"][0]["subject"]
#     email_body = j["data"][0]["email_body"]
#     rendered_html = j["data"][0]["rendered_html"]
    
    
#     data = {
#         "stock_request_code": stock_request_code,
#         "email_list": [
#             {
#                 "recipient_name": "recipient_name", 
#                 "recipient_list": [recipient_email],
#                 "rendered_html": rendered_html,
#                 "email_body": rendered_html,
#                 "email_subject" : "subject"
#             }
#         ]
#     }
    
#     response = test_stock_item.do_stock_request_send(client,headers,data)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
    
#     data = {
#         "stock_request_code": stock_request_code,
#         "facility_id_list": [4,5,6],
#         'stock_activity_start_timestamp': "2020-01-01 00:00:00",
#         'stock_activity_end_timestamp': "2020-01-01 00:00:00",
#         'stock_activity_status': 'done',
#         'department_feature_enabled_p': 1,
#         'stock_item_list': [
#             {
#                 "stock_item_id": 1,
#                 "quantity": 10,
#                 "measurement_id": 1,
#                 "supplier_id": 1,
#                 "cost_per_pack": 10.00,
#                 "from_department_id": 3,
#                 "to_department_id": 4,
#                 "quantity_per_pack": 10.00,
#             },
#             {
#                 "stock_item_id": 2,
#                 "quantity": 20,
#                 "measurement_id": 1,
#                 "supplier_id": 1,
#                 "cost_per_pack": 8.00,
#                 "from_department_id": 3,
#                 "to_department_id": 4,
#                 "quantity_per_pack": 5.00,
#             },
#             {
#                 "stock_item_id": 3,
#                 "quantity": 15,
#                 "measurement_id": 1,
#                 "supplier_id": 1,
#                 "cost_per_pack": 20.00,
#                 "from_department_id": 3,
#                 "to_department_id": 4,
#                 "quantity_per_pack": 15.00,
#             },
#             {
#                 "stock_item_id": 3,
#                 "quantity": 15,
#                 "measurement_id": 1,
#                 "supplier_id": 1,
#                 "cost_per_pack": 20.00,
#                 "from_department_id": 3,
#                 "to_department_id": 4,
#                 "quantity_per_pack": 15.00,
#             }
#         ]
#     }
    
#     response = test_stock_item.do_stock_item_receiving(client,headers,data)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
    
#     data = {
#         "stock_request_code": stock_request_code,
#         "stock_request_status": "completed",
#     }
    
#     response = test_stock_item.do_update_stock_request_status(client,headers,data)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
    
    