import json

base_api_url = "/api"

###############################
# TEST - MERCHANT BILLING
###############################

def do_get_merchant_billing_alerts(client, headers):
    """
    Get Merchant Billing Alerts
    """
    response = client.get(f'{base_api_url}/merchant-billing-alerts', headers=headers)
    return response

def do_get_merchant_billing_alert(client, headers, merchant_id):
    """
    Get Merchant Billing Alert
    """
    response = client.get(f'{base_api_url}/merchant/{merchant_id}/billing-alert', headers=headers)
    return response

def do_update_merchant_billing_alert(client, headers, merchant_id, payload):
    """
    Update Merchant Billing Alert
    """
    response = client.put(f'{base_api_url}/merchant/{merchant_id}/billing-alert', headers=headers, json=payload)
    return response

####################
# GLOBALS
####################
merchant_id = None
merchant_billing_alert_id = None

####################
# TEST CASES
####################

def test_get_merchant_billing_alerts(client, headers):
    """
    Test get merchant billing alerts
    """
    response = do_get_merchant_billing_alerts(client, headers)
    assert response.status_code == 200
    assert response.json['status'] == 'successful'
    assert response.json['action'] == 'get_merchant_billing_alerts'
    
    merchant_billing_alert_list = response.json['data']
    assert len(merchant_billing_alert_list) > 0, "No merchant billing alerts found"
    
    global merchant_id, merchant_billing_alert_id
    merchant_id = merchant_billing_alert_list[0]['merchant']['merchant_id']
    merchant_billing_alert_id = merchant_billing_alert_list[0]['merchant_billing_alert_id']

def test_get_merchant_billing_alert(client, user_headers):
    """
    Test get merchant billing alert
    """
    global merchant_id
    response = do_get_merchant_billing_alert(client, user_headers, merchant_id)
    assert response.status_code == 200
    assert response.json['status'] == 'successful'
    assert response.json['action'] == 'get_merchant_billing_alert'

def test_update_merchant_billing_alert(client, user_headers):
    """
    Test update merchant billing alert
    """
    global merchant_id
    payload = {
        "trial_start_date": "2022-01-01",
        "trial_end_date": "2022-01-31",
        "billing_start_date": "2022-02-01",
        "alert_type": "yellow",
        "screen_alert_status": "active",
        "override_alert_p": 0,
        "billing_suspend_p": 0,
        "account_suspend_p": 0
    }
    response = do_update_merchant_billing_alert(client, user_headers, merchant_id, payload)
    assert response.status_code == 200
    assert response.json['status'] == 'successful'
    assert response.json['action'] == 'update_merchant_billing_alert'
    
    merchant_billing_alert = response.json['data']
    
    response = do_get_merchant_billing_alert(client, user_headers, merchant_id)
    assert response.status_code == 200
    assert response.json['status'] == 'successful'
    assert response.json['action'] == 'get_merchant_billing_alert'
    
    merchant_billing_alert = response.json['data']
    
    assert merchant_billing_alert['trial_start_date'] == payload['trial_start_date']
    assert merchant_billing_alert['trial_end_date'] == payload['trial_end_date']
    assert merchant_billing_alert['billing_start_date'] == payload['billing_start_date']
    assert merchant_billing_alert['alert_type'] == payload['alert_type']
    assert merchant_billing_alert['screen_alert_status'] == payload['screen_alert_status']
    assert merchant_billing_alert['override_alert_p'] == payload['override_alert_p']
    assert merchant_billing_alert['billing_suspend_p'] == payload['billing_suspend_p']
    assert merchant_billing_alert['account_suspend_p'] == payload['account_suspend_p']