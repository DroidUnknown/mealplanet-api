from flask import Blueprint, request, jsonify, g
from sqlalchemy import text

from utils import jqutils
from plan_management import plan_ninja

plan_management_blueprint = Blueprint('plan_management', __name__)

@plan_management_blueprint.route('/plan/availability', methods=['POST'])
def check_plan_name_availability():
    request_json = request.get_json()

    plan_name = request_json["plan_name"]
    brand_profile_id = request_json["brand_profile_id"]

    availability_p = plan_ninja.check_plan_name_availability(plan_name, brand_profile_id)

    response_body = {
        "data": {
            "availability_p": availability_p
        },
        "action": "check_plan_name_availability",
        "status": "successful"
    }
    return jsonify(response_body)

@plan_management_blueprint.route('/plan', methods=['POST'])
def add_plan():
    request_json = request.get_json()

    brand_profile_id = request_json["brand_profile_id"]
    plan_name = request_json["plan_name"]
    external_plan_id = request_json["external_plan_id"]
    menu_group_id_list = request_json["menu_group_id_list"]    
    
    availabile_p = plan_ninja.check_plan_name_availability(plan_name, brand_profile_id)
    if not availabile_p:
        response_body = {
            "data": {},
            "action": "add_plan",
            "status": "failed",
            "message": "Plan name already in use."
        }
        return jsonify(response_body)

    db_engine = jqutils.get_db_engine()

    with db_engine.connect() as conn:
        query = text("""
            INSERT INTO PLAN (brand_profile_id, plan_name, external_plan_id, meta_status, creation_user_id)
            VALUES (:brand_profile_id, :plan_name, :external_plan_id, :meta_status, :creation_user_id)
        """)
        plan_id = conn.execute(query, brand_profile_id=brand_profile_id, plan_name=plan_name, external_plan_id=external_plan_id,
                meta_status="active", creation_user_id=g.user_id).lastrowid
        assert plan_id, "unable to create plan"

        query_params = ""
        menu_group_id_list = list(set(menu_group_id_list))
        for menu_group_id in menu_group_id_list:
            query_params += f"({plan_id}, {menu_group_id}, 'active', {g.user_id}),"
        
        if query_params:
            query_params = query_params[:-1]
            query = text(f"""
                INSERT INTO plan_menu_group_map (plan_id, menu_group_id, meta_status, creation_user_id)
                VALUES {query_params}
            """)
            result = conn.execute(query).rowcount
            assert result == len(menu_group_id_list), "unable to create plan_menu_group_map"

    response_body = {
        "data": {
            "plan_id": plan_id
        },
        "action": "add_plan",
        "status": "successful"
    }
    return jsonify(response_body)

@plan_management_blueprint.route('/plan/<plan_id>', methods=['GET'])
def get_plan(plan_id):    
    db_engine = jqutils.get_db_engine()

    with db_engine.connect() as conn:
        query = text("""
            SELECT plan_id, external_plan_id, brand_profile_id, plan_name
            FROM plan
            WHERE plan_id = :plan_id
            AND meta_status = :meta_status
        """)
        result = conn.execute(query, plan_id=plan_id, meta_status="active").fetchone()
        assert result, f"unable to get plan_id: {plan_id}"

        plan_detail = {
            "plan_id": result["plan_id"],
            "brand_profile_id": result["brand_profile_id"],
            "plan_name": result["plan_name"],
            "external_plan_id": result["external_plan_id"],
        }
        
        query = text("""
            SELECT mg.menu_group_id, mg.menu_group_name, mg.external_menu_group_id
            FROM plan_menu_group_map pmgm
            JOIN menu_group mg ON pmgm.menu_group_id = mg.menu_group_id
            WHERE pmgm.plan_id = :plan_id
            AND pmgm.meta_status = :meta_status
            AND mg.meta_status = :meta_status
        """)
        result = conn.execute(query, plan_id=plan_id, meta_status="active").fetchall()
        plan_detail["menu_group_list"] = [dict(row) for row in result]

    response_body = {
        "data": plan_detail,
        "action": "get_plan",
        "status": "successful"
    }
    return jsonify(response_body)

