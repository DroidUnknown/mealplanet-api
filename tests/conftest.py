import pytest
import os
import json

from sqlalchemy import text
from dotenv import load_dotenv
load_dotenv(override=True)

from data_migration_management.data_migration_manager import DataMigrationManager
from models import models, archive_models
from utils import jqutils, keycloak_utils

@pytest.fixture(scope="session", autouse=True)
def flask_app():
    assert os.getenv('MYSQL_IP_ADDRESS') in ['localhost', '127.0.0.1'], "tests can only run on localhost"
    import api
    yield api.app

@pytest.fixture(scope="session", autouse=True)
def client(flask_app):
    test_client = flask_app.test_client()
    test_client.testing = True
    return test_client

@pytest.fixture(scope="session", autouse=True)
def landscape():    
    # Dump and recreate database
    db_engine = jqutils.get_db_engine('sys')
    with db_engine.connect() as conn:
        conn.execute('drop database if exists testportalprofileservice')
        conn.execute('create database testportalprofileservice CHARACTER SET utf8 COLLATE utf8_unicode_ci;')
        conn.execute('SET AUTOCOMMIT=1;')
    models.create_all('testportalprofileservice')
    archive_models.create_all('testportalprofileservice')

    # Necessary test dummy data
    migrator = DataMigrationManager('testportalprofileservice', debug=True)
    migrator.run()
    
    assert os.getenv("MYSQL_IP_ADDRESS") in ["localhost", "127.0.0.1"], "tests can only be run locally"
    assert "127.0.0.1" in os.getenv("KEYCLOAK_SERVER_URL"), "tests can only be run locally"
    
    # delete all users from keycloak
    keycloak_utils.delete_all_users()
    
    db_engine = jqutils.get_db_engine('testportalprofileservice')
    with db_engine.connect() as conn:
        
        with open('tests/testdata/landscape.json', 'r') as fp:
            data = json.load(fp)
            for table_name in data:
                rows = data[table_name]
                for one_row in rows:
                    one_row["meta_status"] = "active"
                    one_row["creation_user_id"] = 1
                    query, params = jqutils.jq_prepare_insert_statement(table_name, one_row)
                    conn.execute(query, params)
    
        with open('tests/testdata/users.json', 'r') as fp:
            user_list = json.load(fp)

            for one_user in user_list:
                userdata = {
                    "first_name": one_user['first_name'],
                    "last_name": one_user['last_name'],
                    "phone_nr": one_user['phone_nr'],
                    "email": one_user['email'],
                    "username": one_user['username'],
                    "password": one_user['password']
                }
                allowed_resource_list = one_user['allowed_resource_list']
                role_name_list = one_user['role_name_list']
                
                user_id, policy_id, keycloak_user_id = create_user_on_keycloak_and_database(conn, userdata, allowed_resource_list=allowed_resource_list, role_name_list=role_name_list)

@pytest.fixture(scope="session", autouse=True)
def content_team_headers():
    yield {
        
    }

