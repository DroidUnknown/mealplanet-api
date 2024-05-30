from sqlalchemy.sql import text
from data_migration_management.data_migration_manager import DataMigrationManager

from models import models, archive_models
from utils import jqutils
from dotenv import load_dotenv

import pytest
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
        conn.execute('drop database if exists testportalprofileservice')
        conn.execute('create database testportalprofileservice CHARACTER SET utf8 COLLATE utf8_unicode_ci;')
        conn.execute('SET AUTOCOMMIT=1;')
    models.create_all('testportalprofileservice')
    archive_models.create_all('testportalprofileservice')

    # Necessary test dummy data
    migrator = DataMigrationManager('testportalprofileservice', debug=True)
    migrator.run()
    
    db_engine = jqutils.get_db_engine('testportalprofileservice')
    # with open('tests/testdata/landscape.json', 'r') as fp:
    #     data = json.load(fp)
    #     for table_name in data:
    #         rows = data[table_name]
    #         for one_row in rows:
    #             query, params = jqutils.jq_prepare_insert_statement(table_name, one_row)

    #             with db_engine.connect() as conn:
    #                 conn.execute(query, params)


@pytest.fixture(scope="session", autouse=True)
def content_team_headers():
    yield {
        
    }
        