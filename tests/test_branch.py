import json

base_api_url = "/api"

##########################
# TEST - BRANDS
##########################
def do_get_branch_detail(client, headers, branch_id):
    """
    Get Branch Detail
    """
    response = client.get(base_api_url + f"/branch/{branch_id}", headers=headers)
    return response
    
def do_get_marketplace_menu(client, headers, branch_id, deliveroo_menu_type=None):
    """
    Get Branch Marketplace Menu
    """
    request_url = base_api_url + f"/branch/{branch_id}/marketplace-menu"
    if deliveroo_menu_type:
        request_url += "?deliveroo_menu_type=" + deliveroo_menu_type
    response = client.get(request_url, headers=headers)
    return response

def do_get_branches_by_merchant_id(client, user_headers, merchant_id):
    """
    Get Branches by Merchant ID
    """
    response = client.get(base_api_url + "/merchant/" + str(merchant_id) + "/branches", headers=user_headers)
    return response

def do_get_branches_by_merchant_id_using_filters(client, user_headers, merchant_id, payload):
    """
    Get Branches by Merchant ID
    """
    response = client.get(base_api_url + "/merchant/" + str(merchant_id) + "/branches", headers=user_headers, data=payload)
    return response

def do_get_branch_menu(client, headers, branch_id, get_availability_details=0 ):
    """
    Get Branch Menu
    """
    request_url = base_api_url + f"/branch/{branch_id}/menu"
    if get_availability_details:
        request_url += "?availability_details=1"
    response = client.get(request_url, headers=headers)
    return response

def do_get_branch_menu_v2(client, headers, branch_id, get_availability_details=0 ):
    """
    Get Branch Menu V2
    """
    request_url = base_api_url + f"/branch/{branch_id}/menu-v2"
    if get_availability_details:
        request_url += "?availability_details=1"
    response = client.get(request_url, headers=headers)
    return response

def do_get_branch_display_group_based_menu(client, headers, branch_id ):
    """
    Get Branch Display Group Based Menu
    """
    request_url = base_api_url + f"/branch/{branch_id}/display-group-menu"
    response = client.get(request_url, headers=headers)
    return response

def do_get_external_branches_by_merchant_id(client, user_headers, merchant_id, marketplace_name):
    """
    Get External Branches by Merchant ID
    """
    response = client.get(base_api_url + "/merchant/" + str(merchant_id) + "/marketplace/" + marketplace_name + "/external-branches", headers=user_headers)
    return response

def do_create_branch(client, user_headers, payload):
    """
    Create Branch
    """
    response = client.post(base_api_url + "/branch", headers=user_headers, json=payload)
    return response

def do_update_branch(client, user_headers, branch_id, payload):
    """
    Update Branch
    """
    response = client.put(base_api_url + f"/branch/{branch_id}", headers=user_headers, json=payload)
    return response

def do_get_item_categories_by_branch(client, headers, branch_id):
    """
    Get Item Categories By Branch
    """
    response = client.get(base_api_url + f"/branch/{branch_id}/item_categories", headers=headers)
    return response

def do_add_item_category_for_branches(client, headers, payload):
    """
    Add Item Category For Branches
    """
    response = client.post(base_api_url + f"/item_category", headers=headers, data=payload)
    return response

def do_edit_item_category_for_branches(client, headers, item_category_id, payload):
    """
    Edit Item Category For Branches
    """
    response = client.put(base_api_url + f"/item_category/{item_category_id}", headers=headers, data=payload)
    return response

def do_add_modifier_section_for_branches(client, headers, payload):
    """
    Add Modifier Section For Branches
    """
    response = client.post(base_api_url + f"/modifier_section", headers=headers, json=payload)
    return response

def do_edit_modifier_section_for_branches(client, headers, modifier_section_id, payload):
    """
    Edit Modifier Section For Branches
    """
    response = client.put(base_api_url + f"/modifier_section/{modifier_section_id}", headers=headers, json=payload)
    return response

def do_generate_menu(client, user_headers, branch_id):
    """
    Create Branch
    """
    response = client.post(base_api_url + f"/branch/{branch_id}/generate_menu", headers=user_headers)
    return response

def do_attach_menu_to_branch(client, user_headers, branch_id, data):
    """
    Attach Menu To Branch
    """
    response = client.post(base_api_url + f"/branch/{branch_id}/menu", headers=user_headers, json=data)
    return response

def do_get_branches(client, user_headers, args={}):
    """
    Get Branches
    """
    request_url = base_api_url + "/branches?" + "&".join([f"{k}={v}" for k, v in args.items()])
    response = client.get(request_url, headers=user_headers)
    return response

