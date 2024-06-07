import os
import json
import traceback
import logging

from sqlalchemy import text
from flask import Blueprint, request, jsonify, g
from utils import keycloak_utils, jqutils, jqimage_uploader

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger.setLevel(logging.INFO)

role_management_blueprint = Blueprint('role_management', __name__)

@role_management_blueprint.route('/roles', methods=['GET'])
def get_roles():
    db_engine = jqutils.get_db_engine()

    query = text("""
        SELECT role_id, role_name
        FROM role
        WHERE meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, meta_status="active").fetchall()

    response_body = {
        "data": [dict(row) for row in result],
        "action": "get_roles",
        "status": "successful"
    }
    return jsonify(response_body)