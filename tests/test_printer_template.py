import pytest

base_api_url = "/api"

####################
# PRINTER TEMPLATES
####################
def do_get_printer_templates(client, user_headers):
    """
    Get Printer templates
    """
    response = client.get(base_api_url + "/printer-templates", headers=user_headers)
    return response

def do_add_printer_template(client, user_headers, data):
    """
    Add Printer Template
    """
    response = client.post(base_api_url + "/printer-template", json=data, headers=user_headers)
    return response

def do_get_printer_template(client, user_headers, printer_template_id):
    """
    Get Printer Template
    """
    response = client.get(base_api_url + "/printer-template/" + str(printer_template_id), headers=user_headers)
    return response    

def do_update_printer_template(client, user_headers, printer_template_id, data):
    """
    Update Printer Template
    """
    response = client.put(base_api_url + "/printer-template/" + str(printer_template_id), headers=user_headers, json=data)
    return response

def do_delete_printer_template(client, user_headers, printer_template_id):
    """
    Delete Printer Template
    """
    response = client.delete(base_api_url + "/printer-template/" + str(printer_template_id), headers=user_headers)
    return response

##########################
# PRINTER FACILITY CONFIG
##########################
def do_add_printer_facility_config(client, user_headers, data):
    """
    Add Printer Facility Config
    """
    response = client.post(base_api_url + "/printer-facility-config", headers=user_headers, json=data)
    return response

#################
# PRINTER RULES
#################
def do_get_printer_rules(client, user_headers, printer_id=None):
    """
    Get Printer Rules
    """
    request_url = base_api_url + "/printer-rules"
    if printer_id:
        request_url += "?printer_id=" + str(printer_id)
    response = client.get(request_url, headers=user_headers)
    return response

def do_add_printer_rule(client, user_headers, data):
    """
    Add Printer Rule
    """
    response = client.post(base_api_url + "/printer-rule", headers=user_headers, json=data)
    return response

def do_update_printer_rule(client, user_headers, printer_rule_id, data):
    """
    Update Printer Rule
    """
    response = client.put(base_api_url + "/printer-rule/" + str(printer_rule_id), headers=user_headers, json=data)
    return response

def do_delete_printer_rule(client, user_headers, printer_rule_id):
    """
    Delete Printer Rule
    """
    response = client.delete(base_api_url + "/printer-rule/" + str(printer_rule_id), headers=user_headers)
    return response

##########################
# PRINTER TEMPLATE RULES
##########################
def do_get_printer_template_rules(client, user_headers, printer_template_id=None):
    """
    Get Printer Template Rules
    """
    request_url = base_api_url + "/printer-template-rules"
    if printer_template_id:
        request_url += "?printer_template_id=" + str(printer_template_id)
    response = client.get(request_url, headers=user_headers)
    return response

def do_add_printer_template_rule(client, user_headers, data):
    """
    Add Printer Template Rule
    """
    response = client.post(base_api_url + "/printer-template-rule", headers=user_headers, json=data)
    return response

def do_update_printer_template_rule(client, user_headers, printer_template_rule_id, data):
    """
    Update Printer Template Rule
    """
    response = client.put(base_api_url + "/printer-template-rule/" + str(printer_template_rule_id), headers=user_headers, json=data)
    return response

def do_delete_printer_template_rule(client, user_headers, printer_template_rule_id):
    """
    Delete Printer Template Rule
    """
    response = client.delete(base_api_url + "/printer-template-rule/" + str(printer_template_rule_id), headers=user_headers)
    return response

###########
# FIXTURES
###########
@pytest.fixture(scope="module", autouse=True)
def template_content():
    with open("tests/testdata/printer_templates/template-customer-1.txt", "r", encoding="utf-8") as file:
        customer_template_content = file.read()
    with open("tests/testdata/printer_templates/template-kot-1.txt", "r", encoding="utf-8") as file:
        kot_template_content = file.read()
    
    return {
        "customer": customer_template_content,
        "kot": kot_template_content
    }

###########
# GLOBALS
###########
printer_template_id = None
printer_rule_id = None

###########
# TESTS
###########

