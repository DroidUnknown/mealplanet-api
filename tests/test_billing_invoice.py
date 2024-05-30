base_api_url = "/api"

###############################
# TEST - BILLING INVOICE
###############################
def do_get_billing_invoices(client, headers):
    """
    Get Billing Invoices
    """
    response = client.get(f'{base_api_url}/billing-invoices', headers=headers)
    return response

def do_get_billing_invoice_detail(client, headers, billing_invoice_id):
    """
    Get Billing Invoice Detail
    """
    response = client.get(f'{base_api_url}/billing-invoice/{billing_invoice_id}/detail', headers=headers)
    return response

def do_cancel_billing_invoice(client, headers, billing_invoice_id):
    """
    Cancel Billing Invoice
    """
    response = client.delete(f'{base_api_url}/billing-invoice/{billing_invoice_id}', headers=headers)
    return response

####################
# GLOBALS
####################
billing_invoice_id = None

####################
# TEST CASES
####################
def test_get_billing_invoices(client, headers):
    """
    Test get billing invoices
    """
    response = do_get_billing_invoices(client, headers)
    assert response.status_code == 200
    assert response.json['status'] == 'successful'
    assert response.json['action'] == 'get_billing_invoices'
    
    billing_invoice_list = response.json['data']
    assert len(billing_invoice_list) > 0, "No billing invoices found"
    
    global billing_invoice_id
    billing_invoice_id = billing_invoice_list[0]['billing_invoice_id']

def test_get_billing_invoice_detail(client, headers):
    """
    Test get billing invoice detail
    """
    global billing_invoice_id
    response = do_get_billing_invoice_detail(client, headers, billing_invoice_id)
    assert response.status_code == 200
    assert response.json['status'] == 'successful'
    assert response.json['action'] == 'get_billing_invoice_detail'
    assert response.json['data']['billing_invoice_id'] == billing_invoice_id

def test_cancel_billing_invoice(client, headers):
    """
    Test cancel billing invoice
    """
    global billing_invoice_id
    response = do_cancel_billing_invoice(client, headers, billing_invoice_id)
    assert response.status_code == 200
    assert response.json['status'] == 'successful'
    assert response.json['action'] == 'cancel_billing_invoice'
    assert response.json['data']['billing_invoice_id'] == billing_invoice_id