import json

from utils import jqutils
from sqlalchemy import text

from tests import test_brand_profile

base_api_url = "/api"

def do_add_user(client, payload):
    """
    ADD USER
    """
    response = client.post(base_api_url + "/user", json=payload)
    return response

def do_add_user_image(client, headers, user_id, payload):
    """
    ADD USER IMAGE
    """
    response = client.post(base_api_url + f"/user/{user_id}/upload-image", headers=headers, data=payload)
    return response

def do_update_user_image(client, headers, user_id, payload):
    """
    UPDATE USER IMAGE
    """
    response = client.put(base_api_url + f"/user/{user_id}/upload-image", headers=headers, data=payload)
    return response

def do_get_username_availablity(client, headers, payload):
    """
    GET USERNAME AVAILABILITY
    """
    response = client.post(base_api_url + "/username-availability", json=payload)
    return response

def do_verify_user_otp(client, headers, user_id, payload):
    """
    VERIFY USER OTP
    """
    response = client.post(base_api_url + f"/user/{user_id}/verify-otp", headers=headers, json=payload)
    return response

def do_get_user(client, headers, user_id):
    """
    GET USER
    """
    response = client.get(base_api_url + f"/user/{user_id}", headers=headers)
    return response

def do_update_user(client, headers, user_id, payload):
    """
    UPDATE USER
    """
    response = client.put(base_api_url + f"/user/{user_id}", headers=headers, json=payload)
    return response

def do_delete_user(client, headers, user_id):
    """
    DELETE USER
    """
    response = client.delete(base_api_url + f"/user/{user_id}", headers=headers)
    return response

def do_get_user_list(client, headers):
    """
    GET USER LIST
    """
    response = client.get(base_api_url + "/users", headers=headers)
    return response

def do_initiate_forgot_password_request(client, headers, payload):
    """
    INITIATE FORGOT PASSWORD REQUEST
    """
    response = client.post(f'{base_api_url}/forgot-password', headers=headers, json=payload)
    return response

def do_get_forgot_password_request(client, headers, otp):
    """
    GET FORGOT PASSWORD REQUEST
    """
    response = client.get(f'{base_api_url}/forgot-password/{otp}', headers=headers)
    return response

def do_reset_user_password(client, headers, payload):
    """
    RESET USER PASSWORD
    """
    response = client.post(f'{base_api_url}/reset-password', json=payload)
    return response

###################
# TESTS CASES
###################

user_id = None
all_brand_access_user_id = None

def test_add_user(client):

    payload = {
        "first_names_en": "John",
        "last_name_en": "Doe",
        "first_names_ar": "جون",
        "last_name_ar": "دو",
        "phone_nr": "1234567890",
        "email": "john.doe@something.com",
        "role_id_list": [1],
        "brand_profile_list": [
            {
                "brand_profile_id": 1,
                "module_access_id_list": [1]
            }
        ]
    }
    response = do_add_user(client, payload)
    assert response.status_code == 200
    
    response_json = response.get_json()
    assert response_json["status"] == "successful"
    assert response_json["action"] == "add_user"

    data = response_json["data"]
    assert data["user_id"]
    
    global user_id
    user_id = data["user_id"]

def test_add_user_image(client, content_team_headers):
    global user_id
    payload = {
        "image_type": "profile"
    }
    response = do_add_user_image(client, content_team_headers, user_id, payload)
    assert response.status_code == 200

    response_json = response.get_json()
    assert response_json["status"] == "successful"
    assert response_json["action"] == "add_user_image"

    data = response_json["data"]
    assert data["user_image_url"] == None

def test_update_user_image(client, content_team_headers):
    global user_id
    payload = {
        "image_type": "profile"
    }
    response = do_update_user_image(client, content_team_headers, user_id, payload)
    assert response.status_code == 200

    response_json = response.get_json()
    assert response_json["status"] == "successful"
    assert response_json["action"] == "update_user_image"

    data = response_json["data"]
    assert data["user_image_url"] == None

def test_get_username_availablity(client, content_team_headers):
    payload = {
        "username": "john.doe"
    }
    response = do_get_username_availablity(client, content_team_headers, payload)
    assert response.status_code == 200

    response_json = response.get_json()
    assert response_json["status"] == "successful"
    assert response_json["action"] == "get_username_availability"

    data = response_json["data"]
    assert data["available_p"] == True, "Username should be available"

