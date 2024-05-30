from datetime import datetime
from utils import jqutils
from tests.test_login import do_login
from tests.test_user import do_add_user
from utils import jqutils
from sqlalchemy import text
import json
import random

base_api_url = "/api"

##############
# TEST - MERCHANT
##############

def do_get_merchants(client,headers):
    """
    Get Merchants
    """
    response = client.get(base_api_url + "/merchants", headers=headers)
    return response

def do_get_merchant(client, headers, merchant_id):
    """
    Get One Merchant
    """
    response = client.get(base_api_url + f"/merchant/{merchant_id}", headers=headers)
    return response

def do_get_customer_orders_by_merchant(client, headers, merchant_id, payload):
    """
    Get Customer Orders by Merchant Id
    """
    response = client.post(base_api_url + f"/merchant/{merchant_id}/customer-orders", headers=headers, json=payload)
    return response

def do_get_merchant_users(client, headers, merchant_id):
    """
    Get One Merchant
    """
    response = client.get(base_api_url + f"/merchant/{merchant_id}/users", headers=headers)
    return response

def do_get_myapp_branches(client, user_headers, merchant_id, payload):
    """
    Get list of closest branches for MyApp functionality by Merchant ID
    """
    response = client.post(base_api_url + "/merchant/" + str(merchant_id) + "/myapp", headers=user_headers, json=payload)
    return response

def do_get_iblinkmarketplace_branches(client, user_headers, merchant_id, payload):
    """
    Get list of closest branches for iblinkmarketplace functionality by Merchant ID
    """
    response = client.post(base_api_url + "/merchant/" + str(merchant_id) + "/iblinkmarketplace", headers=user_headers, json=payload)
    return response

def do_get_facility_fulfillment_type_map_for_merchant(client, headers, merchant_id):
    """
    Get Facility Fulfillment Type Map for Merchant
    """
    response = client.get(f'{base_api_url}/merchant/{merchant_id}/facility-fulfillment-type-maps', headers=headers)
    return response

def do_add_merchant(client, headers, payload):
    """
    Add Merchant
    """
    response = client.post(f'{base_api_url}/merchant', headers=headers, json=payload)
    return response

def do_update_merchant(client, headers, payload):
    """
    Update Merchant
    """
    response = client.put(f'{base_api_url}/merchant', headers=headers, json=payload)
    return response

def do_get_merchant_balance(client, headers, merchant_id, days=0):
    """
    Get Merchant Balance
    """
    response = client.get(f'{base_api_url}/merchant-balance/{merchant_id}?days={days}', headers=headers)
    return response

def do_update_merchant_ui_theme(client, headers, merchant_id, payload):
    """
    Update UI Theme for a Merchant
    """
    response = client.put(f'{base_api_url}/merchant/{merchant_id}/ui-theme', headers=headers, json=payload)
    return response

def do_get_merchant_order_panel(client, headers, merchant_id):
    """
    Get Order Panel for a Merchant
    """
    response = client.get(f'{base_api_url}/merchant/{merchant_id}/order-panel', headers=headers)
    return response

def do_update_merchant_order_panel(client, headers, merchant_id, payload):
    """
    Update Order Panel for a Merchant
    """
    response = client.put(f'{base_api_url}/merchant/{merchant_id}/order-panel', headers=headers, json=payload)
    return response

def do_add_merchant_third_party_credential(client, headers, merchant_id, payload):
    """
    Add Third Party Credential for a Merchant
    """
    response = client.post(f'{base_api_url}/merchant/{merchant_id}/credential', headers=headers, json=payload)
    return response

def do_update_merchant_third_party_credential_for_merchant(client, headers, merchant_id, payload):
    """
    Update Third Party Credential for a Merchant
    """
    response = client.put(f'{base_api_url}/merchant/{merchant_id}/credential', headers=headers, json=payload)
    return response

def do_update_merchant_third_party_credential(client, headers, merchant_third_party_credential_id, payload):
    """
    Update Third Party Credential
    """
    response = client.put(f'{base_api_url}/merchant-third-party-credential/{merchant_third_party_credential_id}', headers=headers, json=payload)
    return response

