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
        "username": "basiligo",
        "password": "basiligo123"
    }
    response = do_login(client, payload)
    assert response.status_code == 200
    
    response_json = response.get_json()
    assert response_json["status"] == "successful"
    assert response_json["action"] == "login"
    
    data = response_json["data"]
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["rpt_token"]
    
    global access_token, refresh_token
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]
    
def test_refresh(client):    
    global refresh_token
    
    payload = {
        "refresh_token": refresh_token
    }
    response = do_refresh(client, payload)
    assert response.status_code == 200
    
    response_json = response.get_json()
    assert response_json["status"] == "successful"
    assert response_json["action"] == "refresh"
    
    data = response_json["data"]
    assert data["refresh_token"]
    
    refresh_token = data["refresh_token"]
    
def test_logout(client):
    global refresh_token
    
    payload = {
        "refresh_token": refresh_token
    }
    response = do_logout(client, payload)
    assert response.status_code == 200
    
    response_json = response.get_json()
    assert response_json["status"] == "successful"
    assert response_json["action"] == "logout"
