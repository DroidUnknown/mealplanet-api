from flask import Blueprint, request, jsonify, g
from sqlalchemy import text

from utils import jqutils
from menu_group_management import menu_group_ninja

menu_group_management_blueprint = Blueprint('menu_group_management', __name__)

@menu_group_management_blueprint.route('/menu-group', methods=['POST'])
def add_menu_group():
    request_data = request.get_json()

    menu_group_name = request_data["menu_group_name"]

    one_dict = {
        "menu_group_name": menu_group_name,
        "meta_status": "active",
        "creation_user_id": g.user_id
    }

    menu_group_id = jqutils.create_new_single_db_entry(one_dict, "menu_group")
   
    response_body = {
        "data": {
            "menu_group_id": menu_group_id
        },
        "action": "add_menu_group",
        "status": "successful"
    }
    return jsonify(response_body)

@menu_group_management_blueprint.route('/menu-group/<menu_group_id>', methods=['GET'])
def get_menu_group(menu_group_id):
    db_engine = jqutils.get_db_engine()

    query = text("""
        SELECT mg.menu_group_id, mg.menu_group_name
        FROM menu_group mg
        WHERE mg.menu_group_id = :menu_group_id
        AND mg.meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, menu_group_id=menu_group_id, meta_status="active").fetchone()

    if result:
        response_body = {
            "data": dict(result),
            "action": "get_menu_group",
            "status": "successful"
        }
    else:
        response_body = {
            "data": {},
            "action": "get_menu_group",
            "status": "successful",
            "message": "No data found"
        }
    return jsonify(response_body)

@menu_group_management_blueprint.route('/menu-group/<menu_group_id>', methods=['PUT'])
def update_menu_group(menu_group_id):
    request_data = request.get_json()

    menu_group_name = request_data["menu_group_name"]

    one_dict = {
        "menu_group_name": menu_group_name,
        "modification_user_id": g.user_id
    }

    condition = {
        "menu_group_id": str(menu_group_id),
        "meta_status": 'active'
    }

    jqutils.update_single_db_entry(one_dict, "menu_group", condition)
   
    response_body = {
        "action": "update_menu_group",
        "status": "successful"
    }
    return jsonify(response_body)

@menu_group_management_blueprint.route('/menu-group/<menu_group_id>', methods=['DELETE'])
def delete_menu_group(menu_group_id):
    one_dict = {
        "meta_status": "deleted",
        "deletion_user_id": g.user_id,
        "deletion_timestamp": jqutils.get_utc_datetime()
    }

    condition = {
        "menu_group_id": str(menu_group_id)
    }

    jqutils.update_single_db_entry(one_dict, "menu_group", condition)
   
    response_body = {
        "action": "delete_menu_group",
        "status": "successful"
    }
    return jsonify(response_body)

@menu_group_management_blueprint.route('/menu-groups', methods=['GET'])
def get_menu_groups():
    db_engine = jqutils.get_db_engine()

    query = text("""
        SELECT mg.menu_group_id, mg.menu_group_name
        FROM menu_group mg
        WHERE mg.meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, meta_status="active").fetchall()

    response_body = {
        "data": [dict(row) for row in result],
        "action": "get_menu_groups",
        "status": "successful"
    }
    return jsonify(response_body)

@menu_group_management_blueprint.route('/plan/<plan_id>/menu-group', methods=['GET'])
def get_menu_groups_by_plan(plan_id):
    db_engine = jqutils.get_db_engine()

    result = menu_group_ninja.get_menu_group_list_map_by_plan_list([plan_id])
    response_body = {
        "data": result,
        "action": "get_menu_groups_by_plan",
        "status": "successful"
    }
    return jsonify(response_body)