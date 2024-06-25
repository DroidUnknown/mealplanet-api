import os
import json

from keycloak import KeycloakOpenID, KeycloakAdmin
from dotenv import load_dotenv

load_dotenv(override=True)

server_url = os.getenv("KEYCLOAK_SERVER_URL")
client_id = os.getenv("KEYCLOAK_CLIENT_ID")
realm_name = os.getenv("KEYCLOAK_REALM_NAME")
client_secret_key = os.getenv("KEYCLOAK_CLIENT_SECRET_KEY")
admin_username = os.getenv("KEYCLOAK_ADMIN_USERNAME")
admin_password = os.getenv("KEYCLOAK_ADMIN_PASSWORD")
client_uuid = os.getenv("KEYCLOAK_CLIENT_UUID")

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
        rpt_token = keycloak_client_openid.token(
            grant_type='urn:ietf:params:oauth:grant-type:uma-ticket',
            audience=realm_name
        )
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
            disassociate_user_from_policies(user_id)
            keycloak_admin_openid.delete_user(user_id=user_id)

def delete_user(user_id):
    keycloak_admin_openid = get_keycloak_admin_openid()

    # Delete a user
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

def update_user(user_id, first_name="", last_name="", email=""):
    keycloak_admin_openid = get_keycloak_admin_openid()
    
    keycloak_admin_openid.update_user(user_id, {
        "firstName": first_name,
        "lastName": last_name,
        "email": email
    })

def update_user_password(user_id, password):
    keycloak_admin_openid = get_keycloak_admin_openid()
    
    keycloak_admin_openid.set_user_password(user_id, password, temporary=False)

def get_user(user_id):
    keycloak_admin_openid = get_keycloak_admin_openid()
    
    user = keycloak_admin_openid.get_user(user_id)
    
    return user

def delete_all_policies():
    keycloak_admin_openid = get_keycloak_admin_openid()
    
    policies = keycloak_admin_openid.get_client_authz_policies(client_uuid)
    
    for policy in policies:
        policy_id = policy["id"]
        keycloak_admin_openid.delete_client_authz_policy(client_uuid, policy_id)

def create_user_policy(username):
    keycloak_admin = get_keycloak_admin_openid()    

    payload={
        "type": "user",
        "config": {
            "users": f"[\"{username}\"]",
        },
        "logic": "POSITIVE",
        "name": username,
        "description": ""
    }
    
    keycloak_user_policy_id = keycloak_admin.create_client_authz_policy(client_uuid, payload)
    
    return keycloak_user_policy_id["id"]

def attach_user_to_policies(associate_policy_id, policy_name_list):
    keycloak_admin_openid = get_keycloak_admin_openid()
    
    policy_list = keycloak_admin_openid.get_client_authz_permissions(client_uuid)
    
    existing_policy_list = keycloak_admin_openid.get_client_authz_policies(client_uuid)
    existing_policy_id_list = [policy["id"] for policy in existing_policy_list]
    assert associate_policy_id in existing_policy_id_list, f"Policy {associate_policy_id} not found"
    
    existing_policy_name_list = []
    for one_policy in policy_list:
        cand_policy_id = one_policy["id"]
        cand_policy_name = one_policy["name"]
        existing_policy_name_list.append(cand_policy_name)
        if cand_policy_name in policy_name_list:
            
            existing_associated_policies = keycloak_admin_openid.get_client_authz_permission_associated_policies(client_uuid, cand_policy_id)
            existing_associated_resources = keycloak_admin_openid.get_client_authz_policy_resources(client_uuid, cand_policy_id)
            
            existing_associated_policy_id_list = [policy["id"] for policy in existing_associated_policies]
            existing_associated_resource_id_list = [resource["_id"] for resource in existing_associated_resources]
            
            if associate_policy_id not in existing_associated_policy_id_list:
                existing_associated_policy_id_list.append(associate_policy_id)

                payload={
                    "id": cand_policy_id,
                    "name": cand_policy_name,
                    "type": "resource",
                    "logic": "POSITIVE",
                    "decisionStrategy": "AFFIRMATIVE",
                    "resources": existing_associated_resource_id_list,
                    "scopes": [],
                    "policies": existing_associated_policy_id_list
                }
                
                keycloak_admin_openid.update_client_authz_resource_permission(payload, client_uuid, cand_policy_id)
      
    for one_policy_name in policy_name_list:
        assert one_policy_name in existing_policy_name_list, f"Policy {one_policy_name} not found"
    
def disassociate_user_from_policies(user_id):
    keycloak_admin_openid = get_keycloak_admin_openid()
    
    existing_policy_list = keycloak_admin_openid.get_client_authz_policies(client_uuid)
    
    user_policy = None
    for policy in existing_policy_list:
        policy_config = policy["config"]
    
        if "users" in policy_config:
            user_id_list = policy_config["users"]
            if user_id in user_id_list:
                user_policy = policy
                break
    
    if user_policy:
        policy_id = user_policy["id"]
        policy_list = keycloak_admin_openid.get_client_authz_permissions(client_uuid)
        
        for one_policy in policy_list:
            
            existing_associated_policies = keycloak_admin_openid.get_client_authz_permission_associated_policies(client_uuid, one_policy["id"])
            existing_associated_policy_id_list = [policy["id"] for policy in existing_associated_policies]
            existing_associated_resources = keycloak_admin_openid.get_client_authz_policy_resources(client_uuid, one_policy["id"])
            existing_associated_resource_id_list = [resource["_id"] for resource in existing_associated_resources]
            
            if policy_id in existing_associated_policy_id_list:
                existing_associated_policy_id_list.remove(policy_id)
                payload={
                    "id": one_policy["id"],
                    "name": one_policy["name"],
                    "type": "resource",
                    "logic": "POSITIVE",
                    "decisionStrategy": "AFFIRMATIVE",
                    "resources": existing_associated_resource_id_list,
                    "scopes": [],
                    "policies": existing_associated_policy_id_list
                }
                
                keycloak_admin_openid.update_client_authz_resource_permission(payload, client_uuid, one_policy["id"])
                
        keycloak_admin_openid.delete_client_authz_policy(client_uuid, policy_id)
    