def test_get_printer_templates(client, user_headers):
    """
    Test Get Printer Templates
    """
    response = do_get_printer_templates(client, user_headers)
    assert response.status_code == 200
    
    response_body = response.json
    assert response_body["status"] == "successful"
    assert response_body["action"] == "get_printer_templates"
    
    data = response_body["data"]
    assert len(data) > 0, "no printer templates found"

def test_add_printer_template(client, user_headers, template_content):
    """
    Test Add Printer Template
    """
    data = {
        "printer_template_type": "customer",
        "printer_template_name": "Test Printer Template",
        "printer_template_description": "Test Printer Template Description",
        "printer_template_content": template_content["customer"]
    }
    response = do_add_printer_template(client, user_headers, data)
    assert response.status_code == 200
    
    response_body = response.json
    assert response_body["status"] == "successful"
    assert response_body["action"] == "add_printer_template"
    
    data = response_body["data"]
    assert data["printer_template_id"] > 0, "printer template id is invalid"

    global printer_template_id
    printer_template_id = data["printer_template_id"]

def test_get_printer_template(client, user_headers, template_content):
    """
    Test Get Printer Template
    """
    global printer_template_id
    assert printer_template_id is not None, "printer_template_id is not set"
    
    response = do_get_printer_template(client, user_headers, printer_template_id)
    assert response.status_code == 200
    
    response_body = response.json
    assert response_body["status"] == "successful"
    assert response_body["action"] == "get_printer_template"
    
    data = response_body["data"]
    assert data["printer_template_id"] == printer_template_id, "printer template id is invalid"
    
    assert data["printer_template_content"] == template_content["customer"], "printer template content is invalid"

def test_update_printer_template(client, user_headers, template_content):
    """
    Test Update Printer Template
    """
    global printer_template_id
    assert printer_template_id is not None, "printer_template_id is not set"
    
    data = {
        "printer_template_type": "customer",
        "printer_template_name": "Test Printer Template Updated",
        "printer_template_description": "Test Printer Template Description Updated",
        "printer_template_content": template_content["customer"]
    }
    response = do_update_printer_template(client, user_headers, printer_template_id, data)
    assert response.status_code == 200
    
    response_body = response.json
    assert response_body["status"] == "successful"
    assert response_body["action"] == "update_printer_template"
    
    data = response_body["data"]
    assert data["printer_template_id"] == printer_template_id, "printer template id is invalid"

def test_add_printer_facility_config(client, user_headers):
    """
    Test Add Printer Facility Config
    """
    data = {
        "facility_id": 1,
        "brand_id": None,
        "printer_template_id": printer_template_id,
        "printer_id": 1,
        "printer_facility_config_name": "Test Printer Facility Config",
        "printer_facility_config_description": "Test Printer Facility Config Description",
        "print_type": "customer"
    }
    response = do_add_printer_facility_config(client, user_headers, data)
    assert response.status_code == 200
    
    response_body = response.json
    assert response_body["status"] == "successful"
    assert response_body["action"] == "add_printer_facility_config"
    
    data = response_body["data"]
    assert data["printer_facility_config_id"] > 0, "printer facility config id is invalid"

def test_get_printer_rules(client, user_headers):
    """
    Test Get Printer Rules
    """
    response = do_get_printer_rules(client, user_headers)
    assert response.status_code == 200
    
    response_body = response.json
    assert response_body["status"] == "successful"
    assert response_body["action"] == "get_printer_rules"
    
    data = response_body["data"]
    assert len(data) > 0, "no printer rules found"

def test_add_printer_rule(client, user_headers):
    """
    Test Add Printer Rule
    """
    data = {
        "printer_id": 1,
        "rule_type": "customer-receipt",
        "printer_template_id": printer_template_id, 
        "printer_rule_expression": "facility(1)"
    }
    response = do_add_printer_rule(client, user_headers, data)
    assert response.status_code == 200
    
    response_body = response.json
    assert response_body["status"] == "successful"
    assert response_body["action"] == "add_printer_rule"
    
    data = response_body["data"]
    assert data["printer_rule_id"] > 0, "printer rule id is invalid"
    
    global printer_rule_id
    printer_rule_id = data["printer_rule_id"]

