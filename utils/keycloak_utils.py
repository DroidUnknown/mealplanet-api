import os

from keycloak import KeycloakOpenID, KeycloakAdmin
from dotenv import load_dotenv

load_dotenv(override=True)

server_url = os.getenv("KEYCLOAK_SERVER_URL")
client_id = os.getenv("KEYCLOAK_CLIENT_ID")
realm_name = os.getenv("KEYCLOAK_REALM_NAME")
client_secret_key = os.getenv("KEYCLOAK_CLIENT_SECRET_KEY")
admin_username = os.getenv("KEYCLOAK_ADMIN_USERNAME")
admin_password = os.getenv("KEYCLOAK_ADMIN_PASSWORD")


keycloak_client_openid = None
keycloak_admin_openid = None

def get_keycloak_client_openid():
    global keycloak_client_openid
    
    if not keycloak_client_openid:
        keycloak_client_openid = KeycloakOpenID(
            server_url=server_url,
            client_id=client_id,
            realm_name=realm_name,
            client_secret_key=client_secret_key
        )
        
    return keycloak_client_openid

def get_keycloak_admin_openid(master_p=False):
    global keycloak_admin_openid
    
    if master_p:
        return KeycloakAdmin(
            server_url=server_url,
            username=admin_username,
            password=admin_password
        )

    if not keycloak_admin_openid:
        keycloak_admin_openid = KeycloakAdmin(
            server_url=server_url,
            username=admin_username,
            password=admin_password,
            realm_name=realm_name,
            client_id=client_id,
            client_secret_key=client_secret_key
        )
        
    return keycloak_admin_openid

def get_rpt_token(keycloak_client_openid):
    try:
        token = keycloak_client_openid.token(
            grant_type='urn:ietf:params:oauth:grant-type:uma-ticket',
            audience=realm_name
        )
        rpt_token = token['access_token']
        
        return rpt_token
    except Exception as e:
        raise e

def delete_all_users(exception_list=["codify-admin"]):
    keycloak_admin_openid = get_keycloak_admin_openid()
    
    # Delete all existing users
    users = keycloak_admin_openid.get_users()
    for user in users:
        user_id = user["id"]
        username = user["username"]
        if username not in exception_list:
            keycloak_admin_openid.delete_user(user_id=user_id)

def create_user(username, password, first_name="", last_name="", email="", enabled=True):
    keycloak_admin_openid = get_keycloak_admin_openid()
    
    keycloak_user_id = keycloak_admin_openid.create_user({
        "firstName": first_name,
        "lastName": last_name,
        "email": email,
        "enabled": enabled,
        "username": username,
        "credentials": [
            {
                "value": password,
                "type": "password"
            }
        ]
    })
    
    return keycloak_user_id

def create_policy(type, name, keycloak_user_id):
    #TODO: Implement this
    assert False, "Not implemented"
    
    # payload = {
    #     "name": username,
    #     "description": "",
    #     "users": [ keycloak_user_id ],
    #     "logic": "POSITIVE"
    # }
    # keycloak_user_policy_id = keycloak_admin.create_client_authz_policy(client_id, payload)

def attach_user_to_policies(keycloak_user_id, policy_name_list):
    #TODO: Implement this
    assert False, "Not implemented"
    
    # /authz/resource-server/permission/resource
    # {
    #     "resources": [
    #         "d3b68931-6ea5-4030-9d8f-f48e7ce37202"
    #     ],
    #     "policies": [
    #         "b0b79a0d-c553-464a-b9d3-ed17a00108fb"
    #     ],
    #     "name": "all:*:delivery-provider:admin",
    #     "description": "",
    #     "decisionStrategy": "AFFIRMATIVE"
    # }