import json

base_api_url = "/api"

##############
# TEST - LOGIN
##############

def do_login(client, username="admin", password="alburaaq424"):
    """
    Login to the API
    """
    payload = {
        "username": username,
        "password": password
    }
    headers = {
        'Content-Type': 'application/json'
    }
    response = client.post(f'{base_api_url}/login', data=json.dumps(payload), headers=headers)
    return response

def do_logout(client, access_token, user_id):
    """
    Logout from the API
    """
    headers = {
        "X-Access-Token": access_token,
        "X-User-ID": user_id,
    }
    response = client.post(f'{base_api_url}/logout', headers=headers)
    return response

def do_authorization(client, access_token, user_id):
    """
    Test authorization
    """
    headers = {}
    if access_token:
        headers["X-Access-Token"] = access_token
    if user_id:
        headers["X-User-ID"] = user_id

    response = client.get(f'{base_api_url}/authorization', headers=headers)
    return response

##############
# Test Cases
##############

def test_successful_login(client):
    """
    Test a successful login
    """
    response = do_login(client, 'admin', 'alburaaq424')
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'

def test_failed_login_wrong_password(client):
    """
    Test a failed login
    """
    response = do_login(client, 'admin', 'wrong')
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j['status'] == 'failed'
    assert j['message'] == 'invalid username or password'

def test_successful_login_unverified_otp(client):
    """
    Test a successful login for an unverified user
    """
    response = do_login(client, 'unverified_user', '123456')
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j['status'] == 'successful'
    assert j['user_details']['phone_verified_p'] == False

# def test_successful_logout(client):
#     """
#     Test a successful logout
#     """
#     response = do_login(client, 'jq', 'saarookh-dxb')
#     access_token = response.headers['X-Access-Token']
#     user_id = response.headers['X-User-ID']
#     response = do_logout(client, access_token, user_id)
#     assert response.status_code == 200
#     assert response.json['status'] == 'successful'

# def test_successful_authorization(client):
#     """
#     Test a successful authorization
#     """
#     response = do_login(client, 'jq', 'saarookh-dxb')
#     access_token = response.headers['X-Access-Token']
#     user_id = response.headers['X-User-ID']
#     response = do_authorization(client, access_token, user_id)
#     assert response.status_code == 200
#     assert response.json['status'] == 'successful'

# def test_failed_authorization(client):
#     """
#     Test a failed authorization
#     """
#     response = do_authorization(client, None, None)
#     assert response.status_code == 401

# def test_failed_logout_wrong_access_token(client):
#     """
#     Test a failed logout (wrong access token)
#     """
#     response = do_login(client, 'jq', 'saarookh-dxb')
#     user_id = response.headers['X-User-ID']
#     response = do_logout(client, "wrong access token", user_id)
#     assert response.status_code == 401

# def test_failed_logout_wrong_user_id(client):
#     """
#     Test a failed logout (wrong user id)
#     """
#     response = do_login(client, 'jq', 'saarookh-dxb')
#     access_token = response.headers['X-Access-Token']
#     response = do_logout(client, access_token, -1)
#     assert response.status_code == 401

# def test_failed_logout_no_access_token(client):
#     """
#     Test a failed logout (no access token)
#     """
#     response = do_login(client, 'jq', 'saarookh-dxb')
#     user_id = response.headers['X-User-ID']
#     response = do_logout(client, None, user_id)
#     assert response.status_code == 401

# def test_failed_logout_no_user_id(client):
#     """
#     Test a failed logout (no user id)
#     """
#     response = do_login(client, 'jq', 'saarookh-dxb')
#     access_token = response.headers['X-Access-Token']
#     response = do_logout(client, access_token, None)
#     assert response.status_code == 401
