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

    db_engine = jqutils.get_db_engine('test_portalprofile_service')
    with open('tests/testdata/landscape.json', 'r') as fp:
        data = json.load(fp)
        user_list = data['users']

        # create user on keycloak
        keycloak_admin = keycloak_utils.get_keycloak_admin_openid()

        for one_user in user_list:
            first_name = one_user['first_name']
            last_name = one_user['last_name']
            email = one_user['email']
            username = one_user['username']
            password = one_user['password']

            print(f"Creating user {username} with email {email}")

            new_user = keycloak_admin.create_user({
                "email": email,
                "username": username,
                "enabled": True,
                "firstName": first_name,
                "lastName": last_name,
                "credentials": [
                    {
                        "value": password,
                        "type": "password"
                    }
                ]
            })

            print(f"User {username} created on keycloak")
            print(new_user)
            print("==================================================")

@pytest.fixture(scope="session", autouse=True)
def content_team_headers():
    yield {
        
    }
        