from flask import Blueprint, request, jsonify, g
from sqlalchemy import text

from utils import jqutils
from brand_profile_management import brand_profile_ninja
from plan_management import plan_ninja

brand_profile_management_blueprint = Blueprint('brand_profile_management', __name__)

@brand_profile_management_blueprint.route('/brand-profile/availability', methods=['POST'])
def check_brand_profile_availability():
    request_json = request.get_json()
    brand_profile_name = request_json["brand_profile_name"]

    availability_p = brand_profile_ninja.check_brand_profile_availability(brand_profile_name)

    response_body = {
        "data": {
            "availability_p": availability_p
        },
        "action": "check_brand_profile_availability",
        "status": "successful"
    }
    return jsonify(response_body)

@brand_profile_management_blueprint.route('/brand-profile', methods=['POST'])
def add_brand_profile():
    request_json = request.get_json()

    brand_profile_name = request_json["brand_profile_name"]
    external_brand_profile_id = request_json["external_brand_profile_id"]
    plan_list = request_json.get("plan_list", [])

    brand_profile_available = brand_profile_ninja.check_brand_profile_availability(brand_profile_name)
    if not brand_profile_available:
        response_body = {
            "data": {},
            "action": "add_brand_profile",
            "status": "failed",
            "message": "brand profile name already exists"
        }
        return jsonify(response_body)

    db_engine = jqutils.get_db_engine()
    
    with db_engine.connect() as conn:        
        query = text("""
            INSERT INTO brand_profile (brand_profile_name, external_brand_profile_id, meta_status, creation_user_id)
            VALUES (:brand_profile_name, :external_brand_profile_id, :meta_status, :creation_user_id)
        """)
        brand_profile_id = conn.execute(query, brand_profile_name=brand_profile_name, creation_user_id=g.user_id,
                            external_brand_profile_id=external_brand_profile_id, meta_status="active").lastrowid
        assert brand_profile_id, "unable to generate brand_profile_id"
   
        for one_plan in plan_list:
            plan_id = one_plan["plan_id"]
            menu_group_id_list = one_plan.get("menu_group_id_list", [])
            
            query = text("""
                INSERT INTO brand_profile_plan_map (brand_profile_id, plan_id, meta_status, creation_user_id)
                VALUES (:brand_profile_id, :plan_id, :meta_status, :creation_user_id)
            """)
            brand_profile_plan_map_id = conn.execute(query, brand_profile_id=brand_profile_id, plan_id=plan_id, meta_status="active", creation_user_id=g.user_id).lastrowid
            assert brand_profile_plan_map_id, f"unable to associate plan_id: {plan_id} with brand_profile_id: {brand_profile_id}"
            
            for menu_group_id in menu_group_id_list:
                query = text("""
                    INSERT INTO brand_profile_plan_menu_group_map (brand_profile_plan_map_id, menu_group_id, meta_status, creation_user_id)
                    VALUES (:brand_profile_plan_map_id, :menu_group_id, :meta_status, :creation_user_id)
                """)
                brand_profile_plan_menu_group_map_id = conn.execute(query, brand_profile_plan_map_id=brand_profile_plan_map_id, menu_group_id=menu_group_id, meta_status="active", creation_user_id=g.user_id)
                assert brand_profile_plan_menu_group_map_id, f"unable to associate menu_group_id: {menu_group_id} with brand_profile_plan_map_id: {brand_profile_plan_map_id}"

    response_body = {
        "data": {
            "brand_profile_id": brand_profile_id
        },
        "action": "add_brand_profile",
        "status": "successful"
    }
    return jsonify(response_body)

