from utils import jqutils
from sqlalchemy import text
from flask import Blueprint, request, jsonify, g
from menu_group_management import menu_group_ninja

menu_group_management_blueprint = Blueprint('menu_group_management', __name__)

@menu_group_management_blueprint.route('/menu-group/availability', methods=['POST'])
def check_menu_group_name_availability():
    request_data = request.get_json()

    menu_group_name = request_data["menu_group_name"]

    available_p = menu_group_ninja.check_menu_group_name_availability(menu_group_name)

    response_body = {
        "data": {
            "available_p": available_p
        },
        "action": "check_menu_group_name_availability",
        "status": "successful"
    }
    return jsonify(response_body)

@menu_group_management_blueprint.route('/menu-group', methods=['POST'])
def add_menu_group():
    request_json = request.get_json()

    menu_group_name = request_json["menu_group_name"]
    external_menu_group_id = request_json["external_menu_group_id"]
    
    availabile_p = menu_group_ninja.check_menu_group_name_availability(menu_group_name)
    if not availabile_p:
        response_body = {
            "data": {
                "menu_group_name": menu_group_name
            },
            "action": "add_menu_group",
            "status": "failed",
            "message": "Menu group name already in use."
        }
        return jsonify(response_body)

    db_engine = jqutils.get_db_engine()
    
    query = text("""
        INSERT INTO menu_group (menu_group_name, external_menu_group_id, meta_status, creation_user_id)
        VALUES (:menu_group_name, :external_menu_group_id, :meta_status, :creation_user_id)
    """)
    with db_engine.connect() as conn:
        menu_group_id = conn.execute(query, menu_group_name=menu_group_name, external_menu_group_id=external_menu_group_id, meta_status="active", creation_user_id=g.user_id).lastrowid
        assert menu_group_id, "unable to create menu_group"
   
    response_body = {
        "data": {
            "menu_group_id": menu_group_id
        },
        "action": "add_menu_group",
        "status": "successful"
    }
    return jsonify(response_body)

@menu_group_management_blueprint.route('/bulk-add-menu-groups', methods=['POST'])
def bulk_add_menu_groups():
    request_json = request.get_json()
    menu_group_list = request_json["menu_group_list"]
    assert len(menu_group_list) > 0, "menu_group_list should not be empty"

    query_params = ""
    already_processed_menu_group_name_list = []
    for one_menu_group in menu_group_list:
        menu_group_name = one_menu_group["menu_group_name"]
        external_menu_group_id = one_menu_group["external_menu_group_id"]
        
        if menu_group_name in already_processed_menu_group_name_list:
            response_body = {
                "data": {},
                "action": "bulk_add_menu_groups",
                "status": "failed",
                "message": "Duplicate menu group names found in menu_group_list."
            }
            return jsonify(response_body)
        
        availabile_p = menu_group_ninja.check_menu_group_name_availability(menu_group_name)
        if not availabile_p:
            response_body = {
                "data": {
                    "menu_group_name": menu_group_name
                },
                "action": "bulk_add_menu_groups",
                "status": "failed",
                "message": "Menu group name already in use."
            }
            return jsonify(response_body)

        query_params += f"('{menu_group_name}', '{external_menu_group_id}', 'active', {g.user_id}),"
        already_processed_menu_group_name_list.append(menu_group_name)

    query_params = query_params[:-1]

    db_engine = jqutils.get_db_engine()
    
    query = text(f"""
        INSERT INTO menu_group (menu_group_name, external_menu_group_id, meta_status, creation_user_id)
        VALUES {query_params}
    """)
    with db_engine.connect() as conn:
        results = conn.execute(query).rowcount
        assert results == len(menu_group_list), "unable to create all menu_groups"
   
    response_body = {
        "data": {},
        "action": "bulk_add_menu_groups",
        "status": "successful"
    }
    return jsonify(response_body)

