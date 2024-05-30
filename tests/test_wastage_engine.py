import gzip
import json
from datetime import datetime, timedelta

from tests import test_item_availability_request

base_api_url = "/api"


def do_get_near_expiry_items(client, headers, facility_id):
    response = client.get(f"{base_api_url}/wastage-engine/near-expiry-items?facility_id={facility_id}", headers=headers)
    return response

def do_generate_promo_image(client, headers, count, promo_text):
    response = client.get(f"{base_api_url}/wastage-engine/generate-promo-image?count={count}", headers=headers)
    return response

def do_generate_text(client, headers, prompt):
    response = client.post(f"{base_api_url}/ai/generate-text", headers=headers, json={"prompt": prompt})
    return response

def test_e2e_wastage_engine(client, headers):
    response = test_item_availability_request.do_get_merchant_items(client, headers, 1)
    decompressed_response = gzip.decompress(response.data)

    j = json.loads(decompressed_response)
    status = j['status']
    assert status == 'successful'
    assert len(j['data']) > 0, 'No items found for merchant'
    assert j['action'] == 'get_merchant_item_list', 'Action not matching'

    item_list = j['data']

    payload_item_list = []
    selectable_hours = [5, 6, 20]
    selection_index = 0
    expected_near_expiry_items = [] # items with less than 12 hours to expiry
    for one_item in item_list:
        hours = selectable_hours[selection_index]
        selection_index = (selection_index + 1) % len(selectable_hours)

        if hours < 12:
            expected_near_expiry_items.append(one_item)

        payload_item_list.append({
            "item_id": one_item["item_id"],
            "expiry_timestamp": (datetime.now() + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S"),
            "quantity": 10
        })

    payload = {
        "facility_id": 1,
        "item_list": payload_item_list
    }
    # item id 1 and 3 are near expiry
    
    response = client.post(f"{base_api_url}/item/inventory", headers=headers, json=payload)
    assert response.status_code == 200
    response_body = json.loads(response.data)
    assert response_body['status'] == "successful"
    assert response_body['action'] == "add_item_to_inventory"

    response = client.get(f"{base_api_url}/wastage-engine/near-expiry-items?facility_id=1", headers=headers)
    assert response.status_code == 200
    response_body = json.loads(response.data)
    assert response_body['status'] == "successful"
    assert response_body['action'] == "get_near_expiry_items"
    assert len(response_body['data']['near_expiry_items']) == len(expected_near_expiry_items)

def do_launch_promotion(client, headers, payload):
    response = client.post(f"{base_api_url}/promotion/launch-promotion", headers=headers, json=payload)
    return response