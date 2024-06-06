import json

base_api_url = "/api"

def do_login(client, payload):
    """
    LOGIN
    """
    response = client.post(base_api_url + "/login", json=payload)
    return response


def test_login(client):
    payload = {
        "username": "codify-admin",
        "password": "123456"
    }
    response = do_login(client, payload)
    assert response.status_code == 200
    response_data = response.get_json()
    assert response_data["message"] == "Login successful"
    assert response_data["data"]["access_token"] is not None
    
    print(json.dumps(response_data, indent=4))