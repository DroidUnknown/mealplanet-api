import json
import pytest
import pandas as pd
import io
import base64
from IPython.display import display

from sqlalchemy import text
from datetime import datetime, timedelta

from tests import test_customer_order, test_discount, test_item, test_wastage_engine, test_stock_item, test_branch, test_menu
from tests.test_merchant import do_add_merchant_and_user, do_get_customer_orders_by_merchant, do_add_merchant_third_party_credential
from tests.test_payment_point_area import do_add_payment_point_area
from tests.test_payment_point import do_add_payment_point
from tests.test_branch import do_create_branch
from tests import test_generative_ai
from utils import jqutils, generative_ai_util
from PIL import Image

base_api_url = "/api"

main_item_id = 129 # potato bun

##############
# TEST-CASE
##############

@pytest.fixture(scope="module", autouse=True)
def merchant_setup(client):
    
    """
    Setup merchant features
    """
    merchant_name = "crazy grill"
    merchant_features = [
        {
            "feature_id": 1, # card-payment
            "enabled": 1
        },
        {
            "feature_id": 14, # iblinkpos
            "enabled": 1
        },
        {
            "feature_id": 20, # financials
            "enabled": 1
        },
        {
            "feature_id": 22, # inventory-tracking
            "enabled": 1
        }
    ]
    
    """
    Create New Merchant (Normal)
    """
    logged_in_user_details, merchant_settings, logged_in_order_panel_details, logged_in_marketplace_details = do_add_merchant_and_user(client, create_order_panel_user=True, create_marketplace_user=False, merchant_features=merchant_features, merchant_name=merchant_name)
    merchant_id = merchant_settings["merchant_id"]

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
        "merchant_id": merchant_id,
        "merchant_name": merchant_settings["merchant_name"],
        "merchant_code": jqutils.get_column_by_id(str(merchant_id), "merchant_code", "merchant"),
    }
    
    """
    Create Merchant Third Party Creds
    """
    payload = {
        "third_party_credential_type": "marketplace-deliveroo",
        "username": "test",
        "password": "test"
    }
    response = do_add_merchant_third_party_credential(client, user_headers, merchant_id, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    merchant_third_party_credential_id = j["merchant_third_party_credential_id"]

    """
    Create Deliveroo integrated branch
    """
    payload = {
        "brand_name": merchant_name,
        "facility_name": "jvc",
        "marketplace_id": None,
        "external_brand_id": None,
        "external_branch_id": None,
        "external_branch_code": None,
        "marketplace_name": "deliveroo",
        "city_name": "dubai",
        "country_name": "united arab emirates",
        "latitude": 25.067566,
        "longitude": 55.153897,
        "merchant_third_party_credential_id": merchant_third_party_credential_id
    }
    response = do_create_branch(client, user_headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'create_branch'
    assert j["branch_id"], "branch id not generated"
    
    deliveroo_branch_details = {
        "brand_id": j["brand_id"],
        "facility_id": j["facility_id"],
        "branch_id": j["branch_id"],
        "marketplace_id": j["marketplace_id"]
    }

    """
    Create pos enabled branch
    """
    payload = {
        "brand_name": merchant_name,
        "facility_name": "jvc",
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

    # -----------------------------------------------------------------
    # TO BE USED IF NOT USING THE PRE-LOADED MENU FROM DATA MIGRATION
    # -----------------------------------------------------------------
    
    with open("tests/testdata/menus/sample_menu.json", encoding='utf-8') as f:
        file_data = json.load(f)
        file_data["brand_id"] = deliveroo_branch_details["brand_id"]
        file_data["facility_id"] = deliveroo_branch_details["facility_id"]
        file_data["marketplace_id"] = deliveroo_branch_details["marketplace_id"]
        file_data["branch_id"] = deliveroo_branch_details["branch_id"]
        
        for one_category in file_data["menu_categories"]:
            for one_sample_item in one_category["menu_items"]:
                if one_sample_item["menu_item_name_en"] == "Potato Bun":
                    one_sample_item["menu_item_price"] = 6
                    break
        
        test_menu.do_upload_brand_menu_items(client, user_headers, file_data)

    # create line item discounts
    payload = {
        "discount_name": "10% Off - potato bun",
        "discount_description": "10% Off - potato bun",
        "discount_display_name_en": "10% Off - potato bun",
        "discount_display_name_ar": "10% Off - potato bun",
        "brand_id": None,
        "marketplace_id": None,
        "item_id_list": [],
        "item_category_id_list": [],
        "discount_level": "order-level",
        "auto_apply_p": 0,
        "currency_id": 1,
        "percentage_p": 0,
        "auto_apply_p": 0,
        "discount_value": 1.4,
        "discount_cap_value": None,
        "minimum_order_value": 0,
        "maximum_order_value": None,
        "from_time": None,
        "to_time": None,
        "timezone": 4,
        "facility_fulfillment_type_map_id_list": []
    }
    response = test_discount.do_add_discount(client, user_headers, payload)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'add_discount'
    
    line_item_discount_id = j["data"]

    # -----------------------------------------------------------------

    yield user_headers, order_panel_headers, merchant_details, deliveroo_branch_details, line_item_discount_id

# ----------------------------------------------------------------------------------------------------------------------------------

def test_e2e_inventory_manifest_flow(client, merchant_setup):
    user_headers, order_panel_headers, merchant_details, deliveroo_branch_details, line_item_discount_id = merchant_setup
    
    # print("adding inventory with expiry timestamps into the system")
    # print("------------------------------------------------------")
    
    payload = {
        "facility_id": deliveroo_branch_details["facility_id"],
        "item_list": [
            {
                "item_id": main_item_id,
                "item_name": "Potato Bun (2 hours) x 5",
                "expiry_timestamp": (datetime.now() + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
                "quantity": 20
            },
            {
                "item_id": main_item_id,
                "item_name": "Potato Bun (8 hours) x 2",
                "expiry_timestamp": (datetime.now() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S"),
                "quantity": 20
            },
            {
                "item_id": main_item_id,
                "item_name": "Potato Bun (9 hours) x 5",
                "expiry_timestamp": (datetime.now() + timedelta(hours=9)).strftime("%Y-%m-%d %H:%M:%S"),
                "quantity": 20
            },
            {
                "item_id": 139,
                "item_name": "Coca Cola (12 hours) x 5",
                "expiry_timestamp": (datetime.now() + timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S"),
                "quantity": 5
            },
            {
                "item_id": 124,
                "item_name": "Coleslaw (12 hours) x 5",
                "expiry_timestamp": (datetime.now() + timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S"),
                "quantity": 5
            },
            {
                "item_id": 101,
                "item_name": "Burger & Brisket duo (14 hours) x 5",
                "expiry_timestamp": (datetime.now() + timedelta(hours=14)).strftime("%Y-%m-%d %H:%M:%S"),
                "quantity": 5
            },
        ]
    }
    # for one_item in payload["item_list"]:
    #     print(one_item["item_name"])
    response = test_item.do_add_item_to_inventory(client, user_headers, payload)
    assert response.status_code == 200
    response_body = json.loads(response.data)
    assert response_body['status'] == "successful"
    assert response_body['action'] == "add_item_to_inventory"
    
    # print("\n")

def test_e2e_wastage_reporting_flow(client, merchant_setup):
    user_headers, order_panel_headers, merchant_details, deliveroo_branch_details, line_item_discount_id = merchant_setup
    
    # print("\n\nadding wastage into the system")
    # print("------------------------------------------------------")
    
    payload = {
        "facility_id": deliveroo_branch_details["facility_id"],
        "stock_wastage_type": "stock_wastage",
        "item_list": [
            {
                "item_id": 129,
                "display_name_en": "Potato Bun: 10 pcs wasted",
                "quantity": 10,
                "wastage_reason_id": 1,
                "comments": ""
            },
        ]
    }
    # for one_item in payload["item_list"]:
    #     print(one_item["display_name_en"])

    response = test_stock_item.do_add_stock_wasatge(client, user_headers, payload)
    assert response.status_code == 200
    response_body = json.loads(response.data)
    assert response_body['status'] == "successful"
    assert response_body['action'] == "create_stock_wastage"
    
    # print("\n")

def test_e2e_normal_customer_order_flow(client, merchant_setup):
    user_headers, order_panel_headers, merchant_details, deliveroo_branch_details, line_item_discount_id = merchant_setup

    merchant_id = merchant_details["merchant_id"]
    merchant_code = merchant_details["merchant_code"]

    with open("tests/testdata/menus/sample_menu.json", encoding='utf-8') as f:
        sample_menu = json.load(f)

    """
    Correct POS customer orders which should be verified before punching
    """
    test_file_list = []
    test_file_list.append("tests/testdata/customer_orders/pos/01_menu_items_only.json")
    test_file_list.append("tests/testdata/customer_orders/pos/10_all_item_types_with_line_item_discount.json")
    # print("")
    # print("placing orders:")
    # print("-------------------")
    for idx, one_test_file in enumerate(test_file_list):
        with open(one_test_file, encoding='utf-8') as f:
            transaction_payload = json.load(f)
            
            transaction_payload["merchant_code"] = merchant_code

            transaction_payload["integration_details"] = {
                "brand_id": deliveroo_branch_details["brand_id"],
                "facility_id": deliveroo_branch_details["facility_id"],
                "marketplace_id": deliveroo_branch_details["marketplace_id"],
                "branch_id": deliveroo_branch_details["branch_id"],
                "fulfillment_type": "marketplace-delivery"
            }
            
            for one_item in transaction_payload["item_list"]:
                item_name = one_item["display_name_en"]
                
                for one_category in sample_menu["menu_categories"]:
                    for one_sample_item in one_category["menu_items"]:
                        if one_sample_item["menu_item_name_en"] == item_name:
                            one_item["external_item_id"] = one_sample_item["menu_item_external_id"]
                            break
    
            if "discount_list" in transaction_payload:
                for one_discount in transaction_payload["discount_list"]:
                    if one_discount["discount_id"]:
                        one_discount["discount_id"] = line_item_discount_id
    
        # print(f"Running test case {idx+1} with file {one_test_file}")
        filename = one_test_file.split('/')[-1].split('_')[1:]
        # print(f"Order# {idx+1} with {' '.join(filename).split('.')[0]}")

        response = test_customer_order.do_calculate_order(client, order_panel_headers, transaction_payload)    
        j = json.loads(response.data)
        assert j["status"] == 'successful'

        response = test_customer_order.do_create_customer_order(client, order_panel_headers, transaction_payload)    
        j = json.loads(response.data)
        assert j["status"] == 'successful'

        customer_order_id = j["customer_order_id"]
        order_code = j["order_code"]
    
    # print("")

def test_e2e_ai_waste_to_revenue_converter_flow(client, merchant_setup):
    user_headers, order_panel_headers, merchant_details, deliveroo_branch_details, line_item_discount_id = merchant_setup
    
    # response = test_wastage_engine.do_get_near_expiry_items(client, user_headers, deliveroo_branch_details["facility_id"])
    # assert response.status_code == 200
    # response_body = json.loads(response.data)
    # assert response_body['status'] == "successful"
    # assert response_body['action'] == "get_near_expiry_items"
    
    # print("\n")
    
    # # print(json.dumps(response_body, indent=4, default=str))
    # strategy_dict = response_body["data"]["strategy_dict"]
    
    # print("strategies used:")
    # print("-------------------")
    # for one_key in strategy_dict:
    #     print(f"- {one_key}: {strategy_dict[one_key]}")
    # print("")
    
    # print("Getting near expiry items")
    # print("-------------------")
    # formatted_list = []
    # for one_record in response_body["data"]["near_expiry_items"]:
    #     formatted_list.append({
    #         "item_id": one_record["item_id"],
    #         "menu item": one_record["item_name"],
    #         "stock in hand": one_record["item_count"],
    #         "expiry (hours)": one_record['expiry'],
    #         "recommended discount": "50% off",
    #         "predicted wastage": f"{one_record['predicted_item_wastage']} ( {one_record['predicted_item_wastage_percentage']}% )",
    #         "potential conversion": f"{one_record['potential_conversion']}%",
    #         "recommended platforms": "whatsapp, instagram, myapp",
    #     })
    
    # recommendations_df = pd.DataFrame(formatted_list)
    
    # # sort by expiry
    # recommendations_df = recommendations_df.sort_values(by=['expiry (hours)'])
    # recommendations_df["expiry (hours)"] = recommendations_df["expiry (hours)"].apply(lambda x: int(x))
    
    # display(recommendations_df)
    
    # print("\n")
    # print("generating promo")
    # print("-------------------------------")
    
    # # get first record of dataframe in dict
    # first_recommendation = recommendations_df.iloc[0].to_dict()
    
    # promo = {
    #     "Discount Name": first_recommendation["recommended discount"],
    #     "Item(s)": first_recommendation["menu item"],
    #     "Channels": first_recommendation["recommended platforms"],
    #     "Promo text": f"Get {first_recommendation['recommended discount']} off on {first_recommendation['menu item']}! Offer valid for {first_recommendation['expiry (hours)']} hours only!",
    # }
    
    # print(json.dumps(promo, indent=2))
    
    # print("\n")
    # print("generating promo images")
    # print("------------------------")
    
    # image_prompt = "Photograph taken with a 35mm macro lens on high-quality HD film, capturing on The tastiest epic chocolate cake, slice of chocolate cake, square cut, ambrosia, illuminated aura embodying the canvas"
    # print("\nPrompt for image: ", image_prompt)
    
    # response = test_wastage_engine.do_generate_promo_image(client, user_headers, count=1, promo_text=image_prompt)
    # assert response.status_code == 200
    # response_body = json.loads(response.data)
    # assert response_body['status'] == "successful"
    # assert response_body['action'] == "generate_promo_image"
    
    # for encoded_image in response_body["data"]["image_list"]:
        
    #     # decode base64 string to bytes
    #     encoded_image = base64.b64decode(encoded_image)
        
    #     # display image
    #     image = Image.open(io.BytesIO(encoded_image))
    after_id = 0
    before_id = None
    fetch_new_count = 1
    fetch_old_count = 0
    image_url_list, new_after_id, before_id = generative_ai_util.generate_image(before_id, after_id, fetch_new_count, fetch_old_count)
    
    # print("\nGenerated promo image: ", image_url_list)

    # print("\n")
    # print("generating promo text")
    # print("------------------------")
    
    text_prompt = "write me a promo sentence for a 50% discount on chocolate ice cream cake"
    # print("\nPrompt for text: ", text_prompt)
    
    payload = {
        "prompt_text": text_prompt,
        "context": "promo-message"
    }
    response = test_generative_ai.do_generate_text(client, user_headers, payload)
    assert response.status_code == 200
    response_body = json.loads(response.data)
    assert response_body['status'] == "successful"
    assert response_body['action'] == "process_text_prompt"
    
    generated_promo_text = response_body["data"]["generated_text"]
    # print("\nGenerate promo text: ", generated_promo_text)
    
    # print("\n")
    # print("launching campaign with said promo image and text")
    # print("--------------------------------------------------------")
    
    # payload = {
    #     "discount": {
    #         "discount_name": promo["Discount Name"],
    #         "discount_leve": "order-level",
    #         "discount_value": 50,
    #         "percentage_p": 1,
    #         "item_list": promo["Item(s)"],
    #     },
    #     "promo_message": "Get your sweet tooth fix with our delicious chocolate ice cream cake now at a 50%% discount - limited time offer! #ChocolateHeaven #DiscountDelight #SaleTime #IndulgeToday #DessertLove",
    #     "platform_list": ["whatsapp"],
    #     "marketplace_list": ["deliveroo"],
    # }
    # response = test_wastage_engine.do_launch_promotion(client, user_headers, payload)
    # assert response.status_code == 200
    # response_body = json.loads(response.data)
    # assert response_body['status'] == "successful"
    # assert response_body['action'] == "launch_promotion"