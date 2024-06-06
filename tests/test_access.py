import json

base_api_url = "/api"

def do_login(client, payload):
    """
    LOGIN
    """
    response = client.post(base_api_url + "/login", json=payload)
    return response

def do_refresh(client, payload):
    """
    REFRESH
    """
    response = client.post(base_api_url + "/refresh", json=payload)
    return response

def do_logout(client, payload):
    """
    LOGOUT
    """
    response = client.post(base_api_url + "/logout", json=payload)
    return response




# ###################
# # TESTS
# ###################

refresh_token = None

def test_login(client):
    payload = {
        "username": "admin",
        "password": "admin123"
    }
    response = do_login(client, payload)
    assert response.status_code == 200
    response_data = response.get_json()
    assert response_data["status"] == "successful"
    assert response_data["data"]["access_token"] is not None
    global refresh_token
    refresh_token = response_data["data"]["refresh_token"]
    
def test_refresh(client):
    payload = {
        "refresh_token": refresh_token
    }
    response = do_refresh(client, payload)
    assert response.status_code == 200
    response_data = response.get_json()
    assert response_data["status"] == "successful"
    assert response_data["data"]["access_token"] is not None
    
def test_logout(client):
    payload = {
        "refresh_token": refresh_token
    }
    response = do_logout(client, payload)
    assert response.status_code == 200
    response_data = response.get_json()
    assert response_data["status"] == "successful"
