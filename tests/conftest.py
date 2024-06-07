import pytest
import os
import json

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
        conn.execute('drop database if exists test_portalprofile_service')
        conn.execute('create database test_portalprofile_service CHARACTER SET utf8 COLLATE utf8_unicode_ci;')
        conn.execute('SET AUTOCOMMIT=1;')
    models.create_all('test_portalprofile_service')
    archive_models.create_all('test_portalprofile_service')

    # Necessary test dummy data
    migrator = DataMigrationManager('test_portalprofile_service', debug=True)
    migrator.run()
    
    # create user on keycloak
    keycloak_admin = keycloak_utils.get_keycloak_admin_openid()
    
    # Delete all existing users
    users = keycloak_admin.get_users()
    for user in users:
        user_id = user["id"]
        username = user["username"]
        if username != "codify-admin":
            keycloak_admin.delete_user(user_id=user_id)
    
    db_engine = jqutils.get_db_engine('test_portalprofile_service')
    with db_engine.connect() as conn:
    
        with open('tests/testdata/users.json', 'r') as fp:
            user_list = json.load(fp)

            for one_user in user_list:
                first_name = one_user['first_name']
                last_name = one_user['last_name']
                phone_nr = one_user['phone_nr']
                email = one_user['email']
                username = one_user['username']
                password = one_user['password']
                allowed_resource_list = one_user['allowed_resource_list']

                keycloak_user_id = keycloak_admin.create_user({
                    "firstName": first_name,
                    "lastName": last_name,
                    "email": email,
                    "enabled": True,
                    "username": username,
                    "credentials": [
                        {
                            "value": password,
                            "type": "password"
                        }
                    ]
                })
                
                # payload = {
                #     "name": username,
                #     "description": "",
                #     "users": [ keycloak_user_id ],
                #     "logic": "POSITIVE"
                # }
                # keycloak_user_policy_id = keycloak_admin.create_client_authz_policy("Istio", payload)
                
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
                #     "decisionStrategy": "UNANIMOUS"
                # }
                
                user_dict = {
                    "keycloak_user_id": keycloak_user_id,
                    "first_names_en": first_name,
                    "last_name_en": last_name,
                    "phone_nr": phone_nr,
                    "email": email,
                }
                query, params = jqutils.jq_prepare_insert_statement('user', user_dict)
                conn.execute(query, params)
        
        with open('tests/testdata/landscape.json', 'r') as fp:
            data = json.load(fp)
            for table_name in data:
                rows = data[table_name]
                for one_row in rows:
                    one_row["meta_status"] = "active"
                    one_row["creation_user_id"] = 1
                    query, params = jqutils.jq_prepare_insert_statement(table_name, one_row)
                    conn.execute(query, params)

@pytest.fixture(scope="session", autouse=True)
def content_team_headers():
    yield {
        
    }
        