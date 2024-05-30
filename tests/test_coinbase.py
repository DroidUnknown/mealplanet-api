# import json
# base_api_url = "/api"
# ##############
# # TEST - COINBASE
# ##############

# def do_create_coinbase_payment_request(client,headers):
#     payload = {
#         "payable_amount":50.00,
#         "payable_currency_id":1, #aed
#         "payment_currency_id":6, #eth
#     }
#     response = client.post(f'{base_api_url}/coinbase/charge', headers=headers,json=payload)
#     return response

# def do_coinbase_payment_charge_webhook_mock(client,data):
#     response = client.post(f'{base_api_url}/coinbase/notifications/webhook', data=json.dumps(data))
#     return response




# ##############
# # TEST-CASE
# ##############

# def test_do_create_coinbase_payment_request(client, headers):
#     response = do_create_coinbase_payment_request(client, headers)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
#     assert 'payment_address_details' in j
#     assert "addresses" in j["payment_address_details"]
#     assert "pricing" in j["payment_address_details"]


# def test_coinbase_payment_charge_webhook(client):
    
#     # payment charge initiated
#     with open('tests/testdata/coinbase/sample_payment_charge_creation_webhook_response.json') as f:
#         sample_payment_charge_creation_webhook_response = json.load(f)
#         response = do_coinbase_payment_charge_webhook_mock(client,sample_payment_charge_creation_webhook_response)
#         decoded_response = response.data.decode("utf-8")
#         assert decoded_response == "success","coinbase Payment Charge Creation webhook failed"

#     # payment charge pending
#     with open('tests/testdata/coinbase/sample_payment_charge_pending_webhook_response.json') as f:
#         sample_payment_charge_pending_webhook_response = json.load(f)
#         response = do_coinbase_payment_charge_webhook_mock(client,sample_payment_charge_pending_webhook_response)
#         decoded_response = response.data.decode("utf-8")
#         assert decoded_response == "success","coinbase Payment Charge Creation webhook failed"

#     # payment charge confirmed
#     with open('tests/testdata/coinbase/sample_payment_charge_confirmed_webhook_response.json') as f:
#         sample_payment_charge_confirmed_webhook_response = json.load(f)
#         response = do_coinbase_payment_charge_webhook_mock(client,sample_payment_charge_confirmed_webhook_response)
#         decoded_response = response.data.decode("utf-8")
#         assert decoded_response == "success","coinbase Payment Charge Creation webhook failed"

