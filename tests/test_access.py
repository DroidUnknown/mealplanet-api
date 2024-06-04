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
        "username": "hannan.aamir",
        "password": "123456"
    }
    response = do_login(client, payload)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data["message"] == "Login successful"
    assert response_data["data"]["access_token"] is not None