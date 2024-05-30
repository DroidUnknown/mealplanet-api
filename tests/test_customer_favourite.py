import json

base_api_url = "/api"
customer_favourite_id = None

def do_add_customer_favourite(client,headers,data):
    """
    Add a customer favourite item
    """
    response = client.post(base_api_url + '/customer_favourite', json=data, headers=headers)
    return response
            
def do_get_customer_favourites(client,headers,customer_id,branch_id):
    """
    Get all customer favourite items
    """
    response = client.get(base_api_url + f'/customer/{customer_id}/customer_favourites?branch_id={branch_id}', headers=headers)
    return response

def do_delete_customer_favourite(client,headers,customer_favourite_id):
    """
    Delete a customer favourite item
    """
    response = client.delete(base_api_url + '/customer_favourite/' + str(customer_favourite_id), headers=headers)
    return response

##############
# TESTS CASES
##############

def test_do_add_customer_favourite(client,headers):
    
    data = {
        'customer_id': 1,
        'item_id': 1
    }

    response = do_add_customer_favourite(client,headers,data)
    assert response.status_code == 200
    j = json.loads(response.data)
    status = j['status']
    assert status == 'successful'

def test_do_get_customer_favourites(client,headers):

    response = do_get_customer_favourites(client,headers,1,7)
    assert response.status_code == 200
    j = json.loads(response.data)
    status = j['status']
    assert status == 'successful'

    global customer_favourite_id
    customer_favourite_id = j['data'][0]['customer_favourite_item_map_id']

def test_do_delete_customer_favourite(client,headers):
    
    response = do_delete_customer_favourite(client,headers,customer_favourite_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    status = j['status']
    assert status == 'successful'