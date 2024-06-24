import json
import pytest

from sqlalchemy import text
from utils import jqutils

base_api_url = "/api"

##############################
# TEST - BRAND PROFILE IMAGE
##############################
def do_add_brand_profile_image(client, headers, payload):
    """
    Add brand profile image
    """
    cand_headers = headers.copy()
    cand_headers["Content-Type"] = "multipart/form-data"
    response = client.post(base_api_url + "/brand-profile-image", headers=cand_headers, data=payload)
    return response

def do_get_brand_profile_image(client, headers, brand_profile_image_id):
    """
    Get brand profile image
    """
    response = client.get(base_api_url + f"/brand-profile-image/{brand_profile_image_id}", headers=headers)
    return response

def do_get_brand_profile_images_by_brand_profile(client, headers, brand_profile_id):
    """
    Get brand profile images by brand profile
    """
    response = client.get(base_api_url + f"/brand-profile/{brand_profile_id}/images", headers=headers)
    return response

def do_update_brand_profile_image(client, headers, brand_profile_image_id, payload):
    """
    Update brand profile image
    """
    cand_headers = headers.copy()
    cand_headers["Content-Type"] = "multipart/form-data"
    response = client.put(base_api_url + f"/brand-profile-image/{brand_profile_image_id}", headers=headers, data=payload)
    return response

def do_delete_brand_profile_image(client, headers, brand_profile_image_id):
    """
    Delete brand profile image
    """
    response = client.delete(base_api_url + f"/brand-profile-image/{brand_profile_image_id}", headers=headers)
    return response

##########################
# GLOBALS
########################## 
brand_profile_id = 3
brand_profile_image_id = None
brand_profile_image_url = None

##########################
# FIXTURES
##########################
@pytest.fixture(scope="module", autouse=True)
def existing_brand_profile_image_count():
    db_engine = jqutils.get_db_engine()
    
    query = text("""
        SELECT COUNT(1) AS cnt
        FROM brand_profile_image
        WHERE brand_profile_id = :brand_profile_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, brand_profile_id=brand_profile_id, meta_status="active").fetchone()
        return result["cnt"]

##########################
# TEST CASES
########################## 
def test_add_brand_profile_image(client, content_team_headers):
    """
    Test: Add brand profile image
    """
    
    with open("tests/testdata/assets/prep-and-co-logo.png", "rb") as image_data:
        payload = {
            "brand_profile_id": brand_profile_id,
            "image_type": "main-logo",
            "brand_profile_image": image_data
        }
        response = do_add_brand_profile_image(client, content_team_headers, payload)
        assert response.status_code == 200

    response_json = response.get_json()
    assert response_json["status"] == "successful"
    assert response_json["action"] == "add_brand_profile_image"

    global brand_profile_image_id
    response_data = response_json["data"]
    brand_profile_image_id = response_data["brand_profile_image_id"]

def test_get_brand_profile_image(client, content_team_headers):
    """
    Test: Get brand profile image
    """
    response = do_get_brand_profile_image(client, content_team_headers, brand_profile_image_id)
    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json["status"] == "successful"
    assert response_json["action"] == "get_brand_profile_image"

    response_data = response_json["data"]
    assert response_data["brand_profile_image_id"] == brand_profile_image_id
    assert response_data["image_type"] == "main-logo"
    assert response_data["brand_profile_image_url"] is not None, "Brand Profile Image URL should not be empty."
    
    global brand_profile_image_url
    brand_profile_image_url = response_data["brand_profile_image_url"]

def test_update_brand_profile_image(client, content_team_headers):
    """
    Test: Update brand profile image
    """
    with open("tests/testdata/assets/eat-fit-go-logo.png", "rb") as image_data:
        payload = {
            "image_type": "main-logo",
            "brand_profile_image": image_data
        }
        response = do_update_brand_profile_image(client, content_team_headers, brand_profile_image_id, payload)
        assert response.status_code == 200

    response_json = json.loads(response.data)

    assert response_json["status"] == "successful"
    assert response_json["action"] == "update_brand_profile_image"

    """
    Test: Get brand profile image
    """
    response = do_get_brand_profile_image(client, content_team_headers, brand_profile_image_id)
    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json["status"] == "successful"
    assert response_json["action"] == "get_brand_profile_image"

    response_data = response_json["data"]
    assert response_data["brand_profile_image_id"] == brand_profile_image_id

    global brand_profile_image_url
    assert response_data["brand_profile_image_url"] is not None, "Brand Profile Image URL should not be empty."
    assert response_data["brand_profile_image_url"] != brand_profile_image_url, "Brand Profile Image URL should have changed."

def test_get_brand_profile_images_by_brand_profile(client, content_team_headers):
    """
    Test: Get Brand Profile Images
    """
    response = do_get_brand_profile_images_by_brand_profile(client, content_team_headers, brand_profile_id)
    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json["status"] == "successful"
    assert response_json["action"] == "get_brand_profile_images_by_brand_profile"
    response_data = response_json["data"]
    assert len(response_data) == 1, "Brand Profile List should have 1 item."

def test_delete_brand_profile_image(client, content_team_headers):
    """
    Test: Delete Brand Profile
    """
    response = do_delete_brand_profile_image(client, content_team_headers, brand_profile_image_id)
    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json["status"] == "successful"
    assert response_json["action"] == "delete_brand_profile_image"

    """
    Test: Get Brand Profile List
    """
    response = do_get_brand_profile_images_by_brand_profile(client, content_team_headers, brand_profile_id)
    assert response.status_code == 200
    response_json = json.loads(response.data)
    assert response_json["status"] == "successful"
    assert response_json["action"] == "get_brand_profile_images_by_brand_profile"
    response_data = response_json["data"]
    assert len(response_data['brand_profile_image_list']) == 0, "Brand Profile Images List should have 0 item."