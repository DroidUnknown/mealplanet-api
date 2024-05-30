import json

from tests import test_user, test_login, test_city, test_country, test_printer, test_facility, test_merchant, test_branch, test_menu, test_item, test_stock_item, test_preparation
from utils import jqutils
from sqlalchemy import text
import random

base_api_url = "/api"

email = "merchant.signup@example.com"
password = "12345678"
marketplace_id = 1 # talabat

def test_e2e_merchant_signup(client):

    # merchant's first signup
    response = test_user.do_email_signup(client, email)

    assert response.status_code == 200
    response_body = json.loads(response.data)

    assert response_body["status"] == "successful"
    signup_request_id = response_body["signup_request_id"]

    # WEIRD CASE - merchant tries signing up again
    response = test_user.do_email_signup(client, email)

    assert response.status_code == 200
    response_body = json.loads(response.data)

    assert response_body["status"] == "successful"
    signup_request_id = response_body["signup_request_id"]

    # merchant is redirected to the /confirm-email/<otp> page on the frontend

    db_engine = jqutils.get_db_engine()

    query = text("""
        SELECT otp, otp_request_count
        FROM one_time_password
        WHERE signup_request_id = :signup_request_id
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, signup_request_id=signup_request_id).fetchone()
        assert result, "OTP not found in DB"

    otp = result["otp"]
    otp_request_count = result["otp_request_count"]
    assert otp_request_count == 2

    # verify email and set password
    data = {
        "contact_method": "email",
        "phone_nr": None,
        "email": email,
        "otp": otp,
        "intent": "merchant_signup",
        "password": password
    }

    response = test_user.do_verify_otp(client, data)
    assert response.status_code == 200

    # login using the new password
    response = test_login.do_login(client, email, password)
    assert response.status_code == 200

    response_body = response.json
    assert response_body["status"] == "successful"
    assert response_body["username"] == email
    assert response_body["role_id"] == 2
    assert response_body["merchant"]["merchant_id"] == None

def test_e2e_merchant_registeration(client):
    
    db_engine = jqutils.get_db_engine()

    # login using the new password
    response = test_login.do_login(client, email, password)
    assert response.status_code == 200

    response_body = response.json
    assert response_body["status"] == "successful"
    assert response_body["username"] == email
    assert response_body["role_id"] == 2
    assert response_body["merchant"]["merchant_id"] == None

    user_id = response.headers["X-User-Id"]
    access_token = response.headers["X-Access-Token"]

    merchant_headers = {
        'X-User-Id': user_id,
        'X-Access-Token': access_token,
        'X-Username': response.json["username"]
    }

    # get current user details
    response = test_user.do_get_current_user(client, access_token, user_id)
    assert response.status_code == 200

    # start merchant signup
    # step 1 - user details
    data = {
        "first_names_en": "John",
        "last_name_en": "Doe",
        "phone_nr": "+1234567890",
        "business_designation": "owner"
    }
    response = test_user.do_update_user_details(client, merchant_headers, user_id, data)
    assert response.status_code == 200
    response_body = response.json

    assert response_body["status"] == "successful"

    # gather city and country lookups
    response = test_city.do_get_cities(client, merchant_headers)
    assert response.status_code == 200
    response_body = response.json
    assert len(response_body['data']) > 0

    response = test_country.do_get_countries(client, merchant_headers)
    assert response.status_code == 200
    response_body = response.json
    assert len(response_body['payload']) > 0

    # step 2 - business details
    data = {
        "brand_name": "burgerland",
        "merchant_name": "John Doe's Store",
        "merchant_address_line_1": "123 Main St",
        "merchant_address_line_2": "Apt 1",
        "area_name": "Downtown",
        "city_id": 1,
        "country_id": 1,
        "facility_name_list": [
            "satwa",
            "al barsha",
        ]
    }
    response = test_user.do_update_merchant_details(client, merchant_headers, user_id, data)
    assert response.status_code == 200
    response_body = response.json

    assert response_body["status"] == "successful"
    merchant_id = response_body["data"]["merchant_id"]

    data = {
        "brand_name": "burgerland",
        "merchant_name": "Doe's Store",
        "merchant_address_line_1": "Main St",
        "merchant_address_line_2": "Apt 2",
        "area_name": "Uptown",
        "city_id": 2,
        "country_id": 1,
        "facility_name_list": [
            "satwa 2",
            "al barsha 2",
        ]
    }
    response = test_user.do_update_merchant_details(client, merchant_headers, user_id, data)
    assert response.status_code == 200
    response_body = response.json

    assert response_body["status"] == "successful"
    assert merchant_id == response_body["data"]["merchant_id"], "Merchant ID changed"
    
    merchant_id = response_body["data"]["merchant_id"]
    merchant_api_key = response_body["data"]["merchant_api_key"]

    merchant_headers["X-Api-Key"] = merchant_api_key

    # get current user details
    response = test_user.do_get_current_user(client, access_token, user_id)
    assert response.status_code == 200

    # step 3 - connect marketplace
    
    # upload order panel credentials
    data = {
        "marketplace_id": marketplace_id,
        "username": "talabat_order_panel_username",
        "password": "talabat_order_panel_password"
    }
    response = test_merchant.do_add_merchant_marketplace_credential(client, merchant_headers, merchant_id, data)
    assert response.status_code == 200

    # step 4 - create branch

    branch = {
        "brand_name": "test brand 1",
        "external_brand_id": "1231512313",
        "facility_name": "al satwa",
        "marketplace_name": "talabat",
        "external_branch_id": "1234567",
        "external_branch_code": "1234512",
        "city_name": "dubai",
        "country_name": "united arab emirates",
        "latitude": 25.000,
        "longitude": 25.0000
    }
    response = test_branch.do_create_branch(client, merchant_headers, branch)
    assert response.status_code == 200

    # validate branch credentials are populated correctly    
    query = text("""
        SELECT branch_id, username, password, external_branch_id
        FROM branch
        WHERE merchant_id = :merchant_id
        AND marketplace_id = :marketplace_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, merchant_id=merchant_id, marketplace_id=marketplace_id, meta_status="active").fetchone()
        assert result, "Branch not found in DB"

        branch_id = result["branch_id"]
        assert result["username"] == data["username"], "invalid username"
        assert result["password"], "password not populated"
        assert result["external_branch_id"] == "1234567", "external_branch_id not populated correctly"

    # get connected branches
    response = test_branch.do_get_branches_by_merchant_id(client, merchant_headers, merchant_id)
    assert response.status_code == 200

    response_body = response.json
    assert response_body["status"] == "successful"
    assert len(response_body["data"]) > 0, "No branches found"

    # step 4A - scrape menu from existing marketplace store

    response = test_branch.do_get_marketplace_menu(client, merchant_headers, branch_id)
    assert response.status_code == 200

    response_body = response.json
    assert response_body["status"] == "successful"

    menu_payload = response_body["data"]
    # print("="*50)
    # print(json.dumps(menu_payload, indent=4))
    # step 4B - upload menu to iblinkx
    response = test_menu.do_upload_brand_menu_items(client, merchant_headers, menu_payload)
    assert response.status_code == 200

    response_body = response.json
    assert response_body["status"] == "successful"

    # step 5 - add printer to facility
    
    # get available printer models
    response = test_printer.do_get_printer_models(client, merchant_headers)
    assert response.status_code == 200

    assert len(response.json["data"]) > 0, "No printer models found"
    printer_model_id = response.json["data"][0]["printer_model_id"]

    # get merchant facilities
    response = test_facility.do_get_facilities(client, merchant_headers, "")
    assert response.status_code == 200

    assert len(response.json["data"]) > 0, "No facilities found"
    facility_id = response.json["data"][0]["facility_id"]

    # add printer to facility
    data = {
        "printer_name": "Test Printer Updated",
        "printer_description": "Test Printer Updated by user",
        "printer_model_id": printer_model_id,
        "printer_ip_address": "192.168.1.1",
        "printer_port_number": 3001
    }
    response = test_printer.do_add_printer_to_facility(client, merchant_headers, facility_id, data)
    assert response.status_code == 200

    # get printers list for merchant
    response = test_printer.do_get_printers_by_merchant_id(client, merchant_headers, merchant_id)
    assert response.status_code == 200

    assert len(response.json["data"]) > 0, "No printers found"

