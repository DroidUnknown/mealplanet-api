from sqlalchemy.sql import text
from data_migration_management.data_migration_manager import DataMigrationManager

from models import models, archive_models
from utils import jqutils, jqsecurity
from dotenv import load_dotenv

import pytest
import json
import os

load_dotenv(override=True)

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
        conn.execute('drop database if exists testiblinkpay')
        conn.execute('create database testiblinkpay CHARACTER SET utf8 COLLATE utf8_unicode_ci;')
        conn.execute('SET AUTOCOMMIT=1;')
    models.create_all('testiblinkpay')
    archive_models.create_all('testiblinkpay')

    # Necessary test dummy data
    migrator = DataMigrationManager('testiblinkpay', debug=True)
    migrator.run()
    
    db_engine = jqutils.get_db_engine('testiblinkpay')
    with open('tests/testdata/landscape.json', 'r') as fp:
        data = json.load(fp)
        for table_name in data:
            rows = data[table_name]
            for one_row in rows:
                query, params = jqutils.jq_prepare_insert_statement(table_name, one_row)

                with db_engine.connect() as conn:
                    conn.execute(query, params)

    # LOAD SERVER KEYS
    password_protector_key = jqsecurity.read_symmetric_key_from_file('tests/testdata/test-password-protector.key')

    with db_engine.connect() as conn:
        query = text("""
                    insert into payment_api_secret (key_algorithm, version, key_name, description, symmetric_key, meta_status) 
                    values (:key_algorithm, :version, :key_name, :description, :symmetric_key, :meta_status)
                """)
        result = conn.execute(query, key_algorithm='aes', version=1, key_name='password-protector-key',
                                description='password-protector-key', symmetric_key=password_protector_key, meta_status='active')

    server_token_private_key = jqsecurity.read_key_bytes_from_file('tests/testdata/server-key.private')
    server_token_public_key = jqsecurity.read_key_bytes_from_file('tests/testdata/server-key.public')
    with db_engine.connect() as conn:
        query = text("""
                    insert into payment_api_secret (key_algorithm, version, key_name, description, private_key, public_key, meta_status) 
                    values (:key_algorithm, :version, :key_name, :description, :private_key, :public_key, :meta_status)
                """)
        result = conn.execute(query, key_algorithm='rsa', version=1, key_name='token-protector-key', description='token-protector-key',
                                private_key=server_token_private_key, public_key=server_token_public_key, meta_status='active')

        # UPDATE ADMIN PASSWORD WHERE PLANTEXT IS:
        username = "admin"
        password = 'alburaaq424'
        save_password_and_token(username, password)

        username = "company-x"
        password = '123456'
        save_password_and_token(username, password)

        username = "haider"
        password = '123456'
        save_password_and_token(username, password)

        username = "unverified_user"
        password = '123456'
        save_password_and_token(username, password)

        username = "order-panel"
        password = '123456'
        save_password_and_token(username, password)

@pytest.fixture(scope="session", autouse=True)
def headers():
    yield {
        "X-Access-Token": "9GdJaJxa7O0B-mk0fxzYNw",
        "X-User-Id": "1",
        "X-Api-Key": "A8XSEUlYE9TLgUK5",
    }

@pytest.fixture(scope="session", autouse=True)
def user_headers():
    yield {
        "X-Access-Token": "9GdJaJxa7O0B-mk0fxzhy^",
        "X-User-Id": "2",
        "X-Api-Key": "A8XSEUlYE9TLgUK5",
        "X-Merchant-Id": 1
    }

@pytest.fixture(scope="session", autouse=True)
def order_panel_headers():
    yield {
        "X-Access-Token": "9GdJaJxa7O0B-1234445^",
        "X-User-Id": "5",
        "X-Api-Key": "A8XSEUlYE9TLgUK5",
        "X-Merchant-Id": 1
    }

def save_password_and_token(username, password):
    db_engine = jqutils.get_db_engine('testiblinkpay')
    password_bytes = password.encode()

    with db_engine.connect() as conn:
        query = text(""" 
            select symmetric_key 
            from payment_api_secret 
            where description = 'password-protector-key' and
            meta_status = 'active'
        """)
        result = conn.execute(query).fetchone()
        key_string_db = result['symmetric_key']
        key_string_db_bytes = key_string_db.encode()

    cipher_text_bytes = jqsecurity.encrypt_bytes_symmetric_to_bytes(password_bytes, key_string_db_bytes)

    update_admin_user_query = text(
        """ 
            update user 
            set password = :password, meta_status = :meta_status, token_expiry_timestamp = now() + INTERVAL 180 DAY
            where username = :username                
        """
    )

    meta_status = 'active'
    with db_engine.connect() as conn:
        user_result = conn.execute(update_admin_user_query, username=username, password=cipher_text_bytes, meta_status=meta_status).lastrowid
        conn.execute('commit')
