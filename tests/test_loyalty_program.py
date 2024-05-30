import json

base_api_url = "/api"

##########################
# TEST - Loyalty Program
##########################

def do_get_customer_loyalty_point_balance(client, headers, customer_id):
    """
    Get customer loyalty point balance
    """
    response = client.get(base_api_url + f"/customer/{customer_id}/loyalty_point_balance", headers=headers)
    return response

def do_get_customer_loyalty_point_ledger(client, headers, customer_id):
    """
    Get customer loyalty point ledger entries
    """
    response = client.get(base_api_url + f"/customer/{customer_id}/loyalty_point_ledger", headers=headers)
    return response

def do_get_merchant_loyalty_program_config(client, headers, merchant_id):
    """
    Get merchant loyalty program configs
    """
    response = client.get(base_api_url + f"/merchant/{merchant_id}/loyalty_program_configs", headers=headers)
    return response

def do_update_merchant_loyalty_program_config(client, headers, merchant_id, data):
    """
    Update merchant loyalty program config
    """
    response = client.put(base_api_url + f"/merchant/{merchant_id}/loyalty_program_config", headers=headers, json=data)
    return response