##########################
# TEST CASES
##########################
def test_get_branch_detail(client, headers):
    """
    Test get branch detail
    """
    branch_id = 2
    response = do_get_branch_detail(client, headers, branch_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_branch_detail'
    data = j["data"]
    assert data["branch_id"] == branch_id

def test_get_marketplace_menu_deliveroo(client, headers):
    """
    Test get marketplace menu Deliveroo
    """
    branch_id = 2
    delveroo_menu_type = "stock-level"
    response = do_get_marketplace_menu(client, headers, branch_id, delveroo_menu_type)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert len(j["data"]) > 0
    assert j["action"] == 'get_branch_marketplace_menu'


def test_get_marketplace_menu_careem(client, headers):
    """
    Test get marketplace menu Careem
    """
    branch_id = 3
    response = do_get_marketplace_menu(client, headers, branch_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert len(j["data"]) > 0
    assert j["action"] == 'get_branch_marketplace_menu'


def test_get_marketplace_menu_entertainer(client, headers):
    """
    Test get marketplace menu Entertainer
    """
    branch_id = 5
    response = do_get_marketplace_menu(client, headers, branch_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert len(j["data"]) > 0
    assert j["action"] == 'get_branch_marketplace_menu'


def test_get_marketplace_menu_noon(client, headers):
    """
    Test get marketplace menu Noon
    """
    branch_id = 4
    response = do_get_marketplace_menu(client, headers, branch_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert len(j["data"]) > 0
    assert j["action"] == 'get_branch_marketplace_menu'


def test_get_external_branches_by_merchant_id_careem(client, headers):
    """
    Test get external branches
    """
    merchant_id = 1
    marketplace_name = "careem"
    response = do_get_external_branches_by_merchant_id(client, headers, merchant_id, marketplace_name)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_external_branches_by_merchant'


def test_get_external_branches_by_merchant_id_noon(client, headers):
    """
    Test get external branches
    """
    merchant_id = 1
    marketplace_name = "noon"
    response = do_get_external_branches_by_merchant_id(client, headers, merchant_id, marketplace_name)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_external_branches_by_merchant'


def test_get_external_branches_by_merchant_id_deliveroo(client, headers):
    """
    Test get external branches
    """
    merchant_id = 1
    marketplace_name = "deliveroo"
    response = do_get_external_branches_by_merchant_id(client, headers, merchant_id, marketplace_name)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_external_branches_by_merchant'


def test_get_external_branches_by_merchant_id_talabat(client, headers):
    """
    Test get external branches
    """
    merchant_id = 1
    marketplace_name = "talabat"
    response = do_get_external_branches_by_merchant_id(client, headers, merchant_id, marketplace_name)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_external_branches_by_merchant'


def test_get_branches_by_merchant_id(client, headers):
    """
    Test get branches by merchant_id
    """
    merchant_id = 1
    response = do_get_branches_by_merchant_id(client, headers, merchant_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_branches_by_merchant'

def test_get_branches(client, headers):
    """
    Test get branches (ADMIN ONLY)
    """
    response = do_get_branches(client, headers)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_branches'

def test_get_branch_menu(client, headers):
    """
    Test get branch menu
    """
    branch_id = 1
    response = do_get_branch_menu(client, headers, branch_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_branch_menu'

def test_get_branch_menu_v2(client, headers):
    """
    Test get branch menu v2
    """
    branch_id = 1
    response = do_get_branch_menu_v2(client, headers, branch_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_branch_menu'

def test_create_branch(client, headers):
    """
    Test create branch
    """
    payload = {
        "merchant_third_party_credential_id": 2,
        "brand_name": "test brand 1",
        "external_brand_id": "1231512313",
        "facility_name": "al satwa",
        "marketplace_name": "careem",
        "external_branch_id": "123415131231",
        "external_branch_code": "1234512",
        "city_name": "dubai",
        "country_name": "united arab emirates",
        "latitude": 25.000,
        "longitude": 25.0000

    }
    response = do_create_branch(client, headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'create_branch'
    assert j["branch_id"], "branch id not generated"

def test_add_item_category_for_branch(client, headers):
    """
    Test add item category for branch
    """

    data = {
        "branch_id_list": "1",
        "item_category_name_en": "test item category 1",
        "item_category_name_ar": "test item category 1",
        "sequence_nr": 1,
        "sync_p": True
    }

    response = do_add_item_category_for_branches(client, headers, data)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'add_item_category_for_branch'
    assert j["item_category_id"], "item category id not generated"


def test_edit_item_category_for_branch(client, headers):
    """
    Test edit item category for branch
    """

    data = {
        "branch_id_list": "1",
        "item_category_name_en": "test item category 1",
        "item_category_name_ar": "test item category 1",
        "sequence_nr": 1,
        "sync_p": True
    }

    # get item category id
    response = do_get_item_categories_by_branch(client, headers, 1)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    item_category_id = j["item_categories"][0]["item_category"]["item_category_id"]

    response = do_edit_item_category_for_branches(client, headers, item_category_id, data)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'update_item_category_for_branch'
    assert j["item_category_id"], "item category id not generated"

def test_attach_menu_to_branch(client, headers):
    """
    Test attach menu to branch
    """
    data = {
        "menu_id": 1,
    }
    response = do_attach_menu_to_branch(client, headers, 1, data)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["branch_id"], "branch id not generated"
    assert j["action"] == 'attach_menu_to_branch'


def test_get_branches_by_merchant_id(client, headers):
    """
    Test get marketplace menu
    """
    merchant_id = 1
    payload = {
        "temp_p": 1,
        "pos_enabled_p": 1,
        "facility_id_list": 1,
        "brand_id_list": 1,
        "marketplace_id_list": 1,
        "integrated_p": 1
    }
    response = do_get_branches_by_merchant_id_using_filters(client, headers, merchant_id, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_branches_by_merchant'