def do_delete_merchant_third_party_credential(client, headers, merchant_third_party_credential_id):
    """
    Delete Third Party Credential
    """
    response = client.delete(f'{base_api_url}/merchant-third-party-credential/{merchant_third_party_credential_id}', headers=headers)
    return response

def do_get_merchant_third_party_credential(client, headers, merchant_id, third_party_credential_type):
    """
    Get Third Party Credential for a Merchant
    """
    response = client.get(f'{base_api_url}/merchant/{merchant_id}/credential?third_party_credential_type={third_party_credential_type}', headers=headers)
    return response

def do_get_merchant_marketplace_credentials(client, headers, merchant_id):
    """
    Get Marketplace Third Party Credentials for a Merchant
    """
    response = client.get(f'{base_api_url}/merchant/{merchant_id}/marketplace-credentials', headers=headers)
    return response

def do_add_merchant_marketplace_credential(client, headers, merchant_id, payload):
    """
    Add Marketplace Credential for a Merchant
    """
    response = client.post(f'{base_api_url}/merchant/{merchant_id}/marketplace-credential', headers=headers, json=payload)
    return response

def do_login_with_merchant_marketplace_credential(client, headers, payload):
    """
    Login With Marketplace Credential
    """
    response = client.post(f'{base_api_url}/external-login', headers=headers, json=payload)
    return response

def do_get_merchant_firebase_configs(client, headers):
    """
    Get firebase configs for merchant
    """
    response = client.get(f'{base_api_url}/merchant/firebase-configs', headers=headers)
    return response

def do_get_item_categories_by_merchant(client, headers, merchant_id):
    """
    Get item categories by merchant
    """
    response = client.get(f'{base_api_url}/merchant/{merchant_id}/item-categories', headers=headers)
    return response

def do_get_merchant_iblinkmarketplace_config(client, headers, merchant_code):
    """
    Get Merchant iBlinkMarketplace Config
    """
    response = client.get(f'{base_api_url}/merchant/{merchant_code}/iblinkmarketplace-config', headers=headers)
    return response

