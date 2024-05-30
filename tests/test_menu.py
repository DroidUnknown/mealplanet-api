import json

from tests.test_branch import do_get_marketplace_menu
from utils import jqutils
from sqlalchemy.sql import text

base_api_url = "/api"

##########################
# TEST - BRANDS
##########################
def do_upload_brand_menu_items(client, headers, payload):
    """
    Get Upload brand menu items
    """
    response = client.post(base_api_url + "/menu/brand_menu_items", headers=headers, json=payload)
    return response

def do_add_menu(client, headers, payload):
    """
    Get Add menu
    """
    response = client.post(base_api_url + "/menu", headers=headers, json=payload)
    return response

def do_get_menu(client, headers, menu_id):
    """
    Get menu
    """
    response = client.get(base_api_url + f"/menu/{menu_id}", headers=headers)
    return response

def do_get_menus(client, headers, payload):
    """
    Get menus
    """
    response = client.get(base_api_url + "/menus", headers=headers)
    return response

def do_update_menu(client, headers, menu_id, payload):
    """
    Get update menu
    """
    response = client.put(base_api_url + f"/menu/{menu_id}", headers=headers, json=payload)
    return response

def do_delete_menu(client, headers, menu_id):
    """
    Get delete menu
    """
    response = client.delete(base_api_url + f"/menu/{menu_id}", headers=headers)
    return response

##########################
# TEST CASES
##########################

def test_upload_brand_menu_items(client, headers):
    """
    Test upload brand menu
    """
    menu = do_get_marketplace_menu(client, headers, 1)
    menu_payload = json.loads(menu.data)

    response = do_upload_brand_menu_items(client, headers, menu_payload['data'])
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'upload_menu_items'

def test_add_menu(client, headers):
    """
    Test add menu
    """
    payload = {
        "merchant_id": 1,
        "menu_name": "event menu",
        "menu_description": "event menu description"
    }

    response = do_add_menu(client, headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'add_menu'

def test_get_menu(client, headers):
    """
    Test get menu
    """
    db_engine = jqutils.get_db_engine()

    query = text("""
        SELECT menu_id
        FROM menu
        WHERE menu_name = :menu_name
        AND menu_description = :menu_description
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, menu_name="event menu", menu_description="event menu description").fetchone()

    menu_id = result['menu_id']
    
    response = do_get_menu(client, headers, menu_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_menu'

def test_get_menus(client, headers):
    """
    Test get menus
    """
    response = do_get_menus(client, headers, {})
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_menus'

def test_update_menu(client, headers):
    """
    Test update menu
    """
    payload = {
        "menu_name": "schedule menu",
        "menu_description": "schedule menu description"
    }

    response = do_update_menu(client, headers, 1, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'update_menu'

def test_delete_menu(client, headers):
    """
    Test delete menu
    """
    response = do_delete_menu(client, headers, 1)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'delete_menu'