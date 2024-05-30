import json
base_api_url = "/api"

##############
# TEST - PAYMENT METHOD
##############

def do_handle_payment_intent_webhook(client,data):
    """
    Handle Stripe Event Webhook
    """
    response = client.post(f'{base_api_url}/stripe/payment_intent/webhook', data=json.dumps(data))
    return response