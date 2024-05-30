base_api_url = "/api"

##########################
# TEST - Printer Models
########################## 
def do_get_printer_models(client,user_headers):
    """
    Get Printer Models
    """
    response = client.get(base_api_url + "/printer-models", headers=user_headers)
    return response

def do_add_printer_to_facility(client, user_headers, facility_id, data):
    """
    Add Printer to Facility
    """
    response = client.post(base_api_url + "/facility/" + str(facility_id) + "/printer", json=data, headers=user_headers)
    return response

def do_get_printers_by_merchant_id(client, user_headers, merchant_id):
    """
    Get Printers by Merchant ID
    """
    response = client.get(base_api_url + "/merchant/" + str(merchant_id) + "/printers", headers=user_headers)
    return response    

def do_get_printers_by_facility_id(client,user_headers,facility_id):
    """
    Get Printers by Facility ID
    """
    response = client.get(base_api_url + "/facility/" + str(facility_id) + "/printers", headers=user_headers)
    return response

def do_get_printer(client,user_headers,printer_id):
    """
    Get Printer
    """
    response = client.get(base_api_url + "/printer/" + str(printer_id), headers=user_headers)
    return response

def do_update_printer(client,user_headers,data,printer):
    """
    Update Printer
    """
    response = client.put(base_api_url + "/printer/" + str(printer), json=data, headers=user_headers)
    return response

def do_delete_printer(client,user_headers,printer_id):
    """
    Delete Printer
    """
    response = client.delete(base_api_url + "/printer/" + str(printer_id), headers=user_headers)
    return response

def do_search_printer(client,user_headers):
    """
    Search Printer
    """
    response = client.get(base_api_url + "/printers", headers=user_headers)
    return response

###########
# TESTS
###########

def test_get_printers_by_faciity_id(client, user_headers):
    """
    Test Get Printers by Facility ID
    """

    # Get Printers by Facility ID
    response = do_get_printers_by_facility_id(client, user_headers, 1)
    assert response.json['status'] == 'successful'

def test_get_printer(client,user_headers):
    """
    Test Get Printer
    """

    # Get Printer
    response = do_get_printer(client, user_headers, 2)
    assert response.json['status'] == 'successful'

def test_update_printer(client,user_headers):

    # Get Printer
    
    # Update Printer
    data = {
        "printer_name": "Test Printer Updated",
        "printer_description": "Test Printer Updated by user",
        "printer_ip_address": "127.0.0.1",
        "printer_port_number":23,
        "printer_status": "active"
    }        
    response = do_update_printer(client, user_headers, data, 2)
    assert response.json['status'] == 'successful'

def test_delete_printer(client,user_headers):
    """
    Test Delete Printer
    """

    # Delete Printer
    response = do_delete_printer(client, user_headers, 2)
    assert response.json['status'] == 'successful'

def test_search_printer(client,user_headers):
    """
    Test Search Printer
    """

    # Search Printer
    response = do_search_printer(client, user_headers)
    assert response.json['status'] == 'successful'    