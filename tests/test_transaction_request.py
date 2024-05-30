import json
base_api_url = "/api"

##############
# TEST - TRANSACTION REQUEST (USED IN E2E-Tests)
##############

def do_create_payment_transaction_request(client, headers, payload):
    """
    Create Transaction Request
    """
    response = client.post(f'{base_api_url}/transaction-request', json=payload, headers=headers)
    return response


def do_update_payment_transaction_request(client, payload):
    """
    Update Transaction Tip
    """
    response = client.put(f'{base_api_url}/transaction-request', json=payload)
    return response


def do_update_payment_transaction_request_currency(client, payload):
    """
    Update Transaction Request Currency (b2binpay)
    """
    response = client.put(f'{base_api_url}/transaction-request/currency', json=payload)
    return response


def do_get_transaction_request(client, transaction_code, headers={}):
    """
    Get Transaction Request
    """
    response = client.get(f'{base_api_url}/transaction-request/{transaction_code}', headers=headers)
    return response

def do_cancel_transaction_request(client, headers, transaction_code, payload):
    """
    Cancel Transaction Request
    """
    response = client.delete(f'{base_api_url}/transaction-request/{transaction_code}', headers=headers, json=payload)
    return response
