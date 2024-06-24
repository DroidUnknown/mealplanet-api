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

    available_p = plan_ninja.check_plan_name_availability(plan_name, brand_profile_id)

    response_body = {
        "data": {
            "available_p": available_p
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
            "data": {
                "plan_name": plan_name
            },
            "action": "add_plan",
            "status": "failed",
            "message": "Plan name already in use."
        }
        return jsonify(response_body)

    plan_id = plan_ninja.add_plan(brand_profile_id, plan_name, external_plan_id, menu_group_id_list, g.user_id)
    assert plan_id, "unable to create plan"

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
            "data": {
                "plan_name": plan_name
            },
            "action": "update_plan",
            "status": "failed",
            "message": "Plan name already in use."
        }
        return jsonify(response_body)

    plan_ninja.update_plan(plan_id, plan_name, external_plan_id, menu_group_id_list, g.user_id)

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
    request_args = request.args
    brand_profile_id_list = request_args.get("brand_profile_id_list")
    
    brand_profile_id_filter_statement = ""
    if brand_profile_id_list:
        brand_profile_id_list = brand_profile_id_list.split(",")
        brand_profile_id_filter_statement = "AND brand_profile_id IN :brand_profile_id_list"
    
    db_engine = jqutils.get_db_engine()

    query = text(f"""
        SELECT p.plan_id, p.plan_name, p.external_plan_id, bp.brand_profile_id, bp.brand_profile_name, bp.external_brand_profile_id
        FROM (
            SELECT plan_id, plan_name, external_plan_id, brand_profile_id
            FROM plan
            WHERE meta_status = :meta_status
            {brand_profile_id_filter_statement}
        ) p
        JOIN brand_profile bp ON p.brand_profile_id = bp.brand_profile_id
        WHERE bp.meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        results = conn.execute(query, brand_profile_id_list=brand_profile_id_list, meta_status="active").fetchall()
        
        brand_profile_id_plan_map = {}
        for one_plan in results:
            brand_profile_id = one_plan["brand_profile_id"]
            
            if brand_profile_id not in brand_profile_id_plan_map:
                brand_profile_id_plan_map[brand_profile_id] = {
                    "brand_profile_id": brand_profile_id,
                    "brand_profile_name": one_plan["brand_profile_name"],
                    "external_brand_profile_id": one_plan["external_brand_profile_id"],
                    "plan_list": []
                }
            
            brand_profile_id_plan_map[brand_profile_id]["plan_list"].append({
                "plan_id": one_plan["plan_id"],
                "plan_name": one_plan["plan_name"],
                "external_plan_id": one_plan["external_plan_id"],
            })

    response_body = {
        "data": brand_profile_id_plan_map.values(),
        "action": "get_plans",
        "status": "successful"
    }
    return jsonify(response_body)

@plan_management_blueprint.route('/plan/<plan_id>/menu-groups', methods=['GET'])
def get_menu_groups_by_plan(plan_id):
    plan_id = int(plan_id)
    
    db_engine = jqutils.get_db_engine()
    
    query = text("""
        SELECT pmgm.plan_menu_group_map_id, mg.menu_group_id, mg.menu_group_name, mg.external_menu_group_id
        FROM (
            SELECT plan_menu_group_map_id, menu_group_id
            FROM plan_menu_group_map
            WHERE plan_id = :plan_id
            AND meta_status = :meta_status
        ) pmgm
        JOIN menu_group mg ON pmgm.menu_group_id = mg.menu_group_id
        WHERE mg.meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        results = conn.execute(query, plan_id=plan_id, meta_status="active").fetchall()
        menu_group_list = [dict(row) for row in results]
    
    response_body = {
        "data": {
            "plan_id": plan_id,
            "menu_group_list": menu_group_list
        },
        "action": "get_menu_groups_by_plan",
        "status": "successful"
    }
    return jsonify(response_body)