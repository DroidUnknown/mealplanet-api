# import json

base_api_url = "/api"

# import b2binpay_management.b2binpay_ninja as b2binpay_ninja

# def do_create_invoice(wallet_details, commission_details, merchant_transaction_code payment_link_expiry_seconds):
#     invoice = b2binpay_ninja.create_b2binpay_invoice(wallet_details, commission_details, merchant_transaction_code, payment_link_expiry_seconds)
#     return invoice


# def do_create_payment_request(merchant_details, customer_details, payment_details, service_provider_details, transaction_details, payment_point_details, payment_link_expiry_seconds):
#     payment_request = b2binpay_ninja.create_payment_request_by_b2binpay(merchant_details, customer_details, payment_details, service_provider_details,
#                                                                         transaction_details, payment_point_details, payment_link_expiry_seconds)
#     return payment_request


def do_handle_invoice_webhook(client, payload):
    """
    Get b2binpay invoice webhook
    """
    response = client.post(base_api_url + "/b2binpay/webhook/invoice", json=payload)
    return response


# def test_get_access_token():
#     """
#     Test get access token
#     """
#     access_token = b2binpay_ninja.get_access_token()
#     assert access_token


# def test_create_invoice():
#     """
#     Test create invoice
#     """
#     wallet_details = {"external_wallet_id": 1}
#     commission_details = {"payable_amount": 500, "currency_id": 1}
#     payment_link_expiry_seconds = 50

#     invoice = do_create_invoice(wallet_details, commission_details, payment_link_expiry_seconds)
#     assert invoice

# def test_create_payment_request_by_b2binpay():
#     """
#     Test create payment request
#     """
#     with open("tests/testdata/b2binpay/create_invoice_payload.json") as file:
#         payload = json.load(file)
#     payment_request = do_create_payment_request(payload['merchant_details'], payload['customer_details'], payload['payment_details'],
#                                                 payload['service_provider_details'], payload['transaction_details'], payload['payment_point_details'],
#                                                 payload['payment_link_expiry_seconds'])
#     assert payment_request
