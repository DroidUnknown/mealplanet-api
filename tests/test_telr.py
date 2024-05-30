import json
base_api_url = "/api"

##############
# TEST - PAYMENT METHOD
##############

def do_handle_transaction_request_webhook(client,data):
    """
    Handle Telr Event Webhook
    """
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    response = client.post(f'{base_api_url}/telr/payment-request/webhook', headers=headers, data=data)
    return response