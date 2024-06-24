import json
import pytest

from sqlalchemy import text
from utils import jqutils

base_api_url = "/api"

##############################
# TEST - USER IMAGE
##############################
def do_add_user_image(client, headers, payload):
    """
    Add user image
    """
    cand_headers = headers.copy()
    cand_headers["Content-Type"] = "multipart/form-data"
    response = client.post(base_api_url + "/user-image", headers=cand_headers, data=payload)
    return response

def do_get_user_image(client, headers, user_image_id):
    """
    Get user image
    """
    response = client.get(base_api_url + f"/user-image/{user_image_id}", headers=headers)
    return response

def do_get_user_images_by_user(client, headers, user_id):
    """
    Get user images by user
    """
    response = client.get(base_api_url + f"/user/{user_id}/images", headers=headers)
    return response

def do_update_user_image(client, headers, user_image_id, payload):
    """
    Update user image
    """
    cand_headers = headers.copy()
    cand_headers["Content-Type"] = "multipart/form-data"
    response = client.put(base_api_url + f"/user-image/{user_image_id}", headers=headers, data=payload)
    return response

def do_delete_user_image(client, headers, user_image_id):
    """
    Delete user image
    """
    response = client.delete(base_api_url + f"/user-image/{user_image_id}", headers=headers)
    return response

##########################
# GLOBALS
########################## 
user_id = 5
user_image_id = None
user_image_url = None

##########################
# FIXTURES
##########################
@pytest.fixture(scope="module", autouse=True)
def existing_user_image_count():
    db_engine = jqutils.get_db_engine()
    
    query = text("""
        SELECT COUNT(1) AS cnt
        FROM user_image
        WHERE user_id = :user_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, user_id=user_id, meta_status="active").fetchone()
        return result["cnt"]

##########################
# TEST CASES
########################## 
def test_add_user_image(client, content_team_headers):
    """
    Test: Add user image
    """
    
    with open("tests/testdata/assets/prep-and-co-logo.png", "rb") as image_data:
        payload = {
            "user_id": user_id,
            "image_type": "profile-picture",
            "user_image": image_data
        }
        response = do_add_user_image(client, content_team_headers, payload)
        assert response.status_code == 200

    response_json = response.get_json()
    assert response_json["status"] == "successful"
    assert response_json["action"] == "add_user_image"

    global user_image_id
    response_data = response_json["data"]
    user_image_id = response_data["user_image_id"]

def test_get_user_image(client, content_team_headers):
    """
    Test: Get user image
    """
    response = do_get_user_image(client, content_team_headers, user_image_id)
    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json["status"] == "successful"
    assert response_json["action"] == "get_user_image"

    response_data = response_json["data"]
    assert response_data["user_image_id"] == user_image_id
    assert response_data["image_type"] == "profile-picture"
    assert response_data["user_image_url"] is not None, "User Image URL should not be empty."
    
    global user_image_url
    user_image_url = response_data["user_image_url"]

def test_update_user_image(client, content_team_headers):
    """
    Test: Update user image
    """
    with open("tests/testdata/assets/eat-fit-go-logo.png", "rb") as image_data:
        payload = {
            "image_type": "profile-picture",
            "user_image": image_data
        }
        response = do_update_user_image(client, content_team_headers, user_image_id, payload)
        assert response.status_code == 200

    response_json = json.loads(response.data)

    assert response_json["status"] == "successful"
    assert response_json["action"] == "update_user_image"

    """
    Test: Get user image
    """
    response = do_get_user_image(client, content_team_headers, user_image_id)
    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json["status"] == "successful"
    assert response_json["action"] == "get_user_image"

    response_data = response_json["data"]
    assert response_data["user_image_id"] == user_image_id

    global user_image_url
    assert response_data["user_image_url"] is not None, "User Image URL should not be empty."
    assert response_data["user_image_url"] != user_image_url, "User Image URL should have changed."

def test_get_user_images_by_user(client, content_team_headers):
    """
    Test: Get User Images
    """
    response = do_get_user_images_by_user(client, content_team_headers, user_id)
    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json["status"] == "successful"
    assert response_json["action"] == "get_user_images_by_user"
    response_data = response_json["data"]
    assert len(response_data) == 1, "User List should have 1 item."

def test_delete_user_image(client, content_team_headers):
    """
    Test: Delete User
    """
    response = do_delete_user_image(client, content_team_headers, user_image_id)
    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json["status"] == "successful"
    assert response_json["action"] == "delete_user_image"

    """
    Test: Get User List
    """
    response = do_get_user_images_by_user(client, content_team_headers, user_id)
    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json["status"] == "successful"
    assert response_json["action"] == "get_user_images_by_user"
    response_data = response_json["data"]
    assert len(response_data['user_image_list']) == 0, "User Images List should have 0 item."