@brand_profile_management_blueprint.route('/brand-profile/<brand_profile_id>', methods=['GET'])
def get_brand_profile(brand_profile_id):
    brand_profile_id = int(brand_profile_id)
    
    db_engine = jqutils.get_db_engine()
    
    # get brand profile details
    query = text("""
        SELECT brand_profile_id, brand_profile_name, external_brand_profile_id
        FROM brand_profile
        WHERE brand_profile_id = :brand_profile_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, brand_profile_id=brand_profile_id, meta_status="active").fetchone()
        assert result, "brand profile does not exist"

        # get plan list for brand_profile
        brand_profile_id = result["brand_profile_id"]
        plan_list = brand_profile_ninja.get_brand_profile_plan_list(brand_profile_id, menu_group_info_p=True)
        
    response_body = {
        "data": {
            "brand_profile_id": brand_profile_id,
            "brand_profile_name": result["brand_profile_name"],
            "external_brand_profile_id": result["external_brand_profile_id"],
            "plan_list": plan_list
        },
        "action": "get_brand_profile",
        "status": "successful"
    }
    return jsonify(response_body)

@brand_profile_management_blueprint.route('/brand-profile/<brand_profile_id>', methods=['PUT'])
def update_brand_profile(brand_profile_id):
    brand_profile_id = int(brand_profile_id)
    
    request_json = request.get_json()

    brand_profile_name = request_json["brand_profile_name"]
    external_brand_profile_id = request_json["external_brand_profile_id"]

    brand_profile_name_available = brand_profile_ninja.check_brand_profile_availability(external_brand_profile_id, brand_profile_name)
    if not brand_profile_name_available:
        response_body = {
            "data": {},
            "action": "update_brand_profile",
            "status": "failed",
            "message": "brand profile name already in use"
        }
        return jsonify(response_body)

    db_engine = jqutils.get_db_engine()
    
    # update brand profile details
    query = text("""
        UPDATE brand_profile
        SET external_brand_profile_id = :external_brand_profile_id,
            brand_profile_name = :brand_profile_name,
            modification_user_id = :modification_user_id
        WHERE brand_profile_id = :brand_profile_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        conn.execute(query, external_brand_profile_id=external_brand_profile_id, brand_profile_name=brand_profile_name, modification_user_id=g.user_id, brand_profile_id=brand_profile_id, meta_status="active")
   
    response_body = {
        "data": {},
        "action": "update_brand_profile",
        "status": "successful"
    }
    return jsonify(response_body)

@brand_profile_management_blueprint.route('/brand-profile/<brand_profile_id>', methods=['DELETE'])
def delete_brand_profile(brand_profile_id):
    brand_profile_id = int(brand_profile_id)
    
    db_engine = jqutils.get_db_engine()
    
    query = text("""
        SELECT meta_status, deletion_user_id, deletion_timestamp
        FROM brand_profile
        WHERE brand_profile_id = :brand_profile_id
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, brand_profile_id=brand_profile_id).fetchone()
        assert result, "brand profile does not exist"
        
        if result["meta_status"] != "deleted":
            action_timestamp = jqutils.get_utc_datetime()
            
            query = text("""
                UPDATE brand_profile
                SET meta_status = :meta_status,
                deletion_user_id = :deletion_user_id,
                deletion_timestamp = :deletion_timestamp
                WHERE brand_profile_id = :brand_profile_id
            """)
            result = conn.execute(query, meta_status="deleted", deletion_user_id=g.user_id, deletion_timestamp=action_timestamp, brand_profile_id=brand_profile_id).rowcount
            assert result, "unable to delete brand profile"
    
    response_body = {
        "data": {},
        "action": "delete_brand_profile",
        "status": "successful"
    }
    return jsonify(response_body)

@brand_profile_management_blueprint.route('/brand-profiles', methods=['GET'])
def get_brand_profiles():
    db_engine = jqutils.get_db_engine()

    query = text("""
        SELECT brand_profile_id, external_brand_profile_id, brand_profile_name
        FROM brand_profile
        WHERE meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, meta_status="active").fetchall()

    response_body = {
        "data": [dict(row) for row in result],
        "action": "get_brand_profiles",
        "status": "successful"
    }
    return jsonify(response_body)

@brand_profile_management_blueprint.route('/brand-profile/<brand_profile_id>/plans', methods=['GET'])
def get_plans_by_brand_profile(brand_profile_id):
    brand_profile_id = int(brand_profile_id)
    
    request_args = request.args
    menu_group_info_p = True if request_args.get("menu_group_info_p") == "1" else False
    
    plan_list = brand_profile_ninja.get_brand_profile_plan_list(brand_profile_id, menu_group_info_p)

    response_body = {
        "data": {
            "brand_profile_id": brand_profile_id,
            "plan_list": plan_list
        },
        "action": "get_plans_by_brand_profile",
        "status": "successful"
    }
    return jsonify(response_body)
