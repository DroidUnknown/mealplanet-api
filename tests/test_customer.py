import json

base_api_url = "/api"

def do_update_customer(client, headers, data, customer_id):
    response = client.put(base_api_url + '/customer/'+ str(customer_id), json=data, headers=headers)
    return response

def do_get_customer(client, headers, customer_id):
    response = client.get(base_api_url + '/customer/'+ str(customer_id), headers=headers)
    return response

def do_get_customers(client, headers, merchant_id=None, customer_phone_nr=None):
    request_url = base_api_url + '/customers'
    if merchant_id:
        request_url = request_url + '?merchant_id=' + str(merchant_id)
    if customer_phone_nr:
        request_url = request_url + '&customer_phone_nr=' + str(customer_phone_nr)
    response = client.get(request_url, headers=headers)
    return response

# def do_delete_customer(client, headers, customer_id):
#     response = client.delete(base_api_url + '/customer/'+ str(customer_id), headers=headers)
#     return response

##############
# TESTS
##############

def test_do_update_customer(client, headers):
    data = {
        'customer_code': 'abc123',
        'stripe_customer_id': 'cus_123',
        'merchant_id': 1,
        'customer_first_name': 'test customer',
        'customer_last_name': 'user',
        'customer_email': 'test@user.com',
        'customer_phone_nr': '12331231312',
        'customer_remote_id' : '123',
        'customer_gender': 'male',
        'customer_dob': '2020-01-01'
    }
    response = do_update_customer(client, headers, data, customer_id=1)
    j = json.loads(response.data)
    status = j['status']
    assert status == 'successful'

def test_do_get_customer(client,headers):
    response = do_get_customer(client, headers, 1)
    j = json.loads(response.data)
    status = j['status']
    assert status == 'successful'

def test_do_get_customers(client, headers):
    merchant_id = 1
    response = do_get_customers(client, headers, merchant_id)
    j = json.loads(response.data)
    status = j['status']
    assert status == 'successful'

def test_do_get_customers_by_phone_nr(client, headers):
    merchant_id = 1
    phone_nr = '12331231312'
    response = do_get_customers(client, headers, merchant_id, phone_nr)
    j = json.loads(response.data)
    status = j['status']
    assert status == 'successful'

# def test_do_delete_customer(client, headers):
#     response = do_delete_customer(client, headers, 1)
#     j = json.loads(response.data)
#     status = j['status']
#     assert status == 'successful'