def create_user_on_keycloak_and_database(conn, userdata, allowed_resource_list=[], role_name_list=[]):
    username = userdata["username"]
    
    # create user on keycloak
    keycloak_user_id = keycloak_utils.create_user(userdata["username"], userdata["password"], userdata["first_name"], userdata["last_name"], userdata["email"])
    
    # create user in database
    user_dict = {
        "keycloak_user_id": keycloak_user_id,
        "first_names_en": userdata["first_name"],
        "last_name_en": userdata["last_name"],
        "phone_nr": userdata["phone_nr"],
        "email": userdata["email"],
        "meta_status": "active",
        "creation_user_id": 1,
    }
    query, params = jqutils.jq_prepare_insert_statement('user', user_dict)
    user_id = conn.execute(query, params).lastrowid
    assert user_id, "Failed to create user"
    
    # create policy for user on keycloak
    keycloak_user_policy_id = keycloak_utils.create_user_policy(username)
    
    # create policy for user in database
    policy_dict = {
        "keycloak_policy_id": str(keycloak_user_policy_id),
        "policy_name": username,
        "policy_type": "user",
        "logic": "POSITIVE",
        "decision_strategy": "AFFIRMATIVE",
        "meta_status": "active",
        "creation_user_id": 1,
    }
    query, params = jqutils.jq_prepare_insert_statement('policy', policy_dict)
    
    policy_id = conn.execute(query, params).lastrowid
    assert policy_id, "Failed to create policy for user"
    
    # attach user to policy
    policy_user_map_dict = {
        "policy_id": policy_id,
        "user_id": user_id,
        "meta_status": "active",
        "creation_user_id": 1,
    }
    query, params = jqutils.jq_prepare_insert_statement('policy_user_map', policy_user_map_dict)
    result = conn.execute(query, params).lastrowid
    assert result, "Failed to attach user to policy"
    
    if allowed_resource_list:
        assign_policies_to_user(conn, user_id, keycloak_user_policy_id, allowed_resource_list)
    
    if role_name_list:
        assign_realm_roles_to_user(conn, user_id, keycloak_user_id, role_name_list)
        
    return user_id, policy_id, keycloak_user_id

def assign_policies_to_user(conn, user_id, keycloak_user_policy_id, policy_name_list):
    
    # get policies from database
    query = text("""
        SELECT policy_id, policy_name, keycloak_policy_id
        FROM policy
        WHERE policy_name IN :policy_name_list
        AND policy_type = :policy_type
        AND meta_status = :meta_status
    """)
    results = conn.execute(query, policy_name_list=policy_name_list, policy_type="resource", meta_status="active").fetchall()
    assert results, "Failed to find policies"
    
    policy_name_id_map = {}
    keycloak_policy_id_list = []
    for one_policy in results:
        policy_id = one_policy["policy_id"]
        policy_name = one_policy["policy_name"]
        keycloak_policy_id = one_policy["keycloak_policy_id"]
        
        policy_name_id_map[policy_name] = policy_id
        keycloak_policy_id_list.append(keycloak_policy_id)
    
    # attach user to correct policies on keycloak
    keycloak_utils.attach_user_to_policies(keycloak_user_policy_id, keycloak_policy_id_list)
    
    # attach user to correct policies in database
    for policy_name in policy_name_list:
        policy_id = policy_name_id_map[policy_name]
        policy_user_map_dict = {
            "policy_id": policy_id,
            "user_id": user_id,
            "meta_status": "active",
            "creation_user_id": 1,
        }
        query, params = jqutils.jq_prepare_insert_statement('policy_user_map', policy_user_map_dict)
        result = conn.execute(query, params).lastrowid
        assert result, "Failed to attach user to policy"

def assign_realm_roles_to_user(conn, user_id, keycloak_user_id, role_name_list):
    
    # get roles from database
    query = text("""
        SELECT role_id, role_name, keycloak_realm_role_id
        FROM role
        WHERE role_name IN :role_name_list
        AND meta_status = :meta_status
    """)
    results = conn.execute(query, role_name_list=role_name_list, meta_status="active").fetchall()
    assert results, "Failed to find roles"
    
    role_name_id_map = {}
    keycloak_realm_role_id_list = []
    for one_role in results:
        role_id = one_role["role_id"]
        role_name = one_role["role_name"]
        keycloak_realm_role_id = one_role["keycloak_realm_role_id"]
        
        role_name_id_map[role_name] = role_id
        keycloak_realm_role_id_list.append(keycloak_realm_role_id)
    
    # attach realm roles to user on keycloak
    keycloak_utils.assign_realm_roles_to_user(keycloak_user_id, keycloak_realm_role_id_list)
    
    # attach realm roles to user in database
    for role_name in role_name_list:
        role_id = role_name_id_map[role_name]
        user_role_map_dict = {
            "user_id": user_id,
            "role_id": role_id,
            "meta_status": "active",
            "creation_user_id": 1,
        }
        query, params = jqutils.jq_prepare_insert_statement('user_role_map', user_role_map_dict)
        result = conn.execute(query, params).lastrowid
        assert result, "Failed to attach user to role"