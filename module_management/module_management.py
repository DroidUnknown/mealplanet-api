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

module_management_blueprint = Blueprint('module_management', __name__)

@module_management_blueprint.route('/modules', methods=['GET'])
def get_modules():
    db_engine = jqutils.get_db_engine()

    query = text("""
        SELECT module_id, module_name, module_description
        FROM module
        WHERE meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, meta_status="active").fetchall()

    module_list = [dict(row) for row in result]

    for one_module in module_list:
        module_id = one_module["module_id"]

        # get module accesses
        query = text("""
            SELECT module_access_id, access_level
            FROM module_access
            WHERE module_id = :module_id
            AND meta_status = :meta_status
        """)
        with db_engine.connect() as conn:
            module_access_result = conn.execute(query, module_id=module_id, meta_status="active").fetchall()

        module_access_list = []
        for one_module_access in module_access_result:
            module_access_list.append(dict(one_module_access))

        one_module["module_access_list"] = module_access_list

    response_body = {
        "data": module_list,
        "action": "get_modules",
        "status": "successful"
    }
    return jsonify(response_body)