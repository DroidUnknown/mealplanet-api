import json

base_api_url = "/api"

def do_search_items(client, headers, params=""):
    """
    Search Items
    """
    response = client.get(f'{base_api_url}/items?{params}', headers=headers)
    return response

def do_get_item(client, headers, item_id):
    """
    Get One Item
    """
    response = client.get(f'{base_api_url}/item/{item_id}', headers=headers)
    return response

def do_add_item(client, headers, payload):
    """
    Add One Item
    """
    response = client.post(f'{base_api_url}/item', data=payload, headers=headers)
    return response

def do_update_item(client, headers, item_id, payload):
    """
    Update One Item
    """
    response = client.put(f'{base_api_url}/item/{item_id}', json=payload, headers=headers)
    return response

def do_delete_item(client, headers, item_id):
    """
    Delete One Item
    """
    response = client.delete(f'{base_api_url}/item/{item_id}', headers=headers)
    return response

def do_get_item_availability_on_marketplaces(client, headers, item_id):
    """
    Get Item Availability on Marketplaces
    """
    response = client.get(f'{base_api_url}/item/{item_id}/marketplace-availability', headers=headers)
    return response

def do_edit_item_availability_on_marketplaces(client, headers, item_id, payload):
    """
    Edit Item Availability on Marketplaces
    """
    response = client.put(f'{base_api_url}/item/{item_id}/marketplace-availability', json=payload, headers=headers)
    return response

def do_get_item_availability_on_locations(client, headers, item_id):
    """
    Get Item Availability on Locations
    """
    response = client.get(f'{base_api_url}/item/{item_id}/location-availability', headers=headers)
    return response

def do_edit_item_availability_on_locations(client, headers, item_id, payload):
    """
    Edit Item Availability on Locations
    """
    response = client.put(f'{base_api_url}/item/{item_id}/location-availability', json=payload, headers=headers)
    return response

def do_upload_item_images(client, headers, item_id, payload):
    """
    Upload Item Images
    """
    response = client.post(f'{base_api_url}/item_images', json=payload, headers=headers)
    return response

def do_get_item_images(client, headers, item_id):
    """
    Get Item Images
    """
    response = client.get(f'{base_api_url}/item_images', headers=headers)
    return response

def do_delete_item_for_branch(client, headers, item_id, payload):
    """
    Delete Item for Branch
    """
    response = client.post(f'{base_api_url}/item/{item_id}', headers=headers, json=payload)
    return response

def do_update_item_on_marketplace_multiform(client, headers, item_id, marketplace_id, payload):
    """
    Update Item on Marketplace
    """
    response = client.put(f'{base_api_url}/item/{item_id}/marketplace/{marketplace_id}', data=payload, headers=headers)
    return response

def do_update_item_on_location_multiform(client, headers, item_id, facility_id, payload):
    """
    Update Item on Location
    """
    response = client.put(f'{base_api_url}/item/{item_id}/facility/{facility_id}', data=payload, headers=headers)
    return response

def do_add_item_to_inventory(client, headers, payload):
    """
    Add Item to Inventory
    """
    response = client.post(f'{base_api_url}/item/inventory', headers=headers, json=payload)
    return response

##########################
# TEST CASES
##########################

# def test_get_item_availability_on_marketplaces(client, headers):
#     """
#     Test Get Availability of Item on Marketplaces
#     """
#     response = do_get_item_availability_on_marketplaces(client, headers, 9)
#     assert response.status_code == 200
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
#     assert j["action"] == 'get_item_availability_on_marketplaces'
#     assert len(j["data"]) > 0

# def test_edit_item_availability_on_marketplaces(client, headers):
#     """
#     Test Edit Availability of Item on Marketplaces
#     """
#     payload = {
#         "marketplace_list": [
#             {
#                 "marketplace_id": 1,
#                 "excluded_p": True
#             },
#             {
#                 "marketplace_id": 2,
#                 "excluded_p": False
#             }
#         ]
#     }
#     response = do_edit_item_availability_on_marketplaces(client, headers, 9, payload)
#     assert response.status_code == 200
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
#     assert j["action"] == 'edit_item_availability_on_marketplaces'
#     assert j["data"]["is_available"] == True

# def test_get_item_availability_on_locations(client, headers):
#     """
#     Test Get Availability of Item on Locations
#     """
#     response = do_get_item_availability_on_locations(client, headers, 1)
#     assert response.status_code == 200
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
#     assert j["action"] == 'get_item_availability_on_locations'
#     assert len(j["data"]) > 0

# def test_edit_item_availability_on_locations(client, headers):
#     """
#     Test Edit Availability of Item on Locations
#     """
#     payload = {
#         "location_list": [
#             {
#                 "location_id": 1,
#                 "excluded_p": True
#             },
#             {
#                 "location_id": 2,
#                 "excluded_p": False
#             }
#         ]
#     }
#     response = do_edit_item_availability_on_locations(client, headers, 9, payload)
#     assert response.status_code == 200
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
#     assert j["action"] == 'edit_item_availability_on_locations'
#     assert j["data"]["is_available"] == True

# def test_upload_item_images(client, headers, monkeypatch):
#     """
#     Test the upload_item_images API
#     """
#     # Mock environment variables
#     monkeypatch.setenv("MOCK_S3_UPLOAD", "1")  # Mock S3 upload
#     monkeypatch.setenv("S3_BUCKET_NAME", "test_bucket")  # Your test bucket name

#     # Create a mock file for testing
#     class MockFile:
#         def __init__(self, filename):
#             self.filename = filename

#     mock_file1 = MockFile("test_image1.jpg")
#     mock_file2 = MockFile("test_image2.jpg")

#     # Mock request.files.getlist to return a list of mock file objects
#     def mock_getlist(arg):
#         if arg == "item_image_list":
#             return [mock_file1, mock_file2]
#         return []

#     # Mock the S3 upload function
#     def mock_upload_fileobj(file, bucket_name, object_key):
#         # Simulate a successful S3 upload
#         return True

#     # Apply the mocks
#     monkeypatch.setattr("item_management.os.getenv", lambda x: {
#         "MOCK_S3_UPLOAD": "1",
#         "S3_BUCKET_NAME": "test_bucket"
#     }.get(x))
#     monkeypatch.setattr("item_management.request.files.getlist", mock_getlist)
#     monkeypatch.setattr("item_management.jqimage_uploader.upload_fileobj", mock_upload_fileobj)

#     # Make the API request
#     response = do_upload_item_images(client, headers)

#     # Assertions
#     assert response.status_code == 200
#     j = json.loads(response.data)
#     assert j["status"] == "successful"
#     assert j["action"] == "upload_item_images"

# def test_get_item_images(client, headers):
#     """
#     Test Get Item Images
#     """
#     response = do_get_item_images(client, headers, 9)
#     assert response.status_code == 200
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
#     assert j["action"] == 'get_item_images'
#     assert len(j["data"]) > 0


# def test_update_item_on_marketplace(client, headers):
#     """
#     Test Update Item on Marketplace
#     """
#     payload = {
#         "branch_id": 1,
#         "brand_id": 1,
#         "item_category_id": 1,
#         "display_name_en": "Hamburger",
#         "display_name_ar": "هامبرغر",
#         "item_description_en": "Chicken Ham Burger",
#         "item_description_ar": "هامبرغر دجاج",
#         "sequence_nr": 2,
#         "item_type": None,
#         "offer_p": 0,
#         "default_price": 5.66,
#         "currency_id": 1,
#         "item_id": 9,
#         "item_image_id": None
#     }
#     response = do_update_item_on_marketplace_multiform(client, headers, 9, payload)
#     assert response.status_code == 200
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
#     assert j["action"] == 'update_item_on_marketplace'
#     assert j["data"]["item_id"] == 9

# def test_update_item_on_location(client, headers):
#     """
#     Test Update Item on Location
#     """
#     payload = {
#         "branch_id": 1,
#         "brand_id": 1,
#         "item_category_id": 1,
#         "display_name_en": "Hamburger",
#         "display_name_ar": "هامبرغر",
#         "item_description_en": "Chicken Ham Burger",
#         "item_description_ar": "هامبرغر دجاج",
#         "sequence_nr": 2,
#         "item_type": None,
#         "offer_p": 0,
#         "default_price": 5.66,
#         "currency_id": 1,
#         "item_id": 9,
#         "item_image_id": None
#     }

#     response = do_update_item_on_location_multiform(client, headers, 9, payload)
#     assert response.status_code == 200
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
#     assert j["action"] == 'update_item_on_location'
#     assert j["data"]["item_id"] == 9