def test_verify_user_otp(client, content_team_headers):
    global user_id

    db_engine = jqutils.get_db_engine()

    query = text("""
        SELECT otp, otp_request_count
        FROM one_time_password
        WHERE user_id = :user_id
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, user_id=user_id).fetchone()
        assert result, "OTP not found in DB"

    otp = result["otp"]
    otp_request_count = result["otp_request_count"]
    assert otp_request_count == 0

    payload = {
        "username": "john.doe",
        "password": "123456",
        "otp": otp,
        "intent": "user_signup"
    }
    response = do_verify_user_otp(client, content_team_headers, user_id, payload)
    assert response.status_code == 200

    response_json = response.get_json()
    assert response_json["status"] == "successful"
    assert response_json["action"] == "verify_otp"

    data = response_json["data"]
    assert data["username"]

def test_get_user(client, content_team_headers):
    global user_id

    response = do_get_user(client, content_team_headers, user_id)
    assert response.status_code == 200

    response_json = response.get_json()
    assert response_json["status"] == "successful"
    assert response_json["action"] == "get_user"

    data = response_json["data"]
    assert data["username"]
    assert data["first_names_en"]
    assert data["last_name_en"]
    assert data["first_names_ar"]
    assert data["last_name_ar"]
    assert data["phone_nr"]
    assert data["email"]
    assert data["role_list"]
    assert data["brand_profile_list"]
    assert data["user_image_url"] == None

def test_get_user_list(client, content_team_headers):
    """
    Test: Get User List
    """
    response = do_get_user_list(client, content_team_headers)
    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json["status"] == "successful"
    assert response_json["action"] == "get_users"
    response_data = response_json["data"]
    assert len(response_data) == 1, "User List should have 1 item."

def test_update_user(client, content_team_headers):
    global user_id

    payload = {
        "first_names_en": "John",
        "last_name_en": "Doe-1",
        "first_names_ar": "جون",
        "last_name_ar": "دو",
        "phone_nr": "+9711234567890",
        "email": "john.doe@something.com",
        "role_id_list": [1],
        "brand_profile_list": [
            {
                "brand_profile_id": 1,
                "module_access_id_list": [1]
            }
        ]
    }
    response = do_update_user(client, content_team_headers, user_id, payload)
    assert response.status_code == 200

    response_json = response.get_json()
    assert response_json["status"] == "successful"
    assert response_json["action"] == "update_user"

def test_initiate_forgot_password_request_using_email(client, content_team_headers):
    global user_id
    db_engine = jqutils.get_db_engine()
    
    # get email and username for company-x user
    query = text("""
        SELECT username, email
        FROM user
        WHERE user_id = :user_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, user_id=user_id, meta_status='active').fetchone()
        assert result, "failed to get user_id and email"
        username = result["username"]
        email = result["email"]

    payload = {
        "username": username,
        "email": email,
    }
    response = do_initiate_forgot_password_request(client, content_team_headers, payload)
    assert response.status_code == 200
    response_json = response.get_json()
    
    assert response_json["status"] == "successful"
    assert response_json["action"] == "initiate_forgot_password_request"

    data = response_json["data"]
    assert data["user_id"] == user_id
    assert data["contact_method"] == "email"

def test_initiate_forgot_password_request_using_non_existing_email(client, content_team_headers):
    
    username = None
    email = "dummy@example.com"

    payload = {
        "username": username,
        "email": email,
    }
    response = do_initiate_forgot_password_request(client, content_team_headers, payload)
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json["status"] == "failed"
    assert response_json["action"] == "initiate_forgot_password_request"
    assert response_json["message"] == "User not found"

def test_get_forgot_password_request_successfully(client, content_team_headers):
    global user_id
    db_engine = jqutils.get_db_engine()
    
    otp_status = 'sent'
    contact_method = 'email'
    intent = 'forgot_password'

    query = text("""
        SELECT otp
        FROM one_time_password
        WHERE otp_status = :otp_status
        AND contact_method = :contact_method
        AND user_id = :user_id
        AND intent = :intent
        AND meta_status = :meta_status
        ORDER BY otp_requested_timestamp DESC
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, otp_status=otp_status, contact_method=contact_method, user_id=user_id, intent=intent, meta_status='active').fetchone()
        assert result, "failed to get otp"
        otp = result["otp"]
    
    response = do_get_forgot_password_request(client, content_team_headers, otp)
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json["status"] == "successful"
    assert response_json["action"] == "get_forgot_password_request"

    data = response_json["data"]
    assert data["otp_status"] == otp_status

def test_reset_password_using_otp_successful(client, content_team_headers):
    global user_id
    db_engine = jqutils.get_db_engine()

    otp_status = 'sent'
    contact_method = 'email'
    intent = 'forgot_password'

    query = text("""
        SELECT otp
        FROM one_time_password
        WHERE otp_status = :otp_status
        AND contact_method = :contact_method
        AND user_id = :user_id
        AND intent = :intent
        AND meta_status = :meta_status
        ORDER BY otp_requested_timestamp DESC
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, otp_status=otp_status, contact_method=contact_method, user_id=user_id, intent=intent, meta_status='active').fetchone()
        assert result, "failed to get otp"
        otp = result["otp"]
    
    payload = {
        "otp": otp,
        "password": "654321"
    }
    response = do_reset_user_password(client, content_team_headers, payload)
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json["status"] == "successful"
    assert response_json["action"] == "reset_user_password"

    data = response_json["data"]
    assert data["user_id"] == user_id

