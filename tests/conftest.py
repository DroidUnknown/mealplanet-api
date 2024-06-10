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
    
    # # delete all users from keycloak
    # keycloak_utils.delete_all_users()
    
    # keycloak_utils.delete_all_policies()
    
    # db_engine = jqutils.get_db_engine('testportalprofileservice')
    # with db_engine.connect() as conn:
    
    #     with open('tests/testdata/users.json', 'r') as fp:
    #         user_list = json.load(fp)

    #         for one_user in user_list:
    #             first_name = one_user['first_name']
    #             last_name = one_user['last_name']
    #             phone_nr = one_user['phone_nr']
    #             email = one_user['email']
    #             username = one_user['username']
    #             password = one_user['password']
    #             allowed_resource_list = one_user['allowed_resource_list']
                
    #             user_id, policy_id, keycloak_user_id = create_user_on_keycloak_and_database(conn, username, password, first_name, last_name, email, phone_nr)
        
    #     with open('tests/testdata/landscape.json', 'r') as fp:
    #         data = json.load(fp)
    #         for table_name in data:
    #             rows = data[table_name]
    #             for one_row in rows:
    #                 one_row["meta_status"] = "active"
    #                 one_row["creation_user_id"] = 1
    #                 query, params = jqutils.jq_prepare_insert_statement(table_name, one_row)
    #                 conn.execute(query, params)

@pytest.fixture(scope="session", autouse=True)
def content_team_headers():
    yield {
        
    }

def create_user_on_keycloak_and_database(conn, username, password, first_name, last_name, email, phone_nr):
    
    # create user on keycloak
    keycloak_user_id = keycloak_utils.create_user(username, password, first_name, last_name, email)
    
    # create user in database
    user_dict = {
        "keycloak_user_id": keycloak_user_id,
        "first_names_en": first_name,
        "last_name_en": last_name,
        "phone_nr": phone_nr,
        "email": email,
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
        "decision_strategy": "UNANIMOUS",
    }
    query, params = jqutils.jq_prepare_insert_statement('policy', policy_dict)
    print(query)
    policy_id = conn.execute(query, params).lastrowid
    assert policy_id, "Failed to create policy for user"
    
    # attach user to policy
    policy_user_map_dict = {
        "policy_id": policy_id,
        "user_id": user_id
    }
    query, params = jqutils.jq_prepare_insert_statement('policy_user_map', policy_user_map_dict)
    result = conn.execute(query, params).lastrowid
    assert result, "Failed to attach user to policy"
    attach_user_to_policies(conn, keycloak_user_id, [username])
    return user_id, policy_id, keycloak_user_id

def attach_user_to_policies(conn, keycloak_user_id, policy_name_list):
    
    # attach user to correct policies on keycloak
    keycloak_utils.attach_user_to_policies(keycloak_user_id, policy_name_list)
    
    # attach user to correct policies in database
    query = text("""
        SELECT policy_id, policy_name
        FROM policy
        WHERE policy_name IN :policy_name_list
        AND policy_type = :policy_type
        AND meta_status = :meta_status
    """)
    results = conn.execute(query, policy_name_list=policy_name_list, policy_type="resource", meta_status="active").fetchall()
    # assert results, "Failed to find policies"
    
    # TODO: implement this