def do_add_merchant_and_user(client, create_order_panel_user=False, create_marketplace_user=False, connect_account_p=False, commission_paid_by_merchant_p=0, default_tip=0, default_currency_id=1, default_country_id=1, merchant_features=None, merchant_name=None):
    """
    Create Normal Merchant And User Account:
    - log in as admin
    - create normal merchant account
    - create user account for merchant
    - return user_id for the user account
    """
    
    """
    Admin Login
    """
    response = do_login(client, 'admin', 'alburaaq424')
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'

    headers = {
        'X-User-Id': response.headers["X-User-Id"],
        'X-Access-Token': response.headers["X-Access-Token"]
    }

    """
    Creating New Merchant
    """
    merchant_type = "normal" if connect_account_p == False else "connect"
    merchant_type_id = jqutils.get_id_by_name(merchant_type, "merchant_type_name", "merchant_type")
    merchant_details = {
        "merchant_name": merchant_name if merchant_name else f"{merchant_type} merchant" + str(random.randint(1000, 9999)),
        "merchant_type_id": merchant_type_id,
        "merchant_email": f"{merchant_type}" + str(random.randint(1000, 9999)) + "@merchant.com",
        "merchant_website_url": f"{merchant_type}.merchant.com",
        "merchant_description": f"{merchant_type} merchant",
        "default_currency_id": default_currency_id,
        "default_country_id": default_country_id,
        "business_type_id": 1,
        "business_category_id": 1,
        "stripe_merchant_id": "acct_1JQ2ZzJZQ" + str(random.randint(1000, 9999)) if connect_account_p else None,
    }

    # get default merchant commission rules
    query = text("""
        SELECT service_provider_id, minimum_transaction_amount, maximum_transaction_amount,
        commission_cap_amount, commission_percentage, fixed_commission, currency_id
        FROM default_merchant_commission
        WHERE currency_id = :currency_id
        AND meta_status = :meta_status
    """)
    db_engine = jqutils.get_db_engine()
    with db_engine.connect() as conn:
        result = conn.execute(query, currency_id=default_currency_id, meta_status='active').fetchall()
        assert result, "Failed to get default merchant commission rules"
        
        commission_rules = []
        for one_rule in result:
            
            already_handled = False
            for one_commission in commission_rules:
                if one_commission["service_provider_id"] == one_rule["service_provider_id"]:
                    one_commission["rules"].append({
                        "minimum_transaction_amount": one_rule["minimum_transaction_amount"],
                        "maximum_transaction_amount": one_rule["maximum_transaction_amount"],
                        "commission_cap_amount": one_rule["commission_cap_amount"],
                        "commission_percentage": one_rule["commission_percentage"],
                        "fixed_commission": one_rule["fixed_commission"],
                        "currency_id": one_rule["currency_id"],
                    })
                    already_handled = True
                    break
            
            if not already_handled:
                commission_rules.append({
                    "service_provider_id": one_rule["service_provider_id"],
                    "rules": [{
                        "minimum_transaction_amount": one_rule["minimum_transaction_amount"],
                        "maximum_transaction_amount": one_rule["maximum_transaction_amount"],
                        "commission_cap_amount": one_rule["commission_cap_amount"],
                        "commission_percentage": one_rule["commission_percentage"],
                        "fixed_commission": one_rule["fixed_commission"],
                        "currency_id": one_rule["currency_id"],
                    }]
                })

    merchant_id, merchant_payload = test_add_merchant(client, headers, merchant_details, commission_rules=commission_rules, commission_paid_by_merchant_p=commission_paid_by_merchant_p, default_tip=default_tip, merchant_features=merchant_features)

    """
    Creating New User (Role: Merchant)
    """
    username = "normal_e2e_user" + str(random.randint(1000, 9999))
    email = "normal_e2e_user" + str(random.randint(1000, 9999)) + "@gmail.com"
    password = "123abc"
    
    # generate random phone number
    phone_nr = "+924235453" + str(random.randint(1000, 9999))
    payload = {
        "username": username,
        "email": email,
        "business_designation": None,
        "first_names_en": "e2e",
        "last_name_en": "user",
        "first_names_ar": "",
        "last_name_ar": "",
        "phone_nr": phone_nr,
        "password": password,
        "password_expiry_timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "access_token": "",
        "personal_access_code": "123456",
        "token_expiry_timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "root_p": True,
        "role_id": jqutils.get_id_by_name("merchant", "role_name", "role"),
        "merchant_id": merchant_id,
        "facility_id_list":[1,2,3],
        "request_otp": False,
    }
    
    response = do_add_user(client, headers, payload)
    assert response.status_code == 200, "failed to add user"
    assert response.json['status'] == 'successful', "failed to add user"

    """
    User Login
    """
    response = do_login(client, username, password)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'

    logged_in_user_details = {
        "user_id": response.headers["X-User-Id"],
        "access_token": response.headers["X-Access-Token"],
        "merchant_id": j["merchant"]["merchant_id"],
        "merchant_api_key": j["merchant"]["merchant_api_key"],
        "merchant_name": j["merchant"]["merchant_name"],
    }

    logged_in_order_panel_details = None

    if create_order_panel_user:
        """
        Creating New User (Role: Order Panel)
        """
        order_panel_username = "order_panel" + str(random.randint(1000, 9999))
        order_panel_email = "order_panel" + str(random.randint(1000, 9999)) + "@gmail.com"
        order_panel_password = "123abc"
        
        # generate random phone number
        order_panel_phone_nr = "+924235453" + str(random.randint(1000, 9999))
        payload = {
            "username": order_panel_username,
            "email": order_panel_email,
            "business_designation": None,
            "first_names_en": "order",
            "last_name_en": "panel",
            "first_names_ar": "",
            "last_name_ar": "",
            "phone_nr": order_panel_phone_nr,
            "password": order_panel_password,
            "password_expiry_timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "access_token": "",
            "personal_access_code": "123456",
            "token_expiry_timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "root_p": True,
            "role_id": jqutils.get_id_by_name("order-panel", "role_name", "role"),
            "merchant_id": merchant_id,
            "facility_id_list":[1,2,3],
            "request_otp": False,
        }
        
        response = do_add_user(client, headers, payload)
        assert response.status_code == 200, "failed to add user"
        assert response.json['status'] == 'successful', "failed to add user"

        """
        Order Panel Login
        """
        response = do_login(client, order_panel_username, order_panel_password)
        assert response.status_code == 200
        j = json.loads(response.data)
        assert j["status"] == 'successful'

        logged_in_order_panel_details = {
            "user_id": response.headers["X-User-Id"],
            "access_token": response.headers["X-Access-Token"],
            "merchant_id": j["merchant"]["merchant_id"],
            "merchant_api_key": j["merchant"]["merchant_api_key"],
        }
    
    logged_in_marketplace_details = None
    if create_marketplace_user:
        """
        Creating New User (Role: Marketplace)
        """
        marketplace_username = "marketplace" + str(random.randint(1000, 9999))
        marketplace_email = "marketplace" + str(random.randint(1000, 9999)) + "@gmail.com"
        marketplace_password = "123abc"
        
        # generate random phone number
        marketplace_phone_nr = "+924235453" + str(random.randint(1000, 9999))
        payload = {
            "username": marketplace_username,
            "email": marketplace_email,
            "business_designation": None,
            "first_names_en": "marketplace",
            "last_name_en": "user",
            "first_names_ar": "",
            "last_name_ar": "",
            "phone_nr": marketplace_phone_nr,
            "password": marketplace_password,
            "password_expiry_timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "access_token": "",
            "personal_access_code": "123456",
            "token_expiry_timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "root_p": True,
            "role_id": jqutils.get_id_by_name("marketplace", "role_name", "role"),
            "merchant_id": merchant_id,
            "facility_id_list":[1,2,3],
            "request_otp": False,
        }
        
        response = do_add_user(client, headers, payload)
        assert response.status_code == 200, "failed to add user"
        assert response.json['status'] == 'successful', "failed to add user"

        """
        Marketpalce Login
        """
        response = do_login(client, marketplace_username, marketplace_password)
        assert response.status_code == 200
        j = json.loads(response.data)
        assert j["status"] == 'successful'

        logged_in_marketplace_details = {
            "user_id": response.headers["X-User-Id"],
            "access_token": response.headers["X-Access-Token"],
            "merchant_id": j["merchant"]["merchant_id"],
            "merchant_api_key": j["merchant"]["merchant_api_key"],
        }

    return logged_in_user_details, merchant_payload, logged_in_order_panel_details, logged_in_marketplace_details

