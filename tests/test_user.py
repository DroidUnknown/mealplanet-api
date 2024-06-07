import json

from utils import jqutils
from sqlalchemy import text

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

###################
# TESTS CASES
###################

user_id = None
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
    assert response_json["status"] == "failed"
    assert response_json["action"] == "verify_otp"

    data = response_json["data"]
    # assert data["username"]

def test_get_user(client, content_team_headers):
    global user_id

    response = do_get_user(client, content_team_headers, user_id)
    assert response.status_code == 200

    response_json = response.get_json()
    assert response_json["status"] == "successful"
    assert response_json["action"] == "get_user"

    data = response_json["data"]
    # assert data["username"]
    # assert data["first_names_en"]
    # assert data["last_name_en"]
    # assert data["first_names_ar"]
    # assert data["last_name_ar"]
    # assert data["phone_nr"]
    # assert data["email"]
    # assert data["role_list"]
    # assert data["brand_profile_list"]
    # assert data["user_image_url"]

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

# def test_delete_user(client, content_team_headers):
#     global user_id

#     response = do_delete_user(client, content_team_headers, user_id)
#     assert response.status_code == 200

#     response_json = response.get_json()
#     assert response_json["status"] == "successful"
#     assert response_json["action"] == "delete_user"

def test_get_user_list(client, content_team_headers):
    response = do_get_user_list(client, content_team_headers)
    assert response.status_code == 200

    response_json = response.get_json()
    assert response_json["status"] == "successful"
    assert response_json["action"] == "get_users"

    data = response_json["data"]
    assert len(data) == 1, "User List should have 0 item."