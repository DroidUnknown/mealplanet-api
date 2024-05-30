import json
import datetime
import pytest

from sqlalchemy import text

from tests import test_customer_order, test_enterprise_back_office, test_stock_item, test_supplier, test_facility, test_station, test_user
from tests.test_merchant import do_add_merchant_and_user, do_get_customer_orders_by_merchant
from tests.test_payment_point_area import do_add_payment_point_area
from tests.test_payment_point import do_add_payment_point
from tests.test_branch import do_create_branch
from utils import jqutils

base_api_url = "/api"

##############
# TEST-CASE
##############

@pytest.fixture(scope="module", autouse=True)
def merchant_setup(client):
    
    """
    Setup merchant features
    """
    merchant_name = "tresko"
    merchant_features = [
        {
            "feature_id":1, # card-payment
            "enabled": 1
        },
        {
            "feature_id":14, # iblinkpos
            "enabled": 1
        },
        {
            "feature_id":20, # financials
            "enabled": 1
        },
        {
            "feature_id":19, #kitchen-display-system
            "enabled": 1
        }
    ]
    
    """
    Create New Merchant (Normal)
    """
    logged_in_user_details, merchant_settings, logged_in_order_panel_details, logged_in_marketplace_details = do_add_merchant_and_user(client, create_order_panel_user=True, create_marketplace_user=False, merchant_features=merchant_features, merchant_name=merchant_name)

    """
    Normal Transaction Request Creation
    """
    user_headers = {
        "X-User-Id": logged_in_user_details["user_id"],
        "X-Access-Token": logged_in_user_details["access_token"],
        "X-Api-Key": logged_in_user_details["merchant_api_key"]
    }

    """
    Order Panel Request Creation
    """
    order_panel_headers = {
        "X-User-Id": logged_in_order_panel_details["user_id"],
        "X-Access-Token": logged_in_order_panel_details["access_token"],
        "X-Api-Key": logged_in_order_panel_details["merchant_api_key"]
    }

    merchant_details = {
        "merchant_id": merchant_settings["merchant_id"],
        "merchant_name": merchant_settings["merchant_name"],
        "merchant_code": jqutils.get_column_by_id(str(merchant_settings["merchant_id"]), "merchant_code", "merchant"),
        "financial_merchant_id": 3,
        "financial_organization_id": 3,
    }

    """
    Create payment point area for merchant
    """
    payload = {
        "parent_payment_point_area_id": None,
        "payment_point_area_type_id": 1,
        "merchant_id": logged_in_user_details["merchant_id"],
        "payment_point_area_name": "indoor dining area",
        "payment_point_area_description": "desc"
    }
    response = do_add_payment_point_area(client, user_headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'add_payment_point_area'
    payment_point_area_id = j["payment_point_area_id"]

    """
    Create payment point inside the payment point area
    """
    payload = {
        "payment_point_area_id": payment_point_area_id,
        "payment_point_type_id": 1,
        "payment_point_name": "table 1",
        "payment_point_description": "desc",
        "interface_type_id": 1,
    }
    response = do_add_payment_point(client, user_headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'add_payment_point'
    payment_point_id = j["payment_point_id"]

    """
    Create pos enabled branch
    """
    brand_name = "tresko"
    facility_name = "jvc"
    
    payload = {
        "brand_name": brand_name,
        "facility_name": facility_name,
        "marketplace_id": None,
        "external_brand_id": None,
        "external_branch_id": None,
        "external_branch_code": None,
        "marketplace_name": None,
        "pos_enabled_p": 1,
        "city_name": "dubai",
        "country_name": "united arab emirates",
        "latitude": 25.067566,
        "longitude": 55.153897,
    }
    response = do_create_branch(client, user_headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'create_branch'
    assert j["branch_id"], "branch id not generated"
    branch_id = j["branch_id"]
    brand_id = j["brand_id"]
    facility_id = j["facility_id"]

    """
    Setup financials for this merchant
    """
    db_engine = jqutils.get_db_engine()
    
    query = text("""
        UPDATE merchant
        SET financial_merchant_id = :financial_merchant_id,
        financial_organization_id = :financial_organization_id
        WHERE merchant_id = :merchant_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, financial_merchant_id=merchant_details["financial_merchant_id"], financial_organization_id=merchant_details["financial_organization_id"], merchant_id=merchant_details["merchant_id"], meta_status='active').rowcount
        assert result, "merchant financials not updated"

    """
    Setup posting config for this merchant
    """
    with open("tests/testdata/posting_config.json", "r") as f:
        configs = json.load(f)
        financial_organization_id = configs[merchant_name]['financial_organization_id']
        config_list = configs[merchant_name]['config_list']
    
    posting_config_list = []
    for one_config in config_list:
        posting_config_list.append({
            "merchant_id": merchant_details["merchant_id"],
            "financial_organization_id": financial_organization_id,
            "financial_ledger_account_id": one_config["financial_ledger_account_id"],
            "account_category": one_config["account_category"],
            "posting_type": one_config["posting_type"],
            "filter_expression": one_config["filter_expression"],
            "aggregate_function": one_config["aggregate_function"],
            "description_template": one_config["description_template"],
            "transaction_type": one_config["transaction_type"],
            "amount_expression": one_config["amount_expression"],
            "split_amount_expression": one_config["split_amount_expression"],
            "meta_status": "active",
        })
    
    query = text("""
        INSERT INTO posting_config (merchant_id, financial_organization_id, financial_ledger_account_id, account_category,
        posting_type, filter_expression, aggregate_function, description_template, transaction_type, amount_expression, split_amount_expression, meta_status)
        VALUES (:merchant_id, :financial_organization_id, :financial_ledger_account_id, :account_category,
        :posting_type, :filter_expression, :aggregate_function, :description_template, :transaction_type, :amount_expression, :split_amount_expression, :meta_status)
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, posting_config_list).rowcount
        assert result, "unable to insert posting config"

    """
    Setup station screens
    """
    station_username = brand_name + "-" + facility_name + "-001"
    station_password = brand_name + "2024"
    
    response = test_user.do_check_username_availability(client, user_headers, station_username)
    assert response.status_code == 200
    assert response.json['status'] == 'successful'
    assert response.json['available_p'] == True
    
    payload = {
        "facility_id": facility_id,
        "station_name": None,
        "station_description": None,
        "station_access_code": None,
        "preparation_station_p": 1,
        "dispatch_station_p": 0,
        "station_rule_list": [{
            "rule_type": "preparation",
            "station_rule_expression": f"facility({facility_id})"
        }],
        "username": station_username,
        "password": station_password,
    }
    response = test_station.do_add_station(client, user_headers, payload)
    assert response.status_code == 200
    response_body = json.loads(response.data)
    assert response_body["status"] == 'successful'
    assert response_body["action"] == 'add_station'
    
    station_id = response_body["data"]["station_id"]
    station_code = response_body["data"]["station_code"]

    # -----------------------------------------------------------------
    # TO BE USED IF NOT USING THE PRE-LOADED MENU FROM DATA MIGRATION
    # -----------------------------------------------------------------

    # branch_id = j["branch_id"]
    
    # with open("tests/testdata/menus/sample_menu.json", encoding='utf-8') as f:
    #     file_data = json.load(f)
    #     do_upload_brand_menu_items(client, user_headers, file_data)

    # response = do_generate_menu(client, user_headers, branch_id)
    # assert response.status_code == 200
    # j = json.loads(response.data)
    # assert j["status"] == 'successful'
    # assert j["action"] == 'generate_menu'

    # -----------------------------------------------------------------

    yield user_headers, order_panel_headers, merchant_details, payment_point_id

# ----------------------------------------------------------------------------------------------------------------------------------

def test_e2e_normal_customer_order_flow(client, merchant_setup):
    user_headers, order_panel_headers, merchant_details, payment_point_id = merchant_setup

    merchant_id = merchant_details["merchant_id"]
    merchant_code = merchant_details["merchant_code"]

    db_engine = jqutils.get_db_engine()
    
    query = text("""
        SELECT discount_id, discount_name
        FROM discount
        WHERE meta_status = :meta_status
        AND merchant_id = :merchant_id
        AND discount_name in :discount_name_list
    """)
    with db_engine.connect() as conn:
        results = conn.execute(query, merchant_id=merchant_id, discount_name_list=["staff-meal", "late night discount"], meta_status='active').fetchall()
        assert results, "discount not found"
        for one_result in results:
            if one_result["discount_name"] == "staff-meal":
                order_level_discount_id = one_result["discount_id"]
            elif one_result["discount_name"] == "late night discount":
                line_item_discount_id = one_result["discount_id"]

    """
    Correct POS customer orders which should be verified before punching
    """
    test_file_list = []
    test_file_list.append("tests/testdata/customer_orders/pos/01_menu_items_only.json")
    test_file_list.append("tests/testdata/customer_orders/pos/02_menu_items_with_modifiers.json")
    # test_file_list.append("tests/testdata/customer_orders/pos/03_offers_only_NOT_IMPLEMENTED.json")
    # test_file_list.append("tests/testdata/customer_orders/pos/04_offers_with_items_and_modifiers_NOT_IMPLEMENTED.json")
    test_file_list.append("tests/testdata/customer_orders/pos/05_all_item_types.json")
    test_file_list.append("tests/testdata/customer_orders/pos/06_all_item_types_for_payment_point.json")
    test_file_list.append("tests/testdata/customer_orders/pos/07_all_item_types_with_pre_made_discount.json")
    test_file_list.append("tests/testdata/customer_orders/pos/08_all_item_types_with_custom_discount.json")
    test_file_list.append("tests/testdata/customer_orders/pos/09_all_item_types_dine_in_pay_later.json")
    test_file_list.append("tests/testdata/customer_orders/pos/10_all_item_types_with_line_item_discount.json")
    test_file_list.append("tests/testdata/customer_orders/pos/11_menu_items_with_float_quantity_modifiers.json")
    print("")
    for idx, one_test_file in enumerate(test_file_list):
        with open(one_test_file, encoding='utf-8') as f:
            transaction_payload = json.load(f)
            
            if "payment_point" in one_test_file:
                transaction_payload["payment_point_id"] = payment_point_id
            
            transaction_payload["merchant_code"] = merchant_code
            transaction_payload["expiry_timestamp"] = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")

            payable_amount = transaction_payload["payment_details"]["payable_amount"]
            discount_amount = transaction_payload["payment_details"]["discount_amount"]
            tax_amount = transaction_payload["payment_details"]["tax_amount"]
            tip_amount = transaction_payload["payment_details"]["tip_amount"]

            if "discount_list" in transaction_payload:
                if len(transaction_payload["discount_list"]) > 0:
                    if transaction_payload["discount_list"][0]["discount_id"] == 1:
                        transaction_payload["discount_list"][0]["discount_id"] = order_level_discount_id
                    elif transaction_payload["discount_list"][0]["discount_id"] == 2:
                        transaction_payload["discount_list"][0]["discount_id"] = line_item_discount_id

        print(f"Running test case {idx+1} with file {one_test_file}")

        response = test_customer_order.do_calculate_order(client, order_panel_headers, transaction_payload)    
        j = json.loads(response.data)
        assert j["status"] == 'successful'

        response = test_customer_order.do_create_customer_order(client, order_panel_headers, transaction_payload)    
        j = json.loads(response.data)
        assert j["status"] == 'successful'

        customer_order_id = j["customer_order_id"]
        order_code = j["order_code"]

        """
        Get customer order details
        """
        response = test_customer_order.do_get_customer_order(client, order_panel_headers, customer_order_id)
        assert response.status_code == 200
        j = json.loads(response.data)
        assert j["status"] == 'successful'
        assert j["action"] == 'get_customer_order'

        order_code = j["data"]["order_code"]
        
        qrcode = f"IBX F_ASD123 CO_{order_code.upper()} T_12398198273198"
        response = test_customer_order.do_get_customer_order_by_qrcode(client, order_panel_headers, qrcode)
        assert response.status_code == 200
        j = json.loads(response.data)
        assert j["status"] == 'successful'
        assert j["action"] == 'get_customer_order'
    
        assert j["data"]["payable_amount"] == payable_amount, f"payable_amount should be {payable_amount}. Currently it is {j['data']['payable_amount']}"
        assert j["data"]["discount_amount"] == discount_amount, f"discount_amount should be {discount_amount}. Currently it is {j['data']['discount_amount']}"
        assert j["data"]["tax_amount"] == tax_amount, f"tax_amount should be {tax_amount}. Currently it is {j['data']['tax_amount']}"
        assert j["data"]["tip_amount"] == tip_amount, f"tip_amount should be {tip_amount}. Currently it is {j['data']['tip_amount']}"

        """
        Update customer order status to dispatched
        """
        payload = {
            "customer_order_id": customer_order_id,
            "order_status": "dispatched",
            "action_timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        response = test_customer_order.do_update_customer_order(client, order_panel_headers, payload)
        assert response.status_code == 200
        j = json.loads(response.data)
        assert j["status"] == 'successful'

    """
    Correct 'item_list' so sum of all prices match 'payable_amount'
    """
    test_file_list = []
    test_file_list.append("tests/testdata/customer_orders/correct/01_menu_items_only.json")
    test_file_list.append("tests/testdata/customer_orders/correct/02_menu_items_with_modifiers.json")
    test_file_list.append("tests/testdata/customer_orders/correct/03_offers_only.json")
    test_file_list.append("tests/testdata/customer_orders/correct/04_offers_with_items_and_modifiers.json")
    test_file_list.append("tests/testdata/customer_orders/correct/05_all_item_types.json")
    test_file_list.append("tests/testdata/customer_orders/deliveroo/translated_order_merchant_fulfilled_payload.json")
    test_file_list.append("tests/testdata/customer_orders/deliveroo/translated_order_marketplace_fulfilled_payload.json")
    test_file_list.append("tests/testdata/customer_orders/careem/translated_order_merchant_fulfilled_payload.json")
    test_file_list.append("tests/testdata/customer_orders/careem/translated_order_marketplace_fulfilled_payload.json")
    test_file_list.append("tests/testdata/customer_orders/talabat/translated_order_marketplace_fulfilled_payload.json")
    test_file_list.append("tests/testdata/customer_orders/noon/translated_order_marketplace_fulfilled_payload.json")
    test_file_list.append("tests/testdata/customer_orders/correct/06_all_item_types_for_payment_point.json")
    print("")
    for idx, one_test_file in enumerate(test_file_list):
        with open(one_test_file, encoding='utf-8') as f:
            transaction_payload = json.load(f)
            transaction_payload["payment_point_id"] = payment_point_id
            transaction_payload["merchant_code"] = merchant_code
            transaction_payload["expiry_timestamp"] = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")

            payable_amount = transaction_payload["payment_details"]["payable_amount"]
            discount_amount = transaction_payload["payment_details"]["discount_amount"]
            tax_amount = transaction_payload["payment_details"]["tax_amount"]
            tip_amount = transaction_payload["payment_details"]["tip_amount"]

        print(f"Running test case {idx+1} with file {one_test_file}")

        response = test_customer_order.do_create_customer_order(client, order_panel_headers, transaction_payload)    
        j = json.loads(response.data)
        assert j["status"] == 'successful'

        customer_order_id = j["customer_order_id"]
        order_code = j["order_code"]

        """
        Get customer order details
        """
        response = test_customer_order.do_get_customer_order(client, order_panel_headers, customer_order_id)
        assert response.status_code == 200
        j = json.loads(response.data)
        assert j["status"] == 'successful'
        assert j["action"] == 'get_customer_order'

        # """
        # Generate merchant transaction for customer order
        # """
        if transaction_payload['order_placement_channel_id'] != 2:
            response = test_customer_order.do_generate_merchant_transaction_for_customer_order(client, order_panel_headers, customer_order_id)
            assert response.status_code == 200
            j = json.loads(response.data)

    """
    Get all customer orders
    """
    payload = {}
    response = test_customer_order.do_get_customer_orders(client, order_panel_headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert len(j["data"]) > 0
    assert j["action"] == 'get_customer_orders'

    """
    Update customer order status to accepted
    """
    payload = {
        "customer_order_id": customer_order_id,
        "order_status": "accepted",
        "action_timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    response = test_customer_order.do_update_customer_order(client, order_panel_headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'

    db_engine = jqutils.get_db_engine()
    query = text("""
        SELECT order_status
        FROM customer_order
        WHERE customer_order_id = :customer_order_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, customer_order_id=customer_order_id, meta_status='active').fetchone()
        assert result, "customer order status not updated"
        order_status = result["order_status"]
    
    """
    Get customer order status
    """
    response = test_customer_order.do_get_customer_order_status(client, order_panel_headers, customer_order_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["data"]["order_status"] == order_status, f"order_status should be {order_status}. Currently it is {j['order_status']}"

    """
    Get customer orders with accepted and created statuses
    """
    payload = {
        "order_status": ["accepted", "created"]
    }
    response = test_customer_order.do_get_customer_orders(client, order_panel_headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert len(j["data"]) > 0
    assert j["action"] == 'get_customer_orders'

    """
    Reprint customer order receipt
    """
    payload = {
        "customer_order_id": 17
    }
    response = test_customer_order.do_print_customer_order_receipt(client, order_panel_headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'print_customer_order_receipt'

    """
    Test getting customer orders by merchant id
    """
    order_status_list = ["created"]

    query = text("""
        SELECT customer_order_id, facility_id
        FROM customer_order
        WHERE merchant_id = :merchant_id
        AND order_status IN :order_status_list
        AND facility_id IS NOT NULL
        AND meta_status = :meta_status
        ORDER BY customer_order_id DESC
    """)
    with db_engine.connect() as conn:
        results = conn.execute(query, merchant_id=merchant_id, order_status_list=order_status_list, meta_status='active').fetchall()
        assert results, f"Failed to get customer order for merchant id {merchant_id}"
        customer_order_id_list = [result["customer_order_id"] for result in results]
        facility_id_list = [result["facility_id"] for result in results]

    payload = {
        "order_status_list": order_status_list,
        "facility_id_list": list(set(facility_id_list)),
    }
    response = do_get_customer_orders_by_merchant(client, user_headers, merchant_id, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["customer_order_id_list"]['created'] == customer_order_id_list, "invalid customer order id list"

    payload = {
        "merchant_id": merchant_id,
        "from_timestamp": None,
        "to_timestamp": None,
        "branch_id_list": [],
        "brand_id_list": [],
        "marketplace_id_list": [],
        "facility_id_list": [],
        "order_status_list": order_status_list
    }
    response = test_customer_order.do_get_customer_order_stats(client, user_headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'

    total_order_count_api = j["data"]["total_order_count"]
    total_count_db = len(customer_order_id_list)
    assert total_order_count_api == total_count_db, "total count mismatch"

    payload = {
        "merchant_id": merchant_id,
        "after_id": None,
        "before_id": None,
        "from_timestamp": None,
        "to_timestamp": None,
        "branch_id_list": [],
        "brand_id_list": [],
        "marketplace_id_list": [],
        "facility_id_list": [],
        "fulfillment_type_id_list": [],
        "order_status_list": order_status_list,
        "page_size": 2,
        "page_number": 1,
        "sort_by_list": [],
    }
    response = test_customer_order.do_get_customer_order_history(client, user_headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    
    total_count_api = j["data"]["total_count"]
    total_count_db = len(customer_order_id_list)
    order_count = len(j["data"]["customer_order_list"])

    while order_count < total_count_api:
        payload["page_number"] += 1
        response = test_customer_order.do_get_customer_order_history(client, user_headers, payload)
        assert response.status_code == 200
        j = json.loads(response.data)
        assert j["status"] == 'successful'
        order_count += len(j["data"]["customer_order_list"])
    
    assert order_count == total_count_db, "pagination failed"
    
    # """
    # Cancel a customer order
    # """
    # payload = {
    #     "cancellation_reason_id": 1,
    #     "cancellation_reason_note": None,
    # }
    # response = test_customer_order.do_cancel_customer_order(client, order_panel_headers, customer_order_id, payload)
    # assert response.status_code == 200
    # j = json.loads(response.data)
    # assert j["status"] == 'successful'
    # assert j["action"] == 'cancel_customer_order'

    # # validate that cancellation happened both on customer order and merchant transaction
    # query = text("""
    #     SELECT co.order_status, co.cancellation_reason_id, co.cancellation_reason_note, co.merchant_transaction_id, mt.transaction_status,
    #     mt.cancellation_reason_id as mt_cancellation_reason_id, mt.cancellation_reason_note as mt_cancellation_reason_note, co.order_cancelled_timestamp
    #     FROM customer_order co
    #     JOIN merchant_transaction mt ON mt.merchant_transaction_id = co.merchant_transaction_id
    #     WHERE co.customer_order_id = :customer_order_id
    #     AND co.meta_status = :meta_status
    # """)
    # with db_engine.connect() as conn:
    #     result = conn.execute(query, customer_order_id=customer_order_id, meta_status='active').fetchone()
    #     assert result, "customer order status not updated"
    
    # order_status = result["order_status"]
    # cancellation_reason_id = result["cancellation_reason_id"]
    # cancellation_reason_note = result["cancellation_reason_note"]
    # merchant_transaction_id = result["merchant_transaction_id"]
    # transaction_status = result["transaction_status"]
    # mt_cancellation_reason_id = result["mt_cancellation_reason_id"]
    # mt_cancellation_reason_note = result["mt_cancellation_reason_note"]
    # order_cancelled_timestamp = result["order_cancelled_timestamp"]

    # assert order_status == "cancelled"
    # assert cancellation_reason_id == 1
    # assert cancellation_reason_note == None
    # assert merchant_transaction_id
    # assert transaction_status == "cancelled"
    # assert mt_cancellation_reason_id == 1
    # assert mt_cancellation_reason_note == None
    # assert order_cancelled_timestamp

    """MODIFY PAYMENT METHOD BEFORE AND AFTER DISPATCH"""

    with open("tests/testdata/customer_orders/pos/02_menu_items_with_modifiers.json", encoding='utf-8') as f:
        transaction_payload = json.load(f)
        
        if "payment_point" in one_test_file:
            transaction_payload["payment_point_id"] = payment_point_id
        
        transaction_payload["merchant_code"] = merchant_code
        transaction_payload["expiry_timestamp"] = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")

        payable_amount = transaction_payload["payment_details"]["payable_amount"]
        discount_amount = transaction_payload["payment_details"]["discount_amount"]
        tax_amount = transaction_payload["payment_details"]["tax_amount"]
        tip_amount = transaction_payload["payment_details"]["tip_amount"]

        response = test_customer_order.do_calculate_order(client, order_panel_headers, transaction_payload)    
        response_body = json.loads(response.data)
        assert response_body["status"] == 'successful'
        
        response = test_customer_order.do_create_customer_order(client, order_panel_headers, transaction_payload)    
        response_body = json.loads(response.data)
        assert response_body["status"] == 'successful'

        customer_order_id = response_body["customer_order_id"]

    """
    Get customer order details
    """
    response = test_customer_order.do_get_customer_order(client, order_panel_headers, customer_order_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_customer_order'

    assert j["data"]["payable_amount"] == payable_amount, f"payable_amount should be {payable_amount}. Currently it is {j['data']['payable_amount']}"
    assert j["data"]["discount_amount"] == discount_amount, f"discount_amount should be {discount_amount}. Currently it is {j['data']['discount_amount']}"
    assert j["data"]["tax_amount"] == tax_amount, f"tax_amount should be {tax_amount}. Currently it is {j['data']['tax_amount']}"
    assert j["data"]["tip_amount"] == tip_amount, f"tip_amount should be {tip_amount}. Currently it is {j['data']['tip_amount']}"
    assert j["data"]["payment_method_name"] == "card", f"payment_method_name should be card. Currently it is {j['data']['payment_method_name']}"

    """
    Update customer order payment method before dispatch to cash (original was card)
    """
    payload = {
        "payment_method_id": 3,
        "delivery_amount": 2
    }
    response = test_customer_order.do_update_customer_order_payment_detail(client, order_panel_headers, payload, customer_order_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'update_customer_order_payment_detail'

    """
    Get customer order details
    """
    response = test_customer_order.do_get_customer_order(client, order_panel_headers, customer_order_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_customer_order'

    assert j["data"]["payment_method_name"] == "cash", f"payment_method_name should be cash. Currently it is {j['data']['payment_method_name']}"

    """
    Update customer order status to dispatched
    """
    payload = {
        "customer_order_id": customer_order_id,
        "order_status": "dispatched",
        "action_timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    response = test_customer_order.do_update_customer_order(client, order_panel_headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'

    """
    Update customer order payment method after dispatch to visa (original was cash)
    """
    payload = {
        "payment_method_id": 6,
        "delivery_amount": 7
    }
    response = test_customer_order.do_update_customer_order_payment_detail(client, order_panel_headers, payload, customer_order_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'update_customer_order_payment_detail'

    """
    Get customer order details
    """
    response = test_customer_order.do_get_customer_order(client, order_panel_headers, customer_order_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_customer_order'

    assert j["data"]["payment_method_name"] == "visa", f"payment_method_name should be visa. Currently it is {j['data']['payment_method_name']}"

def test_e2e_customer_order_financial_posting_flow(client, merchant_setup):
    user_headers, order_panel_headers, merchant_details, payment_point_id = merchant_setup

    merchant_id = merchant_details["merchant_id"]
    merchant_code = merchant_details["merchant_code"]

    payload = {
        "merchant_id": merchant_id,
        "after_id": None,
        "before_id": None,
        "from_timestamp": None,
        "to_timestamp": None,
        "branch_id_list": [],
        "brand_id_list": [],
        "marketplace_id_list": [],
        "facility_id_list": [],
        "fulfillment_type_id_list": [],
        "order_status_list": ['dispatched'],
        "page_size": 2,
        "page_number": 1,
        "sort_by_list": [],
    }
    response = test_customer_order.do_get_customer_order_history(client, user_headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    customer_order_list = j["data"]["customer_order_list"]
    customer_order_id_list = [customer_order["customer_order_id"] for customer_order in customer_order_list]

    payload = {
        "customer_order_id_list": customer_order_id_list
    }
    response = test_enterprise_back_office.do_get_customer_order_posting(client, user_headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'customer_order_posting'

def test_e2e_edit_customer_order_flow(client, merchant_setup):
    user_headers, order_panel_headers, merchant_code, payment_point_id = merchant_setup

    """
    Correct POS customer orders which should be verified before punching
    """
    
    print("\n")
    one_test_file = "tests/testdata/customer_orders/pos/09_all_item_types_dine_in_pay_later.json"
    
    with open(one_test_file, encoding='utf-8') as f:
        transaction_payload = json.load(f)
        transaction_payload["merchant_code"] = merchant_code

    if "payment_point" in one_test_file:
        transaction_payload["payment_point_id"] = payment_point_id

    payable_amount = transaction_payload["payment_details"]["payable_amount"]
    discount_amount = transaction_payload["payment_details"]["discount_amount"]
    tax_amount = transaction_payload["payment_details"]["tax_amount"]
    tip_amount = transaction_payload["payment_details"]["tip_amount"]

    print(f"Running edit order tests with file {one_test_file}")

    """
    Get calculated values for the order payload
    """
    response = test_customer_order.do_calculate_order(client, order_panel_headers, transaction_payload)    
    j = json.loads(response.data)
    assert j["status"] == 'successful'

    response = test_customer_order.do_create_customer_order(client, order_panel_headers, transaction_payload)    
    j = json.loads(response.data)
    assert j["status"] == 'successful'

    customer_order_id = j["customer_order_id"]

    """
    Get customer order details
    """
    # for edit order, do not consolidate items
    consolidate_items_p = 0
    response = test_customer_order.do_get_customer_order(client, order_panel_headers, customer_order_id, consolidate_items_p)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_customer_order'

    assert j["data"]["payable_amount"] == payable_amount, f"payable_amount should be {payable_amount}. Currently it is {j['data']['payable_amount']}"
    assert j["data"]["discount_amount"] == discount_amount, f"discount_amount should be {discount_amount}. Currently it is {j['data']['discount_amount']}"
    assert j["data"]["tax_amount"] == tax_amount, f"tax_amount should be {tax_amount}. Currently it is {j['data']['tax_amount']}"
    assert j["data"]["tip_amount"] == tip_amount, f"tip_amount should be {tip_amount}. Currently it is {j['data']['tip_amount']}"

    order_line_item_count = 0
    for one_line_item in j["data"]["item_list"]:
        order_line_item_count += one_line_item["quantity"]

    """
    Create edit order payload from customer order details
    """
    revised_order_payload = create_edit_order_payload(j["data"])

    # print(json.dumps(revised_order_payload, indent=4, default=str))

    """
    TEST CASE 1: Remove one item from the order
    """
    print("Running test case 1: Remove one item from the order")

    revised_order_payload["item_list"][0]["edit_status"] = "deleted"
    revised_order_payload["item_list"][0]["quantity"] = 0
    revised_order_line_item_count = order_line_item_count - 1

    revised_order_payload["payment_details"]["edit_status"] = "updated"
    item_price = revised_order_payload["item_list"][0]["price"]
    payable_amount = revised_order_payload["payment_details"]["payable_amount"]
    revised_payable_amount = payable_amount - item_price
    revised_tax_amount = jqutils.round_half_up(revised_payable_amount - (revised_payable_amount / 1.05), 2)

    revised_order_payload["payment_details"]["payable_amount"] = revised_payable_amount
    revised_order_payload["payment_details"]["tax_amount"] = revised_tax_amount

    # print(json.dumps(revised_order_payload, indent=4, default=str))

    """
    Get calculated values for the revised order payload
    """
    response = test_customer_order.do_calculate_order(client, order_panel_headers, revised_order_payload)    
    j = json.loads(response.data)
    assert j["status"] == 'successful'

    """
    Edit customer order via the revised order payload
    """
    response = test_customer_order.do_edit_customer_order(client, order_panel_headers, revised_order_payload, customer_order_id)    
    j = json.loads(response.data)
    assert j["status"] == 'successful'

    """
    Get customer order details
    """
    response = test_customer_order.do_get_customer_order(client, order_panel_headers, customer_order_id, consolidate_items_p)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_customer_order'

    assert j["data"]["payable_amount"] == revised_payable_amount, f"payable_amount should be {revised_payable_amount}. Currently it is {j['data']['payable_amount']}"
    assert j["data"]["tax_amount"] == revised_tax_amount, f"tax_amount should be {revised_tax_amount}. Currently it is {j['data']['tax_amount']}"

    order_line_item_count = 0
    for one_line_item in j["data"]["item_list"]:
        order_line_item_count += one_line_item["quantity"]
    
    assert order_line_item_count == revised_order_line_item_count, f"order_line_item_count should be {revised_order_line_item_count}. Currently it is {order_line_item_count}"

    """
    Create edit order payload from customer order details
    """
    revised_order_payload = create_edit_order_payload(j["data"])

    """
    TEST CASE 2: Increase quantity for one item
    """
    print("Running test case 2: Increase quantity for one item")

    revised_order_payload["item_list"][0]["edit_status"] = "updated"
    revised_order_payload["item_list"][0]["quantity"] = revised_order_payload["item_list"][0]["quantity"] + 1
    revised_order_line_item_count = order_line_item_count + 1

    revised_order_payload["payment_details"]["edit_status"] = "updated"
    item_price = revised_order_payload["item_list"][0]["price"]
    payable_amount = revised_order_payload["payment_details"]["payable_amount"]
    revised_payable_amount = payable_amount + item_price
    revised_tax_amount = jqutils.round_half_up(revised_payable_amount - (revised_payable_amount / 1.05), 2)

    revised_order_payload["payment_details"]["payable_amount"] = revised_payable_amount
    revised_order_payload["payment_details"]["tax_amount"] = revised_tax_amount

    # print(json.dumps(revised_order_payload, indent=4, default=str))

    """
    Get calculated values for the revised order payload
    """
    response = test_customer_order.do_calculate_order(client, order_panel_headers, revised_order_payload)    
    j = json.loads(response.data)
    assert j["status"] == 'successful'

    """
    Edit customer order via the revised order payload
    """
    response = test_customer_order.do_edit_customer_order(client, order_panel_headers, revised_order_payload, customer_order_id)    
    j = json.loads(response.data)
    assert j["status"] == 'successful'

    """
    Get customer order details
    """
    response = test_customer_order.do_get_customer_order(client, order_panel_headers, customer_order_id, consolidate_items_p)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_customer_order'

    assert j["data"]["payable_amount"] == revised_payable_amount, f"payable_amount should be {revised_payable_amount}. Currently it is {j['data']['payable_amount']}"
    assert j["data"]["tax_amount"] == revised_tax_amount, f"tax_amount should be {revised_tax_amount}. Currently it is {j['data']['tax_amount']}"

    order_line_item_count = 0
    for one_line_item in j["data"]["item_list"]:
        order_line_item_count += one_line_item["quantity"]
    
    assert order_line_item_count == revised_order_line_item_count, f"order_line_item_count should be {revised_order_line_item_count}. Currently it is {order_line_item_count}"

    """
    Create edit order payload from customer order details
    """
    revised_order_payload = create_edit_order_payload(j["data"])

    # """
    # Update customer order status to dispatched
    # """
    # payload = {
    #     "customer_order_id": customer_order_id,
    #     "order_status": "dispatched",
    #     "action_timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # }
    # response = test_customer_order.do_update_customer_order(client, order_panel_headers, payload)
    # assert response.status_code == 200
    # j = json.loads(response.data)
    # assert j["status"] == 'successful'

    # """
    # Get all customer orders
    # """
    # payload = {}
    # response = test_customer_order.do_get_customer_orders(client, order_panel_headers, payload)
    # assert response.status_code == 200
    # j = json.loads(response.data)
    # assert j["status"] == 'successful'
    # assert len(j["data"]) > 0
    # assert j["action"] == 'get_customer_orders'

    # """
    # Update customer order status to accepted
    # """
    # payload = {
    #     "customer_order_id": customer_order_id,
    #     "order_status": "accepted",
    #     "action_timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # }
    # response = test_customer_order.do_update_customer_order(client, order_panel_headers, payload)
    # assert response.status_code == 200
    # j = json.loads(response.data)
    # assert j["status"] == 'successful'

    # db_engine = jqutils.get_db_engine()
    # query = text("""
    #     SELECT order_status
    #     FROM customer_order
    #     WHERE customer_order_id = :customer_order_id
    #     AND meta_status = :meta_status
    # """)
    # with db_engine.connect() as conn:
    #     result = conn.execute(query, customer_order_id=customer_order_id, meta_status='active').fetchone()
    #     assert result, "customer order status not updated"

    # """
    # Get customer orders with accepted and created statuses
    # """
    # payload = {
    #     "order_status": ["accepted", "created"]
    # }
    # response = test_customer_order.do_get_customer_orders(client, order_panel_headers, payload)
    # assert response.status_code == 200
    # j = json.loads(response.data)
    # assert j["status"] == 'successful'
    # assert len(j["data"]) > 0
    # assert j["action"] == 'get_customer_orders'

    # """
    # Reprint customer order receipt
    # """
    # payload = {
    #     "customer_order_id": 17
    # }
    # response = test_customer_order.do_print_customer_order_receipt(client, order_panel_headers, payload)
    # assert response.status_code == 200
    # j = json.loads(response.data)
    # assert j["status"] == 'successful'
    # assert j["action"] == 'print_customer_order_receipt'
    
    # """
    # Cancel a customer order
    # """
    # payload = {
    #     "cancellation_reason_id": 1,
    #     "cancellation_reason_note": None,
    # }
    # response = test_customer_order.do_cancel_customer_order(client, order_panel_headers, customer_order_id, payload)
    # assert response.status_code == 200
    # j = json.loads(response.data)
    # assert j["status"] == 'successful'
    # assert j["action"] == 'cancel_customer_order'

    # # validate that cancellation happened both on customer order and merchant transaction
    # query = text("""
    #     SELECT co.order_status, co.cancellation_reason_id, co.cancellation_reason_note, co.merchant_transaction_id, mt.transaction_status,
    #     mt.cancellation_reason_id as mt_cancellation_reason_id, mt.cancellation_reason_note as mt_cancellation_reason_note, co.order_cancelled_timestamp
    #     FROM customer_order co
    #     JOIN merchant_transaction mt ON mt.merchant_transaction_id = co.merchant_transaction_id
    #     WHERE co.customer_order_id = :customer_order_id
    #     AND co.meta_status = :meta_status
    # """)
    # with db_engine.connect() as conn:
    #     result = conn.execute(query, customer_order_id=customer_order_id, meta_status='active').fetchone()
    #     assert result, "customer order status not updated"
    
    # order_status = result["order_status"]
    # cancellation_reason_id = result["cancellation_reason_id"]
    # cancellation_reason_note = result["cancellation_reason_note"]
    # merchant_transaction_id = result["merchant_transaction_id"]
    # transaction_status = result["transaction_status"]
    # mt_cancellation_reason_id = result["mt_cancellation_reason_id"]
    # mt_cancellation_reason_note = result["mt_cancellation_reason_note"]
    # order_cancelled_timestamp = result["order_cancelled_timestamp"]

    # assert order_status == "cancelled"
    # assert cancellation_reason_id == 1
    # assert cancellation_reason_note == None
    # assert merchant_transaction_id
    # assert transaction_status == "cancelled"
    # assert mt_cancellation_reason_id == 1
    # assert mt_cancellation_reason_note == None
    # assert order_cancelled_timestamp

# ----------------------------------------------------------------------------------------------------------------------------------

def create_edit_order_payload(order_details):

    edit_order_payload = {
        "version": "0.1",
        "test_p": 0,
        "external_order_reference_nr": order_details["external_order_reference_nr"],
        "order_placement_channel_id": order_details["order_placement_channel_id"],
        "order_notes": order_details["order_notes"],
        "payment_point_id": order_details["payment_point"]["payment_point_id"],
        "dining_table_id": order_details["dining_table"]["dining_table_id"],
        "edit_status": None,
        "payment_details": {
            "edit_status": None,
            "payable_amount": order_details["payable_amount"],
            "paid_amount": order_details["paid_amount"],
            "tip_amount": order_details["tip_amount"],
            "discount_amount": order_details["discount_amount"],
            "tax_amount": order_details["tax_amount"],
            "currency_name": order_details["payable_currency_name"],
            "payment_method_name": order_details["payment_method_name"],
            "payment_method_type": order_details["payment_method_type"],
        },
        "integration_details": {
            "edit_status": None,
            "branch_id": order_details["branch_id"],
            "brand_id": order_details["brand_id"],
            "facility_id": order_details["facility_id"],
            "marketplace_id": order_details["marketplace_id"],
            "fulfillment_type": order_details["fulfillment_type_name"],
        },
        "customer_details": {
            "edit_status": None,
            "external_customer_id": None,
            "first_name_en": order_details["customer_details"]["anonymous_customer_name"] if order_details["customer_details"]["anonymous_customer_p"] == 1 else order_details["customer_details"]["customer_first_name"],
            "last_name_en": None if order_details["customer_details"]["anonymous_customer_p"] == 1 else order_details["customer_details"]["customer_last_name"],
            "email": order_details["customer_details"]["temp_email"] if order_details["customer_details"]["anonymous_customer_p"] == 1 else order_details["customer_details"]["customer_email"],
            "phone_nr": order_details["customer_details"]["temp_phone_nr"] if order_details["customer_details"]["anonymous_customer_p"] == 1 else order_details["customer_details"]["customer_phone_nr"],
            "customer_contact_method": None
        },
        "employee_details": {
            "edit_status": None,
            "external_employee_id": None,
            "first_name_en": None,
            "last_name_en": None,
            "email": None,
            "phone_nr": None
        },
        "item_list": [],
        "offer_list": [],
        "discount_list": []
    }

    for one_item in order_details["item_list"]:
        item = {
            "edit_status": None,
            "order_line_item_id_list": one_item["order_line_item_id_list"],
            "external_item_id": one_item["external_item_id"],
            "display_name_en": one_item["display_name_en"],
            "display_name_ar": one_item["display_name_ar"],
            "price": one_item["price"],
            "quantity": one_item["quantity"],
            "modifier_section_list": []
        }

        for one_modifier_section in one_item["modifier_section_list"]:
            modifier_section = {
                "edit_status": None,
                "order_line_item_modifier_section_id_list": [one_modifier_section["order_line_item_modifier_section_id"]],
                "external_modifier_section_id": one_modifier_section["external_modifier_section_id"],
                "display_section_name_en": one_modifier_section["display_section_name_en"],
                "display_section_name_ar": one_modifier_section["display_section_name_ar"],
                "modifier_choice_list": []
            }

            for one_modifier_choice in one_modifier_section["modifier_choice_list"]:
                modifier_section["modifier_choice_list"].append({
                    "edit_status": None,
                    "order_line_item_modifier_choice_id_list": [one_modifier_choice["order_line_item_modifier_choice_id"]],
                    "external_modifier_choice_id": one_modifier_choice["external_modifier_choice_id"],
                    "display_choice_name_en": one_modifier_choice["display_choice_name_en"],
                    "display_choice_name_ar": one_modifier_choice["display_choice_name_ar"],
                    "price": one_modifier_choice["price"],
                    "quantity": one_modifier_choice["quantity"]
                })
            
            item["modifier_section_list"].append(modifier_section)
        
        edit_order_payload["item_list"].append(item)
    
    for one_discount in order_details["discount_list"]:
        edit_order_payload["discount_list"].append({
            "edit_status": None,
            "discount_id": one_discount["discount_id"],
            "item_id": one_discount["item_id"],
            "percentage_p": one_discount["percentage_p"],
            "discount_value": one_discount["discount_value"],
            "discount_cap_value": one_discount["discount_cap_value"],
            "minimum_order_value": one_discount["minimum_order_value"]
        })
    
    return edit_order_payload

def test_e2e_internal_supplier_request_flow(client, merchant_setup):
    user_headers, order_panel_headers, merchant_details, payment_point_id = merchant_setup
    """
    Test E2E Internal Stock Request Flow
    """
    response = test_facility.do_get_facilities(client, user_headers, "")
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert len(j["data"]) > 0
    assert j["action"] == 'get_facilities'
    
    facility_name = "jvc"

    for facility in j["data"]:
        if facility["facility_name"] == facility_name:
            to_facility_id = facility["facility_id"]
            break
    
    response = test_supplier.do_get_supplier_list(client, user_headers, merchant_details["merchant_id"])
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
    
    response = test_stock_item.do_stock_item_request(client, user_headers, data)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    
    stock_request_code = j["stock_request_code"]
    
    response = test_stock_item.do_get_stock_request(client, user_headers, stock_request_code)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    
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
        result = conn.execute(query, facility_contact_name="OKISH", facility_contact_phone_nr="321-33-212", facility_contact_email="go@gmail.com", facility_trn_id="AAAA-0000", address_line_1="faciliy_123", address_line_2="nowhere", timezone=4, facility_id_list=[4,5,6], meta_status='active').rowcount
        
    # data = {
    #     "stock_request_code": stock_request_code,
    #     "approval_status": "approved",
    #     "approval_notes": "test notes"
    # }
    
    
    # response = test_stock_item.do_stock_request_approval(client, user_headers, data)
    # j = json.loads(response.data)
    # assert j["status"] == 'successful'
    
    data = {
        "stock_request_code": stock_request_code,
        "stock_request_status": "sent",
    }
    
    response = test_stock_item.do_update_stock_request_status(client,user_headers,data)
    
    response = test_stock_item.do_get_stock_request_email(client,user_headers,stock_request_code)
    
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
    
    response = test_stock_item.do_stock_request_send(client,user_headers,data)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    
    #  get flow for dispatching
    
    # get stock requests
    
    data = {
        "facility_id_list": [supplier_facility_id],
        "stock_request_type": "supplier-procurement",
    }
    response = test_stock_item.do_get_stock_requests(client, user_headers, data)
    j = json.loads(response.data)
    assert j["status"] == 'successful'

    response = test_stock_item.do_get_stock_request(client, user_headers, stock_request_code)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    
    # data = {
    #     "stock_request_code": stock_request_code,
    #     "from_facility_id": supplier_facility_id,
    #     "stock_item_list": [
    #         {
    #             "stock_item_id": 1,
    #             "quantity": 10,
    #             "measurement_id": 1,
    #             "supplier_id": supplier_id,
    #             "cost_per_pack": 10.00,
    #             "quantity_per_pack": 10.00,
    #         },
    #         {
    #             "stock_item_id": 2,
    #             "quantity": 20,
    #             "measurement_id": 1,
    #             "supplier_id": supplier_id,
    #             "cost_per_pack": 8.00,
    #             "quantity_per_pack": 5.00,
    #         },
    #         {
    #             "stock_item_id": 3,
    #             "quantity": 30,
    #             "measurement_id": 1,
    #             "supplier_id": supplier_id,
    #             "cost_per_pack": 20.00,
    #             "quantity_per_pack": 15.00,
    #         }
    #     ]
    # }
    
    # response = test_stock_item.do_dispatch_stock_request(client, user_headers, data)
    # j = json.loads(response.data)
    # assert j["status"] == 'successful'
    
    
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
    
    response = test_stock_item.do_stock_item_receiving(client, user_headers, data)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    
    data = {
        "stock_request_code": stock_request_code,
        "stock_request_status": "completed",
    }
    response = test_stock_item.do_update_stock_request_status(client, user_headers, data)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    
    data = {
        "facility_id_list": [to_facility_id],
        "stock_request_type": "supplier-procurement",
    }
    response = test_stock_item.do_get_stock_requests(client, user_headers, data)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    
    status_list = ['completed', 'received']
    stock_request_id_list = [stock_request['stock_request_id'] for stock_request in j['data'] if stock_request['stock_request_status'] in status_list]

    if stock_request_id_list:
        payload = {
            "stock_request_id_list": stock_request_id_list
        }
        response = test_enterprise_back_office.do_get_stock_request_posting(client, user_headers, payload)
        assert response.status_code == 200
        j = json.loads(response.data)
        assert j["status"] == 'successful'
        assert j["action"] == 'get_stock_request_posting'