###########
# Globals
###########
merchant_third_party_credential_id = None

###########
# TESTS
###########

def test_get_merchants(client, headers):
    """
    Test get merchants
    """
    response = do_get_merchants(client, headers)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert len(j["data"]) > 0
    assert j["action"] == 'search_merchant_by_filter'

def test_get_merchant(client, headers):
    """
    Test get merchant
    """
    merchant_id = 1
    response = do_get_merchant(client, headers, merchant_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_merchant'

def test_get_merchant_users(client, headers):
    """
    Test get merchant
    """
    merchant_id = 1
    response = do_get_merchant_users(client, headers, merchant_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_users_for_merchant'
    assert len(j["data"]) > 0

def test_add_merchant(client, headers, merchant_details=None, merchant_settings=None, merchant_features=None, commission_rules=None, merchant_tip_choices=None, commission_paid_by_merchant_p=0, default_tip=0):
    """
    Test add merchant
    """

    # use default values if not provided
    if merchant_details is None:
        merchant_details = {
            "merchant_name": "dummy merchant",
            "merchant_type_id": 1,
            "merchant_email": "dummy@merchant.com",
            "merchant_website_url": "dummy.merchant.com",
            "merchant_description": "dummy merchant",
            "default_currency_id": 1,
            "default_country_id": 1,
            "business_type_id": 1,
            "business_category_id": 1,
            "stripe_merchant_id": None
        }
    
    # use default values if not provided
    if merchant_settings is None:
        merchant_settings = {
            "payout_cycle_duration": 15,
            "duration_measurement_id": 12,
            "commission_paid_by_merchant_p": commission_paid_by_merchant_p,
            "payment_link_expiry_duration": 15,
            "expiry_duration_measurement_id": 1
        }
    
    # use default values if not provided
    if merchant_features is None:
        merchant_features = [
            {
                "feature_id":1,
                "enabled": 1
            },
            {
                "feature_id":2,
                "enabled": 0
            },
            {
                "feature_id":3,
                "enabled": 0
            },
            {
                "feature_id":4,
                "enabled": 0
            },
            {
                "feature_id":5,
                "enabled": 0
            },
            {
                "feature_id":6,
                "enabled": 1
            },
            {
                "feature_id":15,
                "enabled": 1
            }
        ]
    
    # use default values if not provided
    if commission_rules is None:
        commission_rules = [
            {
                "service_provider_id": 1,
                "rules": [
                    {
                        "minimum_transaction_amount": 5,
                        "maximum_transaction_amount": None,
                        "commission_cap_amount": None,
                        "commission_percentage": 0.5,
                        "fixed_commission": 0,
                        "currency_id": 1,
                    }
                ],
            }
            
        ]
    
    # use default values if not provided
    if merchant_tip_choices is None:
        merchant_tip_choices = [
            {
                "tip_amount": 5,
                "percentage_p": 1,
                "default_p": default_tip,
                "tip_currency_id": 1
            },
            {
                "tip_amount": 10,
                "percentage_p": 0,
                "default_p": 0,
                "tip_currency_id": 1
            },
            {
                "tip_amount": 20,
                "percentage_p": 1,
                "default_p": 0,
                "tip_currency_id": 1
            }
        ]

    payload = {
        "merchant_name": merchant_details["merchant_name"],
        "merchant_type_id": merchant_details["merchant_type_id"],
        "merchant_email": merchant_details["merchant_email"],
        "merchant_website_url": merchant_details["merchant_website_url"],
        "merchant_description": merchant_details["merchant_description"],
        "default_currency_id": merchant_details["default_currency_id"],
        "default_country_id": merchant_details["default_country_id"],
        "business_type_id": merchant_details['business_type_id'],
        "business_category_id": merchant_details['business_category_id'],
        "stripe_merchant_id": merchant_details['stripe_merchant_id'],

        "payout_cycle_duration": merchant_settings["payout_cycle_duration"],
        "duration_measurement_id": merchant_settings["duration_measurement_id"],
        "commission_paid_by_merchant_p": merchant_settings["commission_paid_by_merchant_p"],
        "payment_link_expiry_duration": merchant_settings["payment_link_expiry_duration"],
        "expiry_duration_measurement_id": merchant_settings["expiry_duration_measurement_id"],

        "merchant_features": merchant_features,
        "commission_rules": commission_rules,
        "merchant_tip_choices": merchant_tip_choices
    }

    response = do_add_merchant(client, headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert "merchant" in j
    merchant_id = j["merchant"]["merchant_id"]
    merchant_code = j["merchant"]["merchant_code"]
    payload["merchant_code"] = merchant_code
    payload["merchant_id"] = merchant_id

    return merchant_id, payload

def test_update_merchant(client, headers):
    """
    Test update merchant
    """
    merchant_id = jqutils.get_id_by_name("dummy@merchant.com","merchant_email","merchant")
    payload = {
        "merchant_id": merchant_id,
        "merchant_name": "dummy merch",
        "merchant_description": "dummy merch",
        "merchant_website_url": "dummy.merch.com",
        "merchant_email": "dummy@merch.com",
        "merchant_phone_nr": "+92123456789",
        "merchant_type_id": 2,
        "stripe_merchant_id": "acct_1JQ2ZzJZQ" + str(random.randint(1000, 9999)),
        "business_category_id": 1,
        "business_type_id": 1,
        "commission_paid_by_merchant_p": 0,
        "verification_status": "verified",
        "payout_cycle_duration": 30,
        "duration_measurement_id": 12,
        "payment_link_expiry_duration": None,
        "expiry_duration_measurement_id": None
    }
    response = do_update_merchant(client, headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert "merchant" in j

def test_get_merchant_balance(client, headers):
    """
    Test get merchant balance
    """
    days = 30
    merchant_id = 1
    response = do_get_merchant_balance(client, headers, merchant_id, days=days)
    assert response.status_code == 200

    response_body = response.json

    assert response_body["status"] == "successful"
    assert len(response_body["past_balances"]) == days, f"past_balances should have {days} days"

def test_add_merchant_third_party_credential(client, headers):
    """
    Test add merchant third party credential
    """
    merchant_id = 1
    payload = {
        "third_party_credential_type": "marketplace",
        "username": "test",
        "password": "test"
    }
    response = do_add_merchant_third_party_credential(client, headers, merchant_id, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    
    global merchant_third_party_credential_id
    merchant_third_party_credential_id = j["merchant_third_party_credential_id"]

def test_update_merchant_third_party_credential_for_merchant(client, headers):
    """
    Test update merchant third party credential for merchant
    """
    payload = {
        "third_party_credential_type": "marketplace",
        "username": "test upd 2",
        "password": "test"
    }
    response = do_update_merchant_third_party_credential_for_merchant(client, headers, merchant_third_party_credential_id, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'

def test_update_merchant_third_party_credential(client, headers):
    """
    Test update merchant third party credential
    """
    merchant_id = 1
    payload = {
        "third_party_credential_type": "marketplace",
        "username": "test upd",
        "password": "test"
    }
    response = do_update_merchant_third_party_credential(client, headers, merchant_id, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'

def test_delete_merchant_third_party_credential(client, headers):
    """
    Test delete merchant third party credential
    """
    response = do_delete_merchant_third_party_credential(client, headers, merchant_third_party_credential_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'

def test_get_merchant_third_party_credential(client, headers):
    """
    Test get merchant third party credential
    """
    merchant_id = 1
    third_party_credential_type = "marketplace"
    response = do_get_merchant_third_party_credential(client, headers, merchant_id, third_party_credential_type)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'

    assert j["data"]["third_party_credential_type"] == third_party_credential_type
    assert j["data"]["username"] == "test upd"
    assert j["data"]["password"] == "test"

def test_add_merchant_marketplace_credential_talabat(client, headers):
    """
    Test add merchant marketplace credential talabat
    """
    merchant_id = 2
    payload = {
        "marketplace_id": 2,
        "username": "test",
        "password": "test"
    }
    response = do_add_merchant_marketplace_credential(client, headers, merchant_id, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'

def test_add_merchant_marketplace_credential_deliveroo(client, headers):
    """
    Test add merchant marketplace credential deliveroo
    """
    merchant_id = 2
    payload = {
        "marketplace_id": 1,
        "username": "test",
        "password": "test"
    }
    response = do_add_merchant_marketplace_credential(client, headers, merchant_id, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'

def test_add_merchant_marketplace_credential_careem(client, headers):
    """
    Test add merchant marketplace credential careem
    """
    merchant_id = 2
    payload = {
        "marketplace_id": 3,
        "username": "test",
        "password": "test"
    }
    response = do_add_merchant_marketplace_credential(client, headers, merchant_id, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'

def test_add_merchant_marketplace_credential_noon(client, headers):
    """
    Test add merchant marketplace credential noon
    """
    merchant_id = 2
    payload = {
        "marketplace_id": 4,
        "username": "test",
        "password": "test"
    }
    response = do_add_merchant_marketplace_credential(client, headers, merchant_id, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'

def test_login_with_third_party_credentials_neighbourhood_pulse(client, headers):
    """
    Test login with third party credentials neighbourhood pulse
    """
    third_party_credential_type = "neighbourhood-pulse"
    payload = {
        "third_party_credential_type": third_party_credential_type,
        "merchant_id": 3,
        "user_id": 1
    }

    response = do_login_with_merchant_marketplace_credential(client, headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'

def test_get_merchant_marketplace_credentials(client, headers):
    """
    Test get merchant marketplace credentials
    """
    merchant_id = 2
    response = do_get_merchant_marketplace_credentials(client, headers, merchant_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_merchant_marketplace_credentials'

    assert len(j["data"]), "no marketplace credentials found"

def test_update_merchant_ui_theme(client, headers):
    """
    Test updating merchant ui theme
    """

    merchant_id = 1
    payload = {
        "ui_theme_name": "test",
        "theme_properties": {
            "primary_color": "#000000",
            "secondary_color": "#ffffff",
            "tertiary_color": "#000000",
        }
    }
    response = do_update_merchant_ui_theme(client, headers, merchant_id, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'update_merchant_ui_theme'

def test_get_order_panel_for_merchant(client, user_headers):
    """
    Test getting order panel for merchant
    """

    merchant_id = 1
    response = do_get_merchant_order_panel(client, user_headers, merchant_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_merchant_order_panel'

def test_update_order_panel_for_merchant(client, user_headers):
    """
    Test updating order panel for merchant
    """

    merchant_id = 1
    response = do_get_merchant_order_panel(client, user_headers, merchant_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_merchant_order_panel'

    payload = {
        "username": j["data"]["username"],
        "old_password": j["data"]["password"],
        "new_password": "55677432",
    }
    response = do_update_merchant_order_panel(client, user_headers, merchant_id, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'update_merchant_order_panel'

    merchant_id = 1
    response = do_get_merchant_order_panel(client, user_headers, merchant_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_merchant_order_panel'

    assert j["data"]["password"] == payload["new_password"], "password should be updated"

def test_get_merchant_myapp_branches(client, user_headers):
    """
    Test getting myapp branches for merchant
    """

    merchant_id = 1
    payload = {
        "latitude": 24.8607,
        "longitude": 67.0011,
        "radius": 100,
        "limit": 10,
        "offset": 0
    }
    response = do_get_myapp_branches(client, user_headers, merchant_id, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'

def test_get_merchant_iblinkmarketplace_branches(client, user_headers):
    """
    Test getting myapp branches for merchant
    """

    merchant_id = 1
    payload = {
        "latitude": 24.8607,
        "longitude": 67.0011,
        "radius": 100,
        "limit": 10,
        "offset": 0
    }
    response = do_get_iblinkmarketplace_branches(client, user_headers, merchant_id, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'

def test_get_facility_fulfillment_type_map_for_merchant(client, headers):
    """
    Test getting all facility fulfillment type maps for merchant
    """

    merchant_id = 1
    response = do_get_facility_fulfillment_type_map_for_merchant(client, headers, merchant_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'

def test_get_merchant_firebase_configs(client, headers):
    """
    Test getting firebase configs for merchant
    """

    response = do_get_merchant_firebase_configs(client, headers)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_merchant_firebase_configs'
    
def test_get_item_categories_by_merchant(client, headers):
    """
    Test getting item categories by merchant
    """
    
    response = do_get_item_categories_by_merchant(client, headers, 1)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_item_categories_by_merchant'
    assert len(j["data"]) > 0

def test_get_merchant_iblinkmarketplace_config(client, headers):
    """
    Test getting iblinkmarketplace config for merchant
    """
    merchant_id = 1
    merchant_code = jqutils.get_column_by_id(merchant_id, "merchant_code", "merchant")
    
    response = do_get_merchant_iblinkmarketplace_config(client, headers, merchant_code)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_merchant_iblinkmarketplace_config'