def test_update_printer_rule(client, user_headers):
    """
    Test Update Printer Rule
    """
    global printer_rule_id
    assert printer_rule_id is not None, "printer_rule_id is not set"
    
    data = {
        "rule_type": "printing",
        "printer_template_id": printer_template_id,
        "printer_rule_expression": "facility(1)"
    }
    response = do_update_printer_rule(client, user_headers, printer_rule_id, data)
    assert response.status_code == 200
    
    response_body = response.json
    assert response_body["status"] == "successful"
    assert response_body["action"] == "update_printer_rule"
    
    data = response_body["data"]
    assert data["printer_rule_id"] == printer_rule_id, "printer rule id is invalid"

def test_get_printer_template_rules(client, user_headers):
    """
    Test Get Printer Template Rules
    """
    global printer_template_id
    assert printer_template_id is not None, "printer_template_id is not set"
    
    response = do_get_printer_template_rules(client, user_headers)
    assert response.status_code == 200
    
    response_body = response.json
    assert response_body["status"] == "successful"
    assert response_body["action"] == "get_printer_template_rules"
    
    data = response_body["data"]
    assert len(data) > 0, "no printer template rules found"
    
def test_add_printer_template_rule(client, user_headers):
    """
    Test Add Printer Template Rule
    """
    global printer_template_rule_id, printer_template_id
    assert printer_template_id is not None, "printer_template_id is not set"
    
    data = {
        "printer_template_id": printer_template_id,
        "rule_type": "exclusion",
        "printer_rule_expression": "item_category(1)"
    }
    response = do_add_printer_template_rule(client, user_headers, data)
    assert response.status_code == 200
    
    response_body = response.json
    assert response_body["status"] == "successful"
    assert response_body["action"] == "add_printer_template_rule"
    
    data = response_body["data"]
    assert data["printer_template_rule_id"] > 0, "printer template rule id is invalid"
    
    printer_template_rule_id = data["printer_template_rule_id"]

def test_update_printer_template_rule(client, user_headers):
    """
    Test Update Printer Template Rule
    """
    global printer_template_rule_id
    assert printer_template_rule_id is not None, "printer_template_rule_id is not set"
    
    data = {
        "rule_type": "exclusion",
        "printer_rule_expression": "item_category(1)"
    }
    response = do_update_printer_template_rule(client, user_headers, printer_template_rule_id, data)
    assert response.status_code == 200
    
    response_body = response.json
    assert response_body["status"] == "successful"
    assert response_body["action"] == "update_printer_template_rule"
    
    data = response_body["data"]
    assert data["printer_template_rule_id"] == printer_template_rule_id, "printer template rule id is invalid"

def test_delete_printer_template_rule(client, user_headers):
    """
    Test Delete Printer Template Rule
    """
    global printer_template_rule_id
    assert printer_template_rule_id is not None, "printer_template_rule_id is not set"
    
    response = do_delete_printer_template_rule(client, user_headers, printer_template_rule_id)
    assert response.status_code == 200
    
    response_body = response.json
    assert response_body["status"] == "successful"
    assert response_body["action"] == "delete_printer_template_rule"
    
    data = response_body["data"]
    assert data["printer_template_rule_id"] == printer_template_rule_id, "printer template rule id is invalid"

def test_delete_printer_rule(client, user_headers):
    """
    Test Delete Printer Rule
    """
    global printer_rule_id
    assert printer_rule_id is not None, "printer_rule_id is not set"
    
    response = do_delete_printer_rule(client, user_headers, printer_rule_id)
    assert response.status_code == 200
    
    response_body = response.json
    assert response_body["status"] == "successful"
    assert response_body["action"] == "delete_printer_rule"
    
    data = response_body["data"]
    assert data["printer_rule_id"] == printer_rule_id, "printer rule id is invalid"

def test_delete_printer_template(client, user_headers):
    """
    Test Delete Printer Template
    """
    global printer_template_id
    assert printer_template_id is not None, "printer_template_id is not set"
    
    response = do_delete_printer_template(client, user_headers, printer_template_id)
    assert response.status_code == 200
    
    response_body = response.json
    assert response_body["status"] == "successful"
    assert response_body["action"] == "delete_printer_template"
    
    data = response_body["data"]
    assert data["printer_template_id"] == printer_template_id, "printer template id is invalid"