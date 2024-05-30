import json

from tests.test_transaction_request import do_create_payment_transaction_request, do_get_transaction_request
from tests.test_login import do_login

base_api_url = "/api"

def do_split_bill(client, payload):
    """
    Split the bill
    """
    response = client.post(f'{base_api_url}/merchant_transaction/split', json=payload)
    return response

###########
# TESTS
###########

def test_split_bill(client, headers):
    """
    Test update merchant
    """

    response = do_login(client)
    j = json.loads(response.data)
    # Normal Transaction Request Creation
    user_headers = {
        "X-User-Id": j["user_details"]["user_id"],
        "X-Api-Key": j["merchant"]["merchant_api_key"],
        "X-Merchant-Name": j["merchant"]["merchant_name"]
    }

    file_name = "tests/testdata/payment_link_generation_payload/stripe/correct/05_all_item_types.json"
    with open(file_name) as file:
        transaction_payload = json.load(file)

    response = do_create_payment_transaction_request(client, user_headers, transaction_payload)
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert "payment_url" in j

    # Extracting transaction code from payment-link
    splitted_str_list = j["payment_url"].split("/")
    transaction_code = splitted_str_list[len(splitted_str_list)-1]

    # Get Transaction Request Details
    response = do_get_transaction_request(client, transaction_code)
    assert response.status_code == 200
    response_body = response.json

    assert response_body["status"] == 'successful'
    assert "data" in response_body
    assert "feature_list" in response_body["data"]
    assert "merchant_details" in response_body["data"]
    assert len(response_body["data"]["item_list"]) == len(transaction_payload["item_list"])
    assert len(response_body["data"]["offer_list"]) == len(transaction_payload["offer_list"])

    stripe_intent_id = response_body["data"]["stripe_intent_id"]
    merchant_transaction_id = response_body["data"]["merchant_transaction_id"]

    payload = {
        "merchant_transaction_id": merchant_transaction_id,
        "stripe_intent_id": stripe_intent_id,
        "payable_amount": 20,
        "currency_name": 'aed'
    }
    response = do_split_bill(client, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert "message" not in j, f"failed to split bill: {j['message']}"
    assert j["status"] == 'successful'