def test_delete_user(client, content_team_headers):
    global user_id

    response = do_delete_user(client, content_team_headers, user_id)
    assert response.status_code == 200

    response_json = response.get_json()
    assert response_json["status"] == "successful"
    assert response_json["action"] == "delete_user"

    response = do_get_user_list(client, content_team_headers)
    assert response.status_code == 200

    response_json = response.get_json()
    assert response_json["status"] == "successful"
    assert response_json["action"] == "get_users"

    data = response_json["data"]
    assert len(data) == 0, "User List should have 0 item."

###################
# TESTS CASES - ALL BRAND PROFILE ACCESS
###################
def test_add_user_with_all_brand_profile_access(client, content_team_headers):

    """
    Test: Add Brand Profile
    """
    payload = {
        "brand_profile_name": "qoqo",
        "external_brand_profile_id": "1",
        "plan_list": [
            {
                "plan_id": 1,
                "menu_group_id_list": [1, 2]
            }
        ]
    }
    response = test_brand_profile.do_add_brand_profile(client, content_team_headers, payload)
    assert response.status_code == 200

    response_json = response.get_json()
    assert response_json["status"] == "successful"
    assert response_json["action"] == "add_brand_profile"

    payload = {
        "first_names_en": "Johnny",
        "last_name_en": "Doe",
        "first_names_ar": "جوني",
        "last_name_ar": "دو",
        "phone_nr": "1234567890",
        "email": "johnny.doe@something.com",
        "role_id_list": [1],
        "brand_profile_list": [],
        "all_brand_profile_access_p": True,
        "module_access_id_list": [1]
    }

    response = do_add_user(client, payload)
    assert response.status_code == 200

    response_json = response.get_json()
    assert response_json["status"] == "successful"
    assert response_json["action"] == "add_user"

    data = response_json["data"]
    assert data["user_id"]

    global all_brand_access_user_id
    all_brand_access_user_id = data["user_id"]

def test_update_all_brand_access_user(client, content_team_headers):
    global all_brand_access_user_id

    payload = {
        "first_names_en": "Johnny",
        "last_name_en": "Doe-1",
        "first_names_ar": "جوني",
        "last_name_ar": "دو",
        "phone_nr": "+9711234567890",
        "email": "johnny.doe@something.com",
        "role_id_list": [1],
        "brand_profile_list": [],
        "all_brand_profile_access_p": True,
        "module_access_id_list": [2]
    }

    response = do_update_user(client, content_team_headers, all_brand_access_user_id, payload)
    assert response.status_code == 200

    response_json = response.get_json()
    assert response_json["status"] == "successful"
    assert response_json["action"] == "update_user"

def test_get_all_brand_access_user(client, content_team_headers):
    global all_brand_access_user_id

    response = do_get_user(client, content_team_headers, all_brand_access_user_id)
    assert response.status_code == 200

    response_json = response.get_json()
    assert response_json["status"] == "successful"
    assert response_json["action"] == "get_user"

    data = response_json["data"]
    assert data["username"] == None
    assert data["first_names_en"]
    assert data["last_name_en"]
    assert data["first_names_ar"]
    assert data["last_name_ar"]
    assert data["phone_nr"]
    assert data["email"]
    assert data["all_brand_profile_access_p"] == True, "User should have all brand profile access"
    assert data["role_list"]
    assert data["module_access_list"]
    assert data["brand_profile_list"]
    assert data["user_image_url"] == None

def test_delete_all_brand_access_user(client, content_team_headers):
    global all_brand_access_user_id

    response = do_delete_user(client, content_team_headers, all_brand_access_user_id)
    assert response.status_code == 200

    response_json = response.get_json()
    assert response_json["status"] == "successful"
    assert response_json["action"] == "delete_user"

    response = do_get_user_list(client, content_team_headers)
    assert response.status_code == 200

    response_json = response.get_json()
    assert response_json["status"] == "successful"
    assert response_json["action"] == "get_users"

    data = response_json["data"]
    assert len(data) == 0, "User List should have 0 item."