@menu_group_management_blueprint.route('/menu-group/<menu_group_id>', methods=['GET'])
def get_menu_group(menu_group_id):
    menu_group_id = int(menu_group_id)
    
    db_engine = jqutils.get_db_engine()

    query = text("""
        SELECT mg.menu_group_id, mg.menu_group_name, mg.external_menu_group_id
        FROM menu_group mg
        WHERE mg.menu_group_id = :menu_group_id
        AND mg.meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, menu_group_id=menu_group_id, meta_status="active").fetchone()
        assert result, f"menu_group with id {menu_group_id} not found"

    response_body = {
        "data": dict(result),
        "action": "get_menu_group",
        "status": "successful"
    }
    return jsonify(response_body)

@menu_group_management_blueprint.route('/menu-groups', methods=['GET'])
def get_menu_groups():
    db_engine = jqutils.get_db_engine()

    query = text("""
        SELECT mg.menu_group_id, mg.menu_group_name, mg.external_menu_group_id
        FROM menu_group mg
        WHERE mg.meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        results = conn.execute(query, meta_status="active").fetchall()
        menu_group_list = [dict(row) for row in results]

    response_body = {
        "data": {
            "menu_group_list": menu_group_list
        },
        "action": "get_menu_groups",
        "status": "successful"
    }
    return jsonify(response_body)

@menu_group_management_blueprint.route('/menu-group/<menu_group_id>', methods=['PUT'])
def update_menu_group(menu_group_id):
    menu_group_id = int(menu_group_id)
    
    request_json = request.get_json()

    menu_group_name = request_json["menu_group_name"]
    external_menu_group_id = request_json["external_menu_group_id"]
    
    availabile_p = menu_group_ninja.check_menu_group_name_availability(menu_group_name, menu_group_id)
    if not availabile_p:
        response_body = {
            "data": {
                "menu_group_name": menu_group_name
            },
            "action": "update_menu_group",
            "status": "failed",
            "message": "Menu group name already in use."
        }
        return jsonify(response_body)

    query = text("""
        UPDATE menu_group
        SET menu_group_name = :menu_group_name, external_menu_group_id = :external_menu_group_id, modification_user_id = :modification_user_id
        WHERE menu_group_id = :menu_group_id
    """)
    with jqutils.get_db_engine().connect() as conn:
        result = conn.execute(query, menu_group_name=menu_group_name, external_menu_group_id=external_menu_group_id,
                    modification_user_id=g.user_id, menu_group_id=menu_group_id).rowcount
        assert result, f"menu_group with id {menu_group_id} not found"
   
    response_body = {
        "data": {
            "menu_group_id": menu_group_id
        },
        "action": "update_menu_group",
        "status": "successful"
    }
    return jsonify(response_body)

@menu_group_management_blueprint.route('/menu-group/<menu_group_id>', methods=['DELETE'])
def delete_menu_group(menu_group_id):
    menu_group_id = int(menu_group_id)
    
    db_engine = jqutils.get_db_engine()

    with db_engine.connect() as conn:
        query = text("""
            SELECT meta_status
            FROM menu_group
            WHERE menu_group_id = :menu_group_id
        """)
        result = conn.execute(query, menu_group_id=menu_group_id).fetchone()
        assert result, f"menu_group with id {menu_group_id} not found"
        
        existing_meta_status = result["meta_status"]
        if existing_meta_status != "deleted":
            action_timestamp = jqutils.get_utc_datetime()
            
            query = text("""
                UPDATE menu_group
                SET meta_status = :meta_status, deletion_user_id = :deletion_user_id, deletion_timestamp = :deletion_timestamp
                WHERE menu_group_id = :menu_group_id
            """)
            result = conn.execute(query, menu_group_id=menu_group_id, deletion_user_id=g.user_id, deletion_timestamp=action_timestamp, meta_status="deleted").rowcount
            assert result, f"menu_group with id {menu_group_id} not found"
   
    response_body = {
        "data": {
            "menu_group_id": menu_group_id
        },
        "action": "delete_menu_group",
        "status": "successful"
    }
    return jsonify(response_body)