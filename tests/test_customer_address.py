import json

base_api_url = "/api"

def do_add_customer_address(client,headers,data):

    response = client.post(base_api_url + '/customer_address', json=data, headers=headers)
    return response

def do_update_customer_address(client,headers,data,customer_address_id):

    response = client.put(base_api_url + '/customer_address/'+ str(customer_address_id), json=data, headers=headers)
    return response
    
def do_get_customer_address(client,headers,customer_address_id):

    response = client.get(base_api_url + '/customer_address/'+ str(customer_address_id), headers=headers)
    return response
        
def do_get_customer_addresses(client,headers,customer_id):

    response = client.get(base_api_url + f'/customer/{customer_id}/customer_addresses', headers=headers)
    return response

def do_delete_customer_address(client,headers,customer_address_id):

    response = client.delete(base_api_url + '/customer_address/'+ str(customer_address_id), headers=headers)
    return response

##############
# TESTS
##############


def test_do_add_customer_address(client,headers):

    data = {
        'customer_id': 1,
        'address_line_1': 'line_1', 
        'address_line_2': 'line_2',
        'address_type_id': 1,
        'city_id': 1,
        'latitude': '36.89',
        'longitude': '89.09',
        'delivery_instructions': 'leave at door'
    }

    response = do_add_customer_address(client,headers,data)
    j = json.loads(response.data)
    status = j['status']
    assert status == 'successful'

def test_do_update_customer_address(client,headers):

    data = {
        'customer_id': 1,
        'address_line_1': 'line_5', 
        'address_line_2': 'line_4',
        'address_type_id': 1,
        'city_id': 1,
        'latitude': '36.89',
        'longitude': '89.09',
        'delivery_instructions': 'leave at door and ring bell'
    }

    response = do_update_customer_address(client,headers,data,1)
    j = json.loads(response.data)
    status = j['status']
    assert status == 'successful'

def test_do_get_customer_address(client,headers):

    response = do_get_customer_address(client,headers,1)
    j = json.loads(response.data)
    status = j['status']
    assert status == 'successful'

def test_do_get_customer_addresses(client,headers):

    response = do_get_customer_addresses(client,headers,1)
    j = json.loads(response.data)
    status = j['status']
    assert status == 'successful'

def test_do_delete_customer_address(client,headers):

    response = do_delete_customer_address(client,headers,1)
    j = json.loads(response.data)
    status = j['status']
    assert status == 'successful'




            
