base_api_url = "/api"

def do_get_customer_order_posting(client, headers, payload):
    """
    Get Customer Order Posting
    """
    response = client.post(f'{base_api_url}/customer-order-posting', json=payload, headers=headers)
    return response

def do_get_stock_request_posting(client, headers, payload):
    """
    Get Stock Request Posting
    """
    response = client.post(f'{base_api_url}/stock-request-posting', json=payload, headers=headers)
    return response