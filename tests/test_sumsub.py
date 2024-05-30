import hashlib
import json
import hmac
import os

from dotenv import load_dotenv

from tests.test_merchant import do_add_merchant_and_user

base_api_url = "/api"

load_dotenv()

sumsub_app_secret = os.getenv('SUMSUB_APP_SECRET').encode('utf-8')

def do_get_sumsub_access_token(client, headers):
    """
    Get Sumsub Access Token For SDK Use
    """
    response = client.get(f'{base_api_url}/sumsub/access_token', headers=headers)
    return response

def do_test_sumsub_webhook(client, headers, payload):
    """
    Test Sumsub Webhook
    """
    response = client.post(f'{base_api_url}/sumsub/webhook', headers=headers, json=payload)
    return response

################
# TEST CASES
################

def test_get_sumsub_access_token(client, headers):
    """
    Test Get Sumsub Access Token For SDK Use
    """
    response = do_get_sumsub_access_token(client, headers)
    assert response.status_code == 200
    assert response.json['status'] == 'skip_sumsub'
    assert response.json['action'] == 'get_sumsub_access_token'

def test_sumsub_approved_webhook(client, headers):
    """
    Test sumsub webhook for user verification approved
    """
    logged_in_user_details, merchant_settings, logged_in_order_panel_details, logged_in_marketplace_details = do_add_merchant_and_user(client)

    with open("tests/testdata/sumsub/webhook/sample_approved_webhook.json",  "r") as file:
        payload = json.load(file)
    payload['externalUserId'] = logged_in_user_details['user_id']

    payload = dict(sorted(payload.items()))
    request_payload = bytes(json.dumps(payload), 'utf-8')
    signature_computed = hmac.new(sumsub_app_secret, request_payload, hashlib.sha1).hexdigest()

    headers['x-payload-digest'] = signature_computed

    response = do_test_sumsub_webhook(client, headers, payload)
    assert response.status_code == 200
    assert response.json['status'] == 'successful'
    assert response.json['action'] == 'handle_sumsub_webhook'

def test_sumsub_rejected_webhook(client, headers):
    """
    Test sumsub webhook for user verification rejected
    """

    logged_in_user_details, merchant_settings, logged_in_order_panel_details, logged_in_marketplace_details = do_add_merchant_and_user(client)

    with open("tests/testdata/sumsub/webhook/sample_rejected_webhook.json",  "r") as file:
        payload = json.load(file)
    payload['externalUserId'] = logged_in_user_details['user_id']

    payload = dict(sorted(payload.items()))
    payload['reviewResult'] = dict(sorted(payload['reviewResult'].items()))
    request_payload = bytes(json.dumps(payload), 'utf-8')

    signature_computed = hmac.new(sumsub_app_secret, request_payload, hashlib.sha1).hexdigest()

    headers['x-payload-digest'] = signature_computed

    response = do_test_sumsub_webhook(client, headers, payload)
    assert response.status_code == 200
    assert response.json['status'] == 'successful'
    assert response.json['action'] == 'handle_sumsub_webhook'