@plan_management_blueprint.route('/plan/<plan_id>', methods=['PUT'])
def update_plan(plan_id):
    request_data = request.get_json()

    brand_profile_id = request_data["brand_profile_id"]
    plan_name = request_data["plan_name"]
    external_plan_id = request_data["external_plan_id"]
    menu_group_id_list = request_data["menu_group_id_list"]
    menu_group_id_list = list(set(menu_group_id_list))

    availabile_p = plan_ninja.check_plan_name_availability(plan_name, brand_profile_id, plan_id)
    if not availabile_p:
        response_body = {
            "data": {},
            "action": "update_plan",
            "status": "failed",
            "message": "Plan name already in use."
        }
        return jsonify(response_body)

    db_engine = jqutils.get_db_engine()
    
    with db_engine.connect() as conn:
        query = text("""
            UPDATE plan
            SET plan_name = :plan_name, external_plan_id = :external_plan_id, modification_user_id = :modification_user_id
            WHERE plan_id = :plan_id
        """)
        result = conn.execute(query, plan_name=plan_name, external_plan_id=external_plan_id, modification_user_id=g.user_id, plan_id=plan_id).rowcount
        assert result, f"unable to update plan_id: {plan_id}"
    
        # get existing menu_group_id_list
        query = text("""
            SELECT menu_group_id
            FROM plan_menu_group_map
            WHERE plan_id = :plan_id
            AND meta_status = :meta_status
        """)
        result = conn.execute(query, plan_id=plan_id, meta_status="active").fetchall()
        existing_menu_group_id_list = [row["menu_group_id"] for row in result]
    
        # get menu_group_id_list to be added
        menu_group_id_list_to_add = list(set(menu_group_id_list) - set(existing_menu_group_id_list))
        if len(menu_group_id_list_to_add) > 0:
            query_params = ""
            for menu_group_id in menu_group_id_list_to_add:
                query_params += f"({plan_id}, {menu_group_id}, 'active', {g.user_id}),"
            
            if query_params:
                query_params = query_params[:-1]
                query = text(f"""
                    INSERT INTO plan_menu_group_map (plan_id, menu_group_id, meta_status, creation_user_id)
                    VALUES {query_params}
                """)
                result = conn.execute(query).rowcount
                assert result == len(menu_group_id_list_to_add), "unable to create plan_menu_group_map"
        
        # get menu_group_id_list to be deleted
        menu_group_id_list_to_delete = list(set(existing_menu_group_id_list) - set(menu_group_id_list))
        if len(menu_group_id_list_to_delete) > 0:
            query = text(f"""
                UPDATE plan_menu_group_map
                SET meta_status = :meta_status, deletion_user_id = :deletion_user_id, deletion_timestamp = :deletion_timestamp
                WHERE plan_id = :plan_id
                AND menu_group_id IN :menu_group_id_list_to_delete
            """)
            result = conn.execute(query, meta_status='deleted', plan_id=plan_id, menu_group_id_list_to_delete=menu_group_id_list_to_delete,
                                    deletion_user_id=g.user_id, deletion_timestamp=jqutils.get_utc_datetime()).rowcount
            assert result == len(menu_group_id_list_to_delete), "unable to delete menu_groups"

    response_body = {
        "data": {},
        "action": "update_plan",
        "status": "successful"
    }
    return jsonify(response_body)

@plan_management_blueprint.route('/plan/<plan_id>', methods=['DELETE'])
def delete_plan(plan_id):
    db_engine = jqutils.get_db_engine()
    
    with db_engine.connect() as conn:
        query = text("""
            SELECT meta_status
            FROM plan
            WHERE plan_id = :plan_id
        """)
        result = conn.execute(query, plan_id=plan_id).fetchone()
        assert result, f"unable to get plan_id: {plan_id}"
        
        if result["meta_status"] != "deleted":
            action_timestamp = jqutils.get_utc_datetime()
            
            query = text("""
                UPDATE plan_menu_group_map
                SET meta_status = :meta_status, deletion_user_id = :deletion_user_id, deletion_timestamp = :deletion_timestamp
                WHERE plan_id = :plan_id
            """)
            conn.execute(query, meta_status="deleted", deletion_user_id=g.user_id, deletion_timestamp=action_timestamp, plan_id=plan_id)
            
            query = text("""
                UPDATE plan
                SET meta_status = :meta_status, deletion_user_id = :deletion_user_id, deletion_timestamp = :deletion_timestamp
                WHERE plan_id = :plan_id
            """)
            result = conn.execute(query, meta_status="deleted", deletion_user_id=g.user_id, deletion_timestamp=action_timestamp, plan_id=plan_id).rowcount
            assert result, f"unable to delete plan_id: {plan_id}"
   
    response_body = {
        "action": "delete_plan",
        "status": "successful"
    }
    return jsonify(response_body)

@plan_management_blueprint.route('/plans', methods=['GET'])
def get_plans():
    db_engine = jqutils.get_db_engine()

    query = text("""
        SELECT plan_id, external_plan_id, brand_profile_id, plan_name
        FROM plan
        WHERE meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, meta_status="active").fetchall()

    response_body = {
        "data": [dict(row) for row in result],
        "action": "get_plans",
        "status": "successful"
    }
    return jsonify(response_body)

@plan_management_blueprint.route('/plan/<plan_id>/menu-group', methods=['GET'])
def get_menu_groups_by_plan(plan_id):
    menu_group_id = int(menu_group_id)
    
    db_engine = jqutils.get_db_engine()
    
    query = text("""
        SELECT mg.menu_group_id, mg.menu_group_name, mg.external_menu_group_id
        FROM (
            SELECT brand_profile_plan_map_id
            FROM brand_profile_plan_map
            WHERE plan_id = :plan_id
            AND meta_status = :meta_status
        ) bppm
        JOIN brand_profile_plan_menu_group_map bpmgm ON bppm.brand_profile_plan_map_id = bpmgm.brand_profile_plan_map_id
        JOIN menu_group mg ON bpmgm.menu_group_id = mg.menu_group_id
        WHERE bpmgm.meta_status = :meta_status
        AND mg.meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        results = conn.execute(query, plan_id=plan_id, meta_status="active").fetchall()
        menu_group_list = [dict(row) for row in results]
    
    response_body = {
        "data": {
            "menu_group_list": menu_group_list
        },
        "action": "get_menu_groups_by_plan",
        "status": "successful"
    }
    return jsonify(response_body)