def test_e2e_menu_management(client):
    
    db_engine = jqutils.get_db_engine()

    # login using the new password
    response = test_login.do_login(client, email, password)
    assert response.status_code == 200

    response_body = response.json
    assert response_body["status"] == "successful"
    assert response_body["username"] == email
    assert response_body["role_id"] == 2

    user_id = response.headers["X-User-Id"]
    access_token = response.headers["X-Access-Token"]
    merchant_id = response_body["merchant"]["merchant_id"]

    merchant_headers = {
        'X-User-Id': user_id,
        'X-Access-Token': access_token,
        'X-Username': response.json["username"]
    }

    # get current user details
    response = test_user.do_get_current_user(client, access_token, user_id)
    assert response.status_code == 200

    merchant_api_key = response_body["merchant"]["merchant_api_key"]
    merchant_headers["X-Api-Key"] = merchant_api_key

    # add a new menu
    data = {
        "merchant_id": merchant_id,
        "menu_name": "christmas menu",
        "menu_description": "christmas menu description"
    }
    response = test_menu.do_add_menu(client, merchant_headers, data)
    assert response.status_code == 200

    response_body = response.json
    assert response_body["status"] == "successful"
    menu_id = response_body["menu_id"]

    # get menu details
    response = test_menu.do_get_menu(client, merchant_headers, menu_id)
    assert response.status_code == 200

    response_body = response.json
    assert response_body["status"] == "successful"

    # get all branches
    response = test_branch.do_get_branches_by_merchant_id(client, merchant_headers, merchant_id)
    assert response.status_code == 200

    response_body = response.json
    assert response_body["status"] == "successful"
    assert len(response_body["data"]) > 0, "No branches found"

    branch_id = response_body["data"][0]["branch_id"]
    brand_id = response_body["data"][0]["brand_id"]
    facility_id = response_body["data"][0]["facility_id"]
    marketplace_id = response_body["data"][0]["marketplace_id"]

    # attach a menu to a branch
    data = {
        "menu_id": menu_id
    }
    response = test_branch.do_attach_menu_to_branch(client, merchant_headers, branch_id, data)
    assert response.status_code == 200

    response_body = response.json
    assert response_body["status"] == "successful"

    # get menu items for brand
    response = test_item.do_search_items(client, merchant_headers, f"brand_id_list={brand_id}")
    assert response.status_code == 200

    response_body = response.json
    assert response_body["status"] == "successful"
    assert len(response_body["data"]) > 0, "No menu items found"

    # Add a new item category for branch
    data = {
        "branch_id_list": f"{branch_id}",
        "item_category_name_en": "Burgers",
        "item_category_name_ar": "البرغر",
        "sequence_nr": 1
    }
    response = test_branch.do_add_item_category_for_branches(client, merchant_headers, data)
    assert response.status_code == 200

    response_body = response.json
    assert response_body["status"] == "successful"
    item_category_branch_map_id = response_body["item_category_branch_map_id"]
    item_category_id = response_body["item_category_id"]

    # get item_categories for this branch
    response = test_branch.do_get_item_categories_by_branch(client, merchant_headers, branch_id)
    assert response.status_code == 200

    response_body = response.json
    assert response_body["status"] == "successful"

    # Add a new item to this item category
    with open("tests/testdata/menus/item_payloads/sample_item_with_no_modifiers.json", "r") as f:
        item_payload = json.load(f)

        item_payload["branch_id_list"] = [branch_id]
        item_payload["item_category_branch_map_id"] = item_category_branch_map_id
        item_payload["item_category_id"] = item_category_id
        item_payload["item_price_map_list"] = []

        data = {
            'json': json.dumps(item_payload)
        }

        # add new item
        response = test_item.do_add_item(client, merchant_headers, data)
        assert response.status_code == 200

        response_body = response.json
        assert response_body["status"] == "successful"
        item_id = response_body["item_id"]

    # get menu item details
    response = test_item.do_get_item(client, merchant_headers, item_id)
    assert response.status_code == 200

    response_body = response.json
    assert response_body["status"] == "successful"
    
    # get menu items for brand
    response = test_item.do_search_items(client, merchant_headers, f"brand_id={brand_id}")
    assert response.status_code == 200

    response_body = response.json
    assert response_body["status"] == "successful"
    assert len(response_body["data"]) > 0, "No menu items found"

    menu_item_list = []
    for one_menu_item in response_body["data"]:
        menu_item_list.append({
            "display_name_en": one_menu_item["display_name_en"],
            "item_category_name_en": one_menu_item["item_category"]["item_category_name_en"],
            "item_category_branch_map_id": one_menu_item["item_category_branch_map_id"],
            "sequence_nr": one_menu_item["sequence_nr"],
        })

