import json

base_api_url = "/api"

def do_get_merchant_kitchen_display_system_config(client, headers, merchant_id):
    """
    Get Kitchen Display System Config for Merchant
    """
    response = client.get(f'{base_api_url}/merchant/{merchant_id}/kitchen-display-system-config', headers=headers)
    return response

def do_update_merchant_kitchen_display_system_config(client, headers, merchant_id, data):
    """
    Update Kitchen Display System Config for Merchant
    """
    response = client.put(f'{base_api_url}/merchant/{merchant_id}/kitchen-display-system-config', headers=headers, json=data)
    return response

##########################
# TEST CASES
##########################

def test_get_merchant_kitchen_display_system_config(client, headers):
    """
    Get Merchant Kitchen Display System Config
    """
    response = do_get_merchant_kitchen_display_system_config(client, headers, 1)
    assert response.status_code == 200
    response_body = json.loads(response.data)
    assert response_body["status"] == "successful"
    assert response_body["action"] == "get_kitchen_display_system_config"
    assert response_body["data"]["merchant_id"] == 1

def test_update_merchant_kitchen_display_system_config(client, headers):
    """
    Update Merchant Kitchen Display System Config
    """
    data = {
        "click_card_to_complete_p": True,
        "show_arabic_p": False,
        "card_per_order": 1,
        "card_per_screen": 1,
        "consolidate_view_p": True,
        "card_color_config": {},
        "header_config": {}
    }
    response = do_update_merchant_kitchen_display_system_config(client, headers, 1, data)
    assert response.status_code == 200
    response_body = json.loads(response.data)
    assert response_body["status"] == "successful"
    assert response_body["data"]["merchant_id"] == 1