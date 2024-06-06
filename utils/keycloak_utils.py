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

def get_keycloak_admin_openid():
    global keycloak_admin_openid
    
    if not keycloak_admin_openid:
        print(server_url, admin_username, admin_password, realm_name, client_id, client_secret_key)
        keycloak_admin_openid = KeycloakAdmin(
            server_url=server_url,
            username=admin_username,
            password=admin_password,
            realm_name=realm_name,
            client_id=client_id,
            client_secret_key=client_secret_key
        )
        
    return keycloak_admin_openid