def test_e2e_recipes(client):
    # login using the new password
    response = test_login.do_login(client, email, password)
    assert response.status_code == 200

    response_body = response.json
    assert response_body["status"] == "successful"
    assert response_body["username"] == email
    assert response_body["role_id"] == 2

    user_id = response.headers["X-User-Id"]
    access_token = response.headers["X-Access-Token"]
    merchant_id = response_body["merchant"]["merchant_id"]

    merchant_headers = {
        'X-User-Id': user_id,
        'X-Access-Token': access_token,
        'X-Username': response.json["username"]
    }

    # get current user details
    response = test_user.do_get_current_user(client, access_token, user_id)
    assert response.status_code == 200

    merchant_api_key = response_body["merchant"]["merchant_api_key"]
    merchant_headers["X-Api-Key"] = merchant_api_key

    # get all branches
    response = test_branch.do_get_branches_by_merchant_id(client, merchant_headers, merchant_id)
    assert response.status_code == 200

    response_body = response.json
    assert response_body["status"] == "successful"
    assert len(response_body["data"]) > 0, "No branches found"

    branch_id = response_body["data"][0]["branch_id"]
    brand_id = response_body["data"][0]["brand_id"]
    facility_id = response_body["data"][0]["facility_id"]
    marketplace_id = response_body["data"][0]["marketplace_id"]

    response = test_item.do_search_items(client, merchant_headers, f"brand_id_list={brand_id}")
    assert response.status_code == 200

    response_body = response.json
    assert response_body["status"] == "successful"
    item_list = response_body["data"]
    assert len(item_list) > 0, "No menu items found"

    stock_item_list = [
        {
            "stock_item_name_en": "white dough",
            "stock_item_description_en": "white dough",
            "default_supplier_id": None,
            "parent_stock_item_id": None,
            "stock_category_id": 1,
            "measurement_id": 3
        },
        {
            "stock_item_name_en": "olive oil",
            "stock_item_description_en": "olive oil",
            "default_supplier_id": None,
            "parent_stock_item_id": None,
            "stock_category_id": 1,
            "measurement_id": 3
        },
        {
            "stock_item_name_en": "akkawi cheese",
            "stock_item_description_en": "akkawi cheese",
            "default_supplier_id": None,
            "parent_stock_item_id": None,
            "stock_category_id": 1,
            "measurement_id": 3
        },
        {
            "stock_item_name_en": "mayo sauce",
            "stock_item_description_en": "mayo sauce",
            "default_supplier_id": None,
            "parent_stock_item_id": None,
            "stock_category_id": 1,
            "measurement_id": 3
        },
        {
            "stock_item_name_en": "garlic sauce",
            "stock_item_description_en": "garlic sauce",
            "default_supplier_id": None,
            "parent_stock_item_id": None,
            "stock_category_id": 1,
            "measurement_id": 3
        },
        {
            "stock_item_name_en": "garlic",
            "stock_item_description_en": "garlic",
            "default_supplier_id": None,
            "parent_stock_item_id": None,
            "stock_category_id": 1,
            "measurement_id": 3
        },
        {
            "stock_item_name_en": "onion",
            "stock_item_description_en": "onion",
            "default_supplier_id": None,
            "parent_stock_item_id": None,
            "stock_category_id": 1,
            "measurement_id": 3
        },
        {
            "stock_item_name_en": "tomato",
            "stock_item_description_en": "tomato",
            "default_supplier_id": None,
            "parent_stock_item_id": None,
            "stock_category_id": 1,
            "measurement_id": 3
        },
        {
            "stock_item_name_en": "tomato sauce",
            "stock_item_description_en": "tomato sauce",
            "default_supplier_id": None,
            "parent_stock_item_id": None,
            "stock_category_id": 1,
            "measurement_id": 3
        }
    ]

    payload = {
        "stock_item_list": stock_item_list
    }

    response = test_stock_item.do_bulk_upload_stock_item(client, merchant_headers, payload)
    assert response.status_code == 200
    response_body = response.json
    assert response_body["status"] == "successful"
    assert response_body["action"] == "bulk_upload_stock_item"
    stock_item_id_list = response_body["stock_item_id_list"]
    assert len(stock_item_id_list) == len(stock_item_list)

    for i in range(len(stock_item_list)):
        stock_item_list[i]["stock_item_id"] = stock_item_id_list[i]

    for one_item in item_list:
        item_id = one_item["item_id"]
        # choose random number between 1 to 4
        random_stock_item_count = random.randint(2, 3)
        input_stock_list = random.sample(stock_item_list, random_stock_item_count)
        
        preparation_input_list = []
        for one_stock in input_stock_list:
            preparation_input_list.append({
                "input_type": "stock-item",
                "item_id": None,
                "stock_item_id": one_stock["stock_item_id"],
                "quantity": 10,
                "measurement_id": 3,
                "waste_value": 20,
                "waste_percentage_p": 1,
                "waste_measurement_id": None,
            })

        preparation_payload = {
            "item_id": item_id,
            "stock_item_id": None,
            "quantity": 1,
            "measurement_id": 4,
            "brand_id":None,
            "preparation_name": one_item["display_name_en"],
            "preparation_description_en": f"prepare {one_item['display_name_en']}",
            "preparation_description_ar": "",
            "min_benchmark_time_to_complete": 5,
            "max_benchmark_time_to_complete": 10,
            "benchmark_time_measurement_id": 13,
            "complexity_level": "medium",
            "critical_points": 1,
            "preparation_input_list": preparation_input_list,
            "preparation_output_list": [{
                "output_type": "stock-item",
                "item_id": item_id,
                "quantity": 1,
                "measurement_id": 4
            }]
        }

        test_preparation.do_create_preparation(client, merchant_headers, preparation_payload)

    # get all preparations
    response = test_preparation.do_get_preparations(client, merchant_headers)
    assert response.status_code == 200
    response_body = response.json
    assert response_body["status"] == "successful"
    assert len(response_body["data"]) > 0, "No preparations found"