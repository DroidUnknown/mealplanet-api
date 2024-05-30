import json
import pytest

from tests import test_user, test_branch, test_merchant, test_menu, test_customer_order, test_discount, test_facility, test_customer, test_customer_address, test_feature, test_loyalty_program
from utils import jqutils
from loyalty_program_management import loyalty_program_ninja

# ------------- Fixtures -------------

@pytest.fixture(scope="module", autouse=True)
def merchant(client):
    
    """
    Create New Merchant (Normal)
    """
    logged_in_user_details, merchant_settings, logged_in_order_panel_details, logged_in_marketplace_details = test_merchant.do_add_merchant_and_user(client, create_order_panel_user=True, create_marketplace_user=False)

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

    merchant_settings["merchant_code"] = jqutils.get_column_by_id(str(merchant_settings["merchant_id"]), "merchant_code", "merchant")

    """
    Enable Loyalty Program Feature
    """
    payload = {
        "merchant_id": merchant_settings["merchant_id"],
        "feature_list": [{
            "feature_id": 17,
            "enabled_p": 1
        }]
    }
    response = test_feature.do_update_merchant_feature(client, user_headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'

    """
    Configure Loyalty Program Configs
    """
    payload = {
        "currency_id": 1,
        "dine_in_point_bonus": 0,
        "dine_in_point_bonus_percent_p": 0,
        "point_earning_rate": 1,
        "point_redemption_rate": 0.1, 
        "loyalty_point_expiry_duration": None,
        "expiry_duration_measurement_id": None,
    }
    response = test_loyalty_program.do_update_merchant_loyalty_program_config(client, user_headers, merchant_settings["merchant_id"], payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'

    """
    Create MyApp branch
    """
    payload = {
        "brand_name": "test brand 2",
        "facility_name": "test satwa 2",
        "marketplace_name": "myapp",
        "external_brand_id": "tb_123",
        "auto_accept_p": True,
        "city_name": "dubai",
        "country_name": "united arab emirates",
        "latitude": "25.2048",
        "longitude": "55.2708",
        "external_branch_id": None,
        "external_branch_code": None
    }
    response = test_branch.do_create_branch(client, user_headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'create_branch'
    assert j["branch_id"], "branch id not generated"

    branch_id = j["branch_id"]
    brand_id = j["brand_id"]
    facility_id = j["facility_id"]

    """
    Add delivery and takeaway fulfillment types to MyApp branch
    """
    facility_fulfillment_type_map_id_list = []
    payload = {
        "facility_fulfillment_type_list": 
        [
            {
                "facility_id": facility_id,
                "fulfillment_type_id": 2, # marketplace delivery
                "iblinkmarketplace_enabled_p": 1
            },
            {
                "facility_id": facility_id,
                "fulfillment_type_id": 3, # restaurant delivery
                "iblinkmarketplace_enabled_p": 1
            },
            {
                "facility_id": facility_id,
                "fulfillment_type_id": 4, # pickup
                "iblinkmarketplace_enabled_p": 1
            }
        ]
    }
    response = test_facility.do_add_facility_fulfillment_type_map(client, user_headers, payload)
    assert response.json['status'] == 'successful'
    j = json.loads(response.data)
    assert j["status"] == 'successful'

    # -----------------------------------------------------------------
    # TO BE USED IF NOT USING THE PRE-LOADED MENU FROM DATA MIGRATION
    # -----------------------------------------------------------------

    with open("tests/testdata/menus/sample_menu.json", encoding='utf-8') as f:
        file_data = json.load(f)
        file_data["brand_id"] = brand_id
        file_data["branch_id"] = branch_id
        test_menu.do_upload_brand_menu_items(client, user_headers, file_data)

    response = test_branch.do_generate_menu(client, user_headers, branch_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'generate_menu'

    # -----------------------------------------------------------------

    yield user_headers, order_panel_headers, merchant_settings

@pytest.fixture(scope="module", autouse=True)
def discount_id(client, merchant):
    merchant_headers, order_panel_headers, merchant_settings = merchant

    """
    Create 30% Discount for MyApp orders
    """
    payload = {
        "discount_name": "30% Off",
        "discount_description": "30% Off",
        "discount_display_name_en": "30% Off",
        "discount_display_name_ar": "30% Off",
        "brand_id": 2,
        "marketplace_id": 9,
        "item_id_list": [],
        "item_category_id_list": [],
        "discount_level": "order-level",
        "auto_apply_p": 0,
        "currency_id": 1,
        "percentage_p": 1,
        "discount_value": 30,
        "discount_cap_value": None,
        "minimum_order_value": 0,
        "maximum_order_value": 1000,
        "facility_fulfillment_type_map_id_list": [],
        "from_time": None,
        "to_time": None,
        "timezone": None,
    }
    response = test_discount.do_add_discount(client, merchant_headers, payload)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    discount_id = j["data"]

    yield discount_id

@pytest.fixture(scope="module", autouse=True)
def customer(client, merchant):
    merchant_headers, order_panel_headers, merchant_settings = merchant

    merchant_code = merchant_settings["merchant_code"]
    
    role_name = "customer"
    phone_nr = "0812345678"
    name = "Customer Joe"
    password = "123456"

    # customer signup and after verification customer is logged in
    user_id, access_token, otp_code = test_user.do_user_signup(client, phone_nr, name, password=password, role_name=role_name, merchant_code=merchant_code)

    # get current user details
    response = test_user.do_get_current_user(client, access_token, user_id)
    assert response.status_code == 200
    response_body = response.json
    assert response_body["status"] == 'successful'
    customer_details = response_body

    """
    Customer request headers
    """
    customer_headers = {
        "X-User-Id": user_id,
        "X-Access-Token": access_token,
        "X-Api-Key": merchant_headers["X-Api-Key"]
    }

    # get customer details
    response = test_customer.do_get_customer(client, customer_headers, customer_details["customer"]["customer_id"])
    assert response.status_code == 200
    response_body = response.json

    yield customer_details, customer_headers

# ------------- Test Cases -------------

customer_order_id_list = []

def test_e2e_myapp_order_flow(client, customer, discount_id):

    customer_details, customer_headers = customer

    customer_id = customer_details["customer"]["customer_id"]
    merchant_id = customer_details["merchant"]["merchant_id"]

    # update customer details
    data = {
        "customer_code": customer_details["customer"]["customer_code"],
        "stripe_customer_id": None,
        "merchant_id": merchant_id,
        "customer_first_name": customer_details["user"]["first_names_en"],
        "customer_last_name": customer_details["user"]["last_name_en"],
        "customer_email": "joe@gmail.com",
        "customer_phone_nr": customer_details["user"]["phone_nr"],
        "customer_remote_id" : None,
        "customer_gender": "male",
        "customer_dob": "2020-01-01"
    }
    response = test_customer.do_update_customer(client, customer_headers, data, customer_id)
    assert response.status_code == 200

    # verify updated customer details
    response = test_customer.do_get_customer(client, customer_headers, customer_id)
    assert response.status_code == 200
    response_body = response.json
    assert response_body["data"]["customer_email"] == "joe@gmail.com"

    # add customer address
    data = {
        "customer_id": customer_id,
        "address_line_1": "test address line 1",
        "address_line_2": "test address line 2",
        "city_id": 1,
        "latitude": "25.2048",
        "longitude": "55.2708",
        "delivery_instructions": "test address",
        "address_type_id": 1 # home
    }
    response = test_customer_address.do_add_customer_address(client, customer_headers, data)
    assert response.status_code == 200
    response_body = response.json
    assert response_body["status"] == 'successful'
    assert response_body["action"] == 'add_customer_address'
    assert response_body["customer_address_id"], "customer address id not generated"

    # get customer address
    response = test_customer_address.do_get_customer_address(client, customer_headers, response_body["customer_address_id"])
    assert response.status_code == 200
    customer_address = response.json
    assert customer_address["customer_id"] == customer_id
    assert customer_address["address_line_1"] == "test address line 1"
    assert customer_address["address_line_2"] == "test address line 2"
    assert customer_address["city_id"] == 1
    assert customer_address["latitude"] == "25.2048"
    assert customer_address["longitude"] == "55.2708"
    assert customer_address["delivery_instructions"] == "test address"
    assert customer_address["address_type_id"] == 1 # home

    # get merchant branches by merchant id
    response = test_branch.do_get_branches_by_merchant_id(client, customer_headers, merchant_id)
    assert response.status_code == 200
    response_body = response.json
    branch_list = response_body["data"]
    assert len(branch_list) > 0, "no branches found"

    branch_id = None
    for one_branch in branch_list:
        if one_branch["marketplace_name"] == "myapp":
            branch_id = one_branch["branch_id"]
            break
    assert branch_id, "no myapp branch found for merchant"

    # get branch menu
    response = test_branch.do_get_branch_menu(client, customer_headers, branch_id)
    assert response.status_code == 200

    response_body = response.json
    assert len(response_body["data"]) > 0, "no menu items found"

    branch_item_category_list = response_body["data"]
    branch_item_list = []
    for one_branch_item_category in branch_item_category_list:
        branch_item_list.extend(one_branch_item_category["menu_items"])

    # get MyApp enabled branches and current distance from customer
    payload = {
        "latitude": "25.2048",
        "longitude": "55.2708",
    }
    response = test_merchant.do_get_myapp_branches(client, customer_headers, merchant_id, payload)
    assert response.status_code == 200

    response_body = response.json
    assert len(response_body["data"]) > 0, "no branches found"

    # select the closest branch to place the order to based on distance
    branch_list = response_body["data"]
    branch_id = branch_list[0]["branch_id"]
    brand_id = branch_list[0]["brand"]["brand_id"]
    facility_id = branch_list[0]["facility"]["facility_id"]
    marketplace_id = branch_list[0]["marketplace"]["marketplace_id"]

    """
    Correct MyApp customer orders for punching
    """
    test_file_list = []
    test_file_list.append("tests/testdata/customer_orders/myapp/01_menu_items_only.json")
    test_file_list.append("tests/testdata/customer_orders/myapp/02_menu_items_with_modifiers.json")
    test_file_list.append("tests/testdata/customer_orders/myapp/03_all_item_types.json")
    test_file_list.append("tests/testdata/customer_orders/myapp/04_all_item_types_with_pre_made_discount.json")
    test_file_list.append("tests/testdata/customer_orders/myapp/05_all_item_types_pickup_order.json")
    test_file_list.append("tests/testdata/customer_orders/myapp/06_all_item_types_redeem_loyalty_points.json")

    for idx, one_test_file in enumerate(test_file_list):
        with open(one_test_file, encoding='utf-8') as f:
            transaction_payload = json.load(f)

            # set integration details
            transaction_payload["customer_details"] = {
                "customer_id": customer_id
            }
            transaction_payload["merchant_code"] = customer_details["merchant"]["merchant_code"]
            transaction_payload["integration_details"]["branch_id"] = branch_id
            transaction_payload["integration_details"]["brand_id"] = brand_id
            transaction_payload["integration_details"]["facility_id"] = facility_id
            transaction_payload["integration_details"]["marketplace_id"] = marketplace_id

            # update external item ids for menu items
            transaction_payload["item_list"] = update_external_item_ids(transaction_payload["item_list"], branch_item_list)

            # update discount_id for discount if exists
            if one_test_file.endswith("04_all_item_types_with_pre_made_discount.json"):
                for one_discount in transaction_payload["discount_list"]:
                    one_discount["discount_id"] = discount_id

            payable_amount = transaction_payload["payment_details"]["payable_amount"]
            discount_amount = transaction_payload["payment_details"]["discount_amount"]
            tax_amount = transaction_payload["payment_details"]["tax_amount"]
            tip_amount = transaction_payload["payment_details"]["tip_amount"]
        
        print(f"Running test case {idx+1} with file {one_test_file}")

        response = test_customer_order.do_calculate_order(client, customer_headers, transaction_payload)    
        j = json.loads(response.data)
        assert j["status"] == 'successful'

        response = test_customer_order.do_create_customer_order(client, customer_headers, transaction_payload)    
        j = json.loads(response.data)
        assert j["status"] == 'successful'

        customer_order_id = j["customer_order_id"]
        customer_order_id_list.append(customer_order_id)

def test_e2e_loyalty_points(client, customer, merchant):

    merchant_headers, order_panel_headers, merchant_settings = merchant
    customer_details, customer_headers = customer
    
    customer_id = customer_details["customer"]["customer_id"]
    creation_user_id = customer_details["user"]["user_id"]
    merchant_id = customer_details["merchant"]["merchant_id"]
    currency_id = customer_details["merchant"]["default_currency"]["currency_id"]

    customer_order_id = customer_order_id_list[0]

    customer_detail = {
        "merchant_id": merchant_id,
        "customer_id": customer_id,
        "currency_id": currency_id,
    }

    loyalty_point_config = loyalty_program_ninja.get_loyalty_program_config(merchant_id, currency_id)
    point_earning_rate = float(loyalty_point_config["point_earning_rate"])
    point_redemption_rate = float(loyalty_point_config["point_redemption_rate"])
    
    loyalty_point_balance_list = loyalty_program_ninja.get_loyalty_point_balance(merchant_id, [customer_id], currency_id)
    expected_loyalty_point_balance = loyalty_point_balance_list[0]["total_loyalty_point_value"]

    money_spent = 10 # AED
    redeemed_loyalty_points = 10
    expected_loyalty_point_balance += ( money_spent - redeemed_loyalty_points )
    expectation = {
        "total_loyalty_point_value": expected_loyalty_point_balance,
        "equivalent_monetary_value": expected_loyalty_point_balance * point_redemption_rate
    }

    earned_loyalty_points = loyalty_program_ninja.earn_loyalty_points(merchant_id, customer_id, customer_order_id, money_spent, currency_id, creation_user_id)
    assert earned_loyalty_points == (money_spent * point_earning_rate), "equivalent money earned is not correct"
    redeemed_p, redemption_details = loyalty_program_ninja.redeem_loyalty_points(merchant_id, customer_id, redeemed_loyalty_points, currency_id, creation_user_id=creation_user_id)
    assert redeemed_p, redemption_details
    assert redemption_details["earned_monetary_value"] == jqutils.round_half_up(redeemed_loyalty_points * point_redemption_rate, 2), "redeemed loyalty points is not correct"
    validate_loyalty_point_balance(customer_detail, expectation)

    money_spent = 15 # AED
    redeemed_loyalty_points = 10
    expected_loyalty_point_balance += ( money_spent - redeemed_loyalty_points )
    expectation = {
        "total_loyalty_point_value": expected_loyalty_point_balance,
        "equivalent_monetary_value": expected_loyalty_point_balance * point_redemption_rate
    }

    earned_loyalty_points = loyalty_program_ninja.earn_loyalty_points(merchant_id, customer_id, customer_order_id, money_spent, currency_id, creation_user_id)
    assert earned_loyalty_points == (money_spent * point_earning_rate), "equivalent money earned is not correct"
    redeemed_p, redemption_details = loyalty_program_ninja.redeem_loyalty_points(merchant_id, customer_id, redeemed_loyalty_points, currency_id, creation_user_id=creation_user_id)
    assert redeemed_p, redemption_details
    assert redemption_details["earned_monetary_value"] == jqutils.round_half_up(redeemed_loyalty_points * point_redemption_rate, 2), "redeemed loyalty points is not correct"
    validate_loyalty_point_balance(customer_detail, expectation)

    money_spent = 15 # AED
    redeemed_loyalty_points = 7
    expected_loyalty_point_balance += ( money_spent - redeemed_loyalty_points )
    expectation = {
        "total_loyalty_point_value": expected_loyalty_point_balance,
        "equivalent_monetary_value": expected_loyalty_point_balance * point_redemption_rate
    }
    
    earned_loyalty_points = loyalty_program_ninja.earn_loyalty_points(merchant_id, customer_id, customer_order_id, money_spent, currency_id, creation_user_id)
    assert earned_loyalty_points == (money_spent * point_earning_rate), "equivalent money earned is not correct"
    redeemed_p, redemption_details = loyalty_program_ninja.redeem_loyalty_points(merchant_id, customer_id, redeemed_loyalty_points, currency_id, creation_user_id=creation_user_id)
    assert redeemed_p, redemption_details
    assert redemption_details["earned_monetary_value"] == jqutils.round_half_up(redeemed_loyalty_points * point_redemption_rate, 2), "redeemed loyalty points is not correct"
    validate_loyalty_point_balance(customer_detail, expectation)

    money_spent = 5 # AED
    redeemed_loyalty_points = 18
    expected_loyalty_point_balance += ( money_spent - redeemed_loyalty_points )
    expectation = {
        "total_loyalty_point_value": expected_loyalty_point_balance,
        "equivalent_monetary_value": expected_loyalty_point_balance * point_redemption_rate
    }

    earned_loyalty_points = loyalty_program_ninja.earn_loyalty_points(merchant_id, customer_id, customer_order_id, money_spent, currency_id, creation_user_id)
    assert earned_loyalty_points == (money_spent * point_earning_rate), "equivalent money earned is not correct"
    redeemed_p, redemption_details = loyalty_program_ninja.redeem_loyalty_points(merchant_id, customer_id, redeemed_loyalty_points, currency_id, creation_user_id=creation_user_id)
    assert redeemed_p, redemption_details
    assert redemption_details["earned_monetary_value"] == jqutils.round_half_up(redeemed_loyalty_points * point_redemption_rate, 2), "redeemed loyalty points is not correct"
    validate_loyalty_point_balance(customer_detail, expectation)

    response = test_loyalty_program.do_get_customer_loyalty_point_balance(client, customer_headers, customer_id)
    assert response.status_code == 200
    response_body = response.json
    assert response_body["status"] == 'successful'
    assert response_body["data"]["loyalty_point_balance"]["total_loyalty_point_value"] == expected_loyalty_point_balance, "loyalty point balance is not correct"

    response = test_loyalty_program.do_get_customer_loyalty_point_ledger(client, customer_headers, customer_id)
    assert response.status_code == 200
    response_body = response.json
    assert response_body["status"] == 'successful'

    response = test_loyalty_program.do_get_merchant_loyalty_program_config(client, merchant_headers, merchant_id)
    assert response.status_code == 200
    response_body = response.json
    assert response_body["status"] == 'successful'

# ------------- Helper Functions -------------

def update_external_item_ids(item_list, branch_item_list):
    for one_item in item_list:
        for one_branch_item in branch_item_list:
            if one_item["display_name_en"].lower() == one_branch_item["menu_item_name_en"]:
                one_item["external_item_id"] = one_branch_item["menu_item_external_id"]
                break
    
    return item_list

def validate_loyalty_point_balance(customer_detail, expectation):
    merchant_id = customer_detail["merchant_id"]
    customer_id = customer_detail["customer_id"]
    currency_id = customer_detail["currency_id"]

    loyalty_point_balance_list = loyalty_program_ninja.get_loyalty_point_balance(merchant_id, [customer_id], currency_id)
    loyalty_point_balance = loyalty_point_balance_list[0]
    expected_loyalty_point_balance = loyalty_point_balance["total_loyalty_point_value"]
    expected_monetary_value = loyalty_point_balance["equivalent_monetary_value"]