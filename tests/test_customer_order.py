import json

base_api_url = "/api"

def do_create_customer_order(client, headers, payload):
    """
    Create Customer Order
    """
    response = client.post(f'{base_api_url}/customer-order', json=payload, headers=headers)
    return response

def do_calculate_order(client, headers, payload):
    """
    Calculate Customer Order
    """
    response = client.post(f'{base_api_url}/calculate-order', json=payload, headers=headers)
    return response

def do_get_customer_order(client, order_panel_headers, customer_order_id, consolidate_items_p=1):
    """
    Get Customer Order
    """
    response = client.get(f'{base_api_url}/customer-order/{customer_order_id}?consolidate_items_p={consolidate_items_p}', headers=order_panel_headers)
    return response

def do_get_customer_order_by_qrcode(client, order_panel_headers, qrcode, consolidate_items_p=1):
    """
    Get Customer Order
    """
    response = client.get(f'{base_api_url}/customer-order/qrcode?qrcode={qrcode}&consolidate_items_p={consolidate_items_p}', headers=order_panel_headers)
    return response

def do_get_customer_orders(client, order_panel_headers, payload):
    """
    Get Customer Orders
    """
    response = client.post(f'{base_api_url}/customer-orders', json=payload, headers=order_panel_headers)
    return response

def do_get_customer_order_history(client, order_panel_headers, payload):
    """
    Get Customer Order History
    """
    response = client.post(f'{base_api_url}/customer-order-history', json=payload, headers=order_panel_headers)
    return response

def do_get_customer_order_status(client, headers, customer_order_id):
    """
    Get Customer Order History
    """
    response = client.get(f'{base_api_url}/customer-order/{customer_order_id}/status', headers=headers)
    return response

def do_generate_merchant_transaction_for_customer_order(client, order_panel_headers, customer_order_id):
    """
    Generate Merchant Transaction for Customer Order
    """
    response = client.get(f'{base_api_url}/customer-order/{customer_order_id}/merchant-transaction', headers=order_panel_headers)
    return response

def do_update_customer_order(client, order_panel_headers, payload):
    """
    Update Customer Order
    """
    response = client.put(f'{base_api_url}/customer-order', json=payload, headers=order_panel_headers)
    return response

def do_cancel_customer_order(client, order_panel_headers, customer_order_id, payload):
    """
    Cancel A Customer Order
    """
    response = client.delete(f'{base_api_url}/customer-order/{customer_order_id}', json=payload, headers=order_panel_headers)
    return response

def do_print_customer_order_receipt(client, order_panel_headers, payload):
    """
    Print A Customer Order Receipt
    """
    customer_order_id = payload['customer_order_id']
    response = client.post(f'{base_api_url}/customer-order/{customer_order_id}/print-receipt', json=payload, headers=order_panel_headers)
    return response

def do_edit_customer_order(client, headers, payload, customer_order_id):
    """
    Edit Customer Order
    """
    response = client.post(f'{base_api_url}/customer-order/{customer_order_id}/edit', json=payload, headers=headers)
    return response

def do_post_customer_orders_invoice(client, headers, payload):
    """
    Post Customer Orders to Financials
    """
    response = client.post(f'{base_api_url}/customer_order_invoice', json=payload, headers=headers)
    return response

def do_update_customer_order_payment_detail(client, headers, payload, customer_order_id):
    """
    Update Customer Order Payment Method
    """
    response = client.put(f'{base_api_url}/customer-order/{customer_order_id}/payment-detail', json=payload, headers=headers)
    return response

def do_get_customer_order_stats(client, order_panel_headers, payload):
    """
    Get Customer Order Stats
    """
    response = client.post(f'{base_api_url}/customer-order-stats', json=payload, headers=order_panel_headers)
    return response

##########################
# TEST CASES
##########################

# def test_post_customer_order_invoice(client, headers):
#     """
#     Test post customer order invoice
#     """
#     payload = {
#         "customer_order_id_list": [1]
#     }
#     response = do_post_customer_orders_invoice(client, headers, payload)
#     assert response.status_code == 200
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
#     assert j["action"] == 'post_customer_order_invoice'