import json
import random
import pytest

from tests import test_branch, test_item

base_api_url = "/api"

def do_get_item_display_groups(client, headers, merchant_id=None):
    """
    Get Item Display Groups
    """
    url = f'{base_api_url}/item_display_groups'
    if merchant_id:
        url += f'?merchant_id={merchant_id}'
    response = client.get(url, headers=headers)
    return response

def do_add_item_display_group(client, headers, payload):
    """
    Add One Item Display Group
    """
    response = client.post(f'{base_api_url}/item_display_group', json=payload, headers=headers)
    return response

def do_get_item_display_group(client, headers, item_display_group_id):
    """
    Get One Item Display Group
    """
    response = client.get(f'{base_api_url}/item_display_group/{item_display_group_id}', headers=headers)
    return response

def do_update_item_display_group(client, headers, item_display_group_id, payload):
    """
    Update One Item Display Group
    """
    response = client.put(f'{base_api_url}/item_display_group/{item_display_group_id}', json=payload, headers=headers)
    return response

def do_delete_item_display_group(client, headers, item_display_group_id):
    """
    Delete One Item Display Group
    """
    response = client.delete(f'{base_api_url}/item_display_group/{item_display_group_id}', headers=headers)
    return response

def do_get_item_display_groups_for_branch(client, headers, branch_id):
    """
    Get Item Display Groups for Branch
    """
    response = client.get(f'{base_api_url}/branch/{branch_id}/item_display_groups', headers=headers)
    return response

def do_add_item_display_group_to_branch(client, headers, branch_id, payload):
    """
    Add Item Display Group to Branch
    """
    response = client.post(f'{base_api_url}/branch/{branch_id}/item_display_group', json=payload, headers=headers)
    return response

def do_get_item_display_group_branch_map(client, headers, item_display_group_branch_map_id):
    """
    Get Item Display Group Branch Map
    """
    response = client.get(f'{base_api_url}/item_display_group_branch_map/{item_display_group_branch_map_id}', headers=headers)
    return response

def do_update_item_display_group_branch_map(client, headers, item_display_group_branch_map_id, payload):
    """
    Update Item Display Group Branch Map
    """
    response = client.put(f'{base_api_url}/item_display_group_branch_map/{item_display_group_branch_map_id}', json=payload, headers=headers)
    return response

def do_delete_item_display_group_branch_map(client, headers, item_display_group_branch_map_id):
    """
    Delete Item Display Group Branch Map
    """
    response = client.delete(f'{base_api_url}/item_display_group_branch_map/{item_display_group_branch_map_id}', headers=headers)
    return response

################################
# Test Cases
################################
branch_id = 1
item_display_group_id = None
item_display_group_branch_map_id = None

################################
# Test Cases
################################

def test_get_item_display_groups(client, user_headers):
    response = do_get_item_display_groups(client, user_headers)
    assert response.status_code == 200
    
    response_body = json.loads(response.data)
    assert response_body['status'] == 'successful'
    assert response_body['action'] == 'get_item_display_groups'
    
    data = response_body['data']
    assert len(data["item_display_group_list"]) > 0, "no item display groups found"

def test_add_item_display_group(client, user_headers):
    payload = {
        "parent_item_display_group_id": None,
        "display_group_name_en": "Test Display Group",
        "display_group_name_ar": "مجموعة عرض الاختبار",
        "display_group_description_en": "Test Display Group",
        "display_group_description_ar": "مجموعة عرض الاختبار"
    }
    response = do_add_item_display_group(client, user_headers, payload)
    assert response.status_code == 200
    
    response_body = json.loads(response.data)
    assert response_body['status'] == 'successful'
    assert response_body['action'] == 'add_item_display_group'
    
    data = response_body['data']
    assert data["item_display_group_id"] > 0

    global item_display_group_id
    item_display_group_id = data["item_display_group_id"]

def test_get_item_display_group(client, user_headers):
    global item_display_group_id
    assert item_display_group_id, "item_display_group_id is required for this test"
    
    response = do_get_item_display_group(client, user_headers, item_display_group_id)
    assert response.status_code == 200
    
    response_body = json.loads(response.data)
    assert response_body['status'] == 'successful'
    assert response_body['action'] == 'get_item_display_group'
    
    data = response_body['data']
    assert data["item_display_group_id"] == item_display_group_id

def test_update_item_display_group(client, user_headers):
    global item_display_group_id
    assert item_display_group_id, "item_display_group_id is required for this test"
    
    payload = {
        "parent_item_display_group_id": None,
        "display_group_name_en": "Test Display Group Updated",
        "display_group_name_ar": "Test Display Group Updated",
        "display_group_description_en": "Test Display Group Updated",
        "display_group_description_ar": "Test Display Group Updated"
    }
    response = do_update_item_display_group(client, user_headers, item_display_group_id, payload)
    assert response.status_code == 200
    
    response_body = json.loads(response.data)
    assert response_body['status'] == 'successful'
    assert response_body['action'] == 'update_item_display_group'
    
    data = response_body['data']
    assert data["item_display_group_id"] == item_display_group_id
    
    response = do_get_item_display_group(client, user_headers, item_display_group_id)
    assert response.status_code == 200
    
    response_body = json.loads(response.data)
    assert response_body['status'] == 'successful'
    assert response_body['action'] == 'get_item_display_group'
    
    data = response_body['data']
    assert data["item_display_group_id"] == item_display_group_id
    assert data["display_group_name_en"] == payload["display_group_name_en"]
    assert data["display_group_name_ar"] == payload["display_group_name_ar"]
    assert data["display_group_description_en"] == payload["display_group_description_en"]
    assert data["display_group_description_ar"] == payload["display_group_description_ar"]

def test_delete_item_display_group(client, user_headers):
    global item_display_group_id
    assert item_display_group_id, "item_display_group_id is required for this test"
    
    response = do_delete_item_display_group(client, user_headers, item_display_group_id)
    assert response.status_code == 200
    
    response_body = json.loads(response.data)
    assert response_body['status'] == 'successful'
    assert response_body['action'] == 'delete_item_display_group'
    
    data = response_body['data']
    assert data["item_display_group_id"] == item_display_group_id

    with pytest.raises(AssertionError):
        response = do_get_item_display_group(client, user_headers, item_display_group_id)
    
    item_display_group_id = None

def test_add_item_display_group_to_branch(client, user_headers):
    response = do_get_item_display_groups(client, user_headers)
    assert response.status_code == 200
    
    response_body = json.loads(response.data)
    assert response_body['status'] == 'successful'
    assert response_body['action'] == 'get_item_display_groups'
    
    data = response_body['data']
    assert len(data["item_display_group_list"]) > 0, "no item display groups found"
    
    global item_display_group_id
    item_display_group_id = data["item_display_group_list"][0]["item_display_group_id"]
    
    payload = {
        "branch_id": branch_id,
        "item_display_group_id": item_display_group_id,
        "sequence_nr": 1
    }
    response = do_add_item_display_group_to_branch(client, user_headers, branch_id, payload)
    assert response.status_code == 200
    
    response_body = json.loads(response.data)
    
    assert response_body['status'] == 'successful'
    assert response_body['action'] == 'add_item_display_group_to_branch'
    
    data = response_body['data']
    assert data["item_display_group_branch_map_id"] > 0
    
    global item_display_group_branch_map_id
    item_display_group_branch_map_id = data["item_display_group_branch_map_id"]

def test_get_item_display_groups_for_branch(client, user_headers):
    response = do_get_item_display_groups_for_branch(client, user_headers, branch_id)
    assert response.status_code == 200
    
    response_body = json.loads(response.data)
    assert response_body['status'] == 'successful'
    assert response_body['action'] == 'get_item_display_groups_for_branch'
    
    data = response_body['data']
    assert len(data["item_display_group_list"]) > 0, "no item display groups found"

def test_get_item_display_group_branch_map(client, user_headers):
    global item_display_group_branch_map_id
    assert item_display_group_branch_map_id, "item_display_group_branch_map_id is required for this test"
    
    response = do_get_item_display_group_branch_map(client, user_headers, item_display_group_branch_map_id)
    assert response.status_code == 200
    
    response_body = json.loads(response.data)
    assert response_body['status'] == 'successful'
    assert response_body['action'] == 'get_item_display_group_branch_map'
    
    data = response_body['data']
    assert data["item_display_group_branch_map_id"] == item_display_group_branch_map_id

def test_update_item_display_group_branch_map(client, user_headers):
    global item_display_group_branch_map_id, item_display_group_id
    assert item_display_group_branch_map_id, "item_display_group_branch_map_id is required for this test"
    
    payload = {
        "branch_id": branch_id,
        "item_display_group_id": item_display_group_id,
        "sequence_nr": 2
    }
    response = do_update_item_display_group_branch_map(client, user_headers, item_display_group_branch_map_id, payload)
    assert response.status_code == 200
    
    response_body = json.loads(response.data)
    assert response_body['status'] == 'successful'
    assert response_body['action'] == 'update_item_display_group_branch_map'
    
    data = response_body['data']
    assert data["item_display_group_branch_map_id"] == item_display_group_branch_map_id
    
    response = do_get_item_display_group_branch_map(client, user_headers, item_display_group_branch_map_id)
    assert response.status_code == 200
    
    response_body = json.loads(response.data)
    assert response_body['status'] == 'successful'
    assert response_body['action'] == 'get_item_display_group_branch_map'
    
    data = response_body['data']
    assert data["item_display_group_branch_map_id"] == item_display_group_branch_map_id
    assert data["sequence_nr"] == payload["sequence_nr"]

def test_e2e_display_group_based_menu(client, user_headers):
    
    # get existing branch details
    response = test_branch.do_get_branch_detail(client, user_headers, branch_id)
    assert response.status_code == 200
    
    response_body = json.loads(response.data)
    assert response_body['status'] == 'successful'
    assert response_body['action'] == 'get_branch_detail'
    
    # enable display group based menu for branch
    data = response_body['data']
    payload = {
        "menu_id": data["menu_id"],
        "auto_accept_p": data["auto_accept_p"],
        "display_group_menu_p": 1
    }
    response = test_branch.do_update_branch(client, user_headers, branch_id, payload)
    assert response.status_code == 200
    
    response_body = json.loads(response.data)
    assert response_body['status'] == 'successful'
    assert response_body['action'] == 'update_branch'

    # add item display group to branch
    payload = {
        "branch_id": branch_id,
        "item_display_group_id": 3,
        "sequence_nr": 1
    }
    response = do_add_item_display_group_to_branch(client, user_headers, branch_id, payload)
    assert response.status_code == 200

    response_body = json.loads(response.data)
    assert response_body['status'] == 'successful'
    assert response_body['action'] == 'add_item_display_group_to_branch'
    
    data = response_body['data']
    assert data["item_display_group_branch_map_id"] > 0
    
    global item_display_group_branch_map_id
    item_display_group_branch_map_id = data["item_display_group_branch_map_id"]

    # get existing menu
    response = test_branch.do_get_branch_menu_v2(client, user_headers, branch_id)
    assert response.status_code == 200
    
    response_body = json.loads(response.data)
    assert response_body['status'] == 'successful'
    assert response_body['action'] == 'get_branch_menu'
    
    data = response_body['data']
    assert len(data), "no menu category found"
    first_item_category = data[0]
    
    # Add a new item to this item category
    with open("tests/testdata/menus/item_payloads/sample_item_with_no_modifiers.json", "r") as f:
        item_payload = json.load(f)

    item_payload["external_item_id"] = random.randint(100000000, 999999999)
    item_payload["branch_id_list"] = [branch_id]
    item_payload["item_display_group_branch_map_id"] = item_display_group_branch_map_id
    item_payload["item_category_branch_map_id"] = first_item_category["item_category_branch_map_id"]
    item_payload["item_category_id"] = first_item_category["item_category_id"]
    item_payload["item_price_map_list"] = []

    data = {
        'json': json.dumps(item_payload)
    }

    # add new item
    response = test_item.do_add_item(client, user_headers, data)
    assert response.status_code == 200

    response_body = response.json
    assert response_body["status"] == "successful"
    item_id = response_body["item_id"]

    # get existing menu
    response = test_branch.do_get_branch_menu_v2(client, user_headers, branch_id)
    assert response.status_code == 200
    
    response_body = json.loads(response.data)
    assert response_body['status'] == 'successful'
    assert response_body['action'] == 'get_branch_menu'

    # get display group based menus
    response = test_branch.do_get_branch_display_group_based_menu(client, user_headers, branch_id)
    assert response.status_code == 200
    
    response_body = json.loads(response.data)
    assert response_body['status'] == 'successful'
    assert response_body['action'] == 'get_branch_display_group_based_menu'

def test_delete_item_display_group_branch_map(client, user_headers):
    global item_display_group_branch_map_id
    assert item_display_group_branch_map_id, "item_display_group_branch_map_id is required for this test"
    
    response = do_delete_item_display_group_branch_map(client, user_headers, item_display_group_branch_map_id)
    assert response.status_code == 200
    
    response_body = json.loads(response.data)
    assert response_body['status'] == 'successful'
    assert response_body['action'] == 'delete_item_display_group_branch_map'
    
    data = response_body['data']
    assert data["item_display_group_branch_map_id"] == item_display_group_branch_map_id

    with pytest.raises(AssertionError):
        response = do_get_item_display_group_branch_map(client, user_headers, item_display_group_branch_map_id)
    
    item_display_group_branch_map_id = None