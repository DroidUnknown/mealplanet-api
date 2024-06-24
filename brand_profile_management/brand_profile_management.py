from flask import Blueprint, request, jsonify, g
from sqlalchemy import text

from utils import jqutils
from brand_profile_management import brand_profile_ninja
from plan_management import plan_ninja

brand_profile_management_blueprint = Blueprint('brand_profile_management', __name__)

@brand_profile_management_blueprint.route('/brand-profile/availability', methods=['POST'])
def check_brand_profile_name_availability():
    request_json = request.get_json()
    brand_profile_name = request_json["brand_profile_name"]

    available_p = brand_profile_ninja.check_brand_profile_name_availability(brand_profile_name)

    response_body = {
        "data": {
            "available_p": available_p
        },
        "action": "check_brand_profile_name_availability",
        "status": "successful"
    }
    return jsonify(response_body)

@brand_profile_management_blueprint.route('/brand-profile', methods=['POST'])
def add_brand_profile():
    request_json = request.get_json()

    brand_profile_name = request_json["brand_profile_name"]
    external_brand_profile_id = request_json["external_brand_profile_id"]
    plan_list = request_json["plan_list"]

    available_p = brand_profile_ninja.check_brand_profile_name_availability(brand_profile_name)
    if not available_p:
        response_body = {
            "data": {},
            "action": "add_brand_profile",
            "status": "failed",
            "message": "Brand profile name already in use."
        }
        return jsonify(response_body)

    already_handled_plan_name_list = []
    validated_plan_list = []
    for one_plan in plan_list:
        plan_name = one_plan["plan_name"]
        external_plan_id = one_plan["external_plan_id"]
        menu_group_id_list = one_plan["menu_group_id_list"]
        
        if plan_name not in already_handled_plan_name_list:
            validated_plan_list.append({
                "plan_name": plan_name,
                "external_plan_id": external_plan_id,
                "menu_group_id_list": list(set(menu_group_id_list))
            })

    db_engine = jqutils.get_db_engine()
    
    with db_engine.connect() as conn:        
        query = text("""
            INSERT INTO brand_profile (brand_profile_name, external_brand_profile_id, meta_status, creation_user_id)
            VALUES (:brand_profile_name, :external_brand_profile_id, :meta_status, :creation_user_id)
        """)
        brand_profile_id = conn.execute(query, brand_profile_name=brand_profile_name, creation_user_id=g.user_id,
                            external_brand_profile_id=external_brand_profile_id, meta_status="active").lastrowid
        assert brand_profile_id, "unable to generate brand_profile_id"
   
        for one_plan in validated_plan_list:
            plan_name = one_plan["plan_name"]
            external_plan_id = one_plan["external_plan_id"]
            menu_group_id_list = one_plan["menu_group_id_list"]
            
            query = text("""
                INSERT INTO plan (brand_profile_id, plan_name, external_plan_id, meta_status, creation_user_id)
                VALUES (:brand_profile_id, :plan_name, :external_plan_id, :meta_status, :creation_user_id)
            """)
            plan_id = conn.execute(query, brand_profile_id=brand_profile_id, plan_name=plan_name, external_plan_id=external_plan_id, meta_status="active", creation_user_id=g.user_id).lastrowid
            assert plan_id, f"unable to create plan_id for plan_name: {plan_name}"
            
            query_params = ""
            for menu_group_id in menu_group_id_list:
                query_params += f"({plan_id}, {menu_group_id}, 'active', {g.user_id}),"
            
            if query_params:
                query_params = query_params[:-1]
            
                query = text(f"""
                    INSERT INTO plan_menu_group_map (plan_id, menu_group_id, meta_status, creation_user_id)
                    VALUES {query_params}
                """)
                results = conn.execute(query).rowcount
                assert results == len(menu_group_id_list), "unable to create plan_menu_group_map"

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

    brand_profile_detail = {
        "brand_profile_id": brand_profile_id,
        "brand_profile_name": result["brand_profile_name"],
        "external_brand_profile_id": result["external_brand_profile_id"],
        "plan_list": plan_list,
        "brand_profile_image_list": []
    }
    
    # get brand profile image
    query = text("""
        SELECT brand_profile_image_id, image_type, image_bucket_name, image_object_key
        FROM brand_profile_image
        WHERE brand_profile_id = :brand_profile_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, brand_profile_id=brand_profile_id, meta_status="active").fetchone()
        
        if result:
            brand_profile_image_id = result["brand_profile_image_id"]
            image_type = result["image_type"]
            image_bucket_name = result["image_bucket_name"]
            image_object_key = result["image_object_key"]
            
            assert image_bucket_name and image_object_key, "unable to generate image_url"
            image_url = jqutils.get_s3_image_url(image_bucket_name, image_object_key)
            
            brand_profile_detail["brand_profile_image_list"].append({
                "brand_profile_image_id": brand_profile_image_id,
                "image_type": image_type,
                "image_url": image_url
            })
    
    response_body = {
        "data": brand_profile_detail,
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
    plan_list = request_json["plan_list"]

    available_p = brand_profile_ninja.check_brand_profile_name_availability(brand_profile_name, brand_profile_id)
    if not available_p:
        response_body = {
            "data": {},
            "action": "update_brand_profile",
            "status": "failed",
            "message": "brand profile name already in use"
        }
        return jsonify(response_body)

    db_engine = jqutils.get_db_engine()
    
    with db_engine.connect() as conn:
        # update brand profile details
        query = text("""
            UPDATE brand_profile
            SET external_brand_profile_id = :external_brand_profile_id,
                brand_profile_name = :brand_profile_name,
                modification_user_id = :modification_user_id
            WHERE brand_profile_id = :brand_profile_id
            AND meta_status = :meta_status
        """)
        result = conn.execute(query, external_brand_profile_id=external_brand_profile_id, brand_profile_name=brand_profile_name, modification_user_id=g.user_id, brand_profile_id=brand_profile_id, meta_status="active").rowcount
        assert result, "unable to update brand profile"

        # get existing plan_id_list
        query = text("""
            SELECT plan_id, plan_name
            FROM plan
            WHERE brand_profile_id = :brand_profile_id
            AND meta_status = :meta_status
        """)
        results = conn.execute(query, brand_profile_id=brand_profile_id, meta_status="active").fetchall()
        existing_plan_id_list = [row["plan_id"] for row in results]
        
        # figure out plan_list to be added or updated
        plan_list_to_be_added = []
        for one_plan in plan_list:
            plan_id = one_plan["plan_id"]
            plan_name = one_plan["plan_name"]
            external_plan_id = one_plan["external_plan_id"]
            menu_group_id_list = one_plan["menu_group_id_list"]
            
            if plan_id is None:
                available_p = plan_ninja.check_plan_name_availability(plan_name, brand_profile_id)
                if not available_p:
                    response_body = {
                        "data": {},
                        "action": "update_brand_profile",
                        "status": "failed",
                        "message": "plan name already in use"
                    }
                    return jsonify(response_body)
                
                plan_list_to_be_added.append({
                    "plan_name": plan_name,
                    "external_plan_id": external_plan_id,
                    "menu_group_id_list": list(set(menu_group_id_list))
                })
            else:
                plan_ninja.update_plan(plan_id, plan_name, external_plan_id, menu_group_id_list, g.user_id)
        
        query_params = ""
        for one_plan in plan_list_to_be_added:
            plan_name = one_plan["plan_name"]
            external_plan_id = one_plan["external_plan_id"]
            query_params += f"({brand_profile_id}, '{one_plan['plan_name']}', '{one_plan['external_plan_id']}', 'active', {g.user_id}),"
        
        if query_params:
            query_params = query_params[:-1]
            query = text(f"""
                INSERT INTO plan (brand_profile_id, plan_name, external_plan_id, meta_status, creation_user_id)
                VALUES {query_params}
            """)
            results = conn.execute(query).rowcount
            assert results == len(plan_list_to_be_added), "unable to create new plans"
        
        # Delete plans that are not in the plan_list anymore
        expected_plan_id_list = [one_plan["plan_id"] for one_plan in plan_list if one_plan["plan_id"] is not None]
        plan_id_list_to_be_deleted = list(set(existing_plan_id_list) - set(expected_plan_id_list))
        
        if plan_id_list_to_be_deleted:
            query = text("""
                UPDATE plan_menu_group_map
                SET meta_status = :meta_status, deletion_user_id = :deletion_user_id, deletion_timestamp = :deletion_timestamp
                WHERE plan_id IN :plan_id_list
            """)
            result = conn.execute(query, meta_status="deleted", deletion_user_id=g.user_id, deletion_timestamp=jqutils.get_utc_datetime(),
                            plan_id_list=plan_id_list_to_be_deleted).rowcount
            assert result == len(plan_id_list_to_be_deleted), "unable to delete plan_menu_group_map"

    response_body = {
        "data": {
            "brand_profile_id": brand_profile_id
        },
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
            
            query = text("""
                UPDATE brand_profile_image
                SET meta_status = :meta_status,
                deletion_user_id = :deletion_user_id,
                deletion_timestamp = :deletion_timestamp
                WHERE brand_profile_id = :brand_profile_id
                AND meta_status = :meta_status_active
            """)
            conn.execute(query, meta_status="deleted", deletion_user_id=g.user_id, deletion_timestamp=action_timestamp, brand_profile_id=brand_profile_id, meta_status_active="active").rowcount
            
            query = text("""
                UPDATE plan_menu_group_map
                SET meta_status = :meta_status,
                deletion_user_id = :deletion_user_id,
                deletion_timestamp = :deletion_timestamp
                WHERE plan_id IN (
                    SELECT plan_id
                    FROM plan
                    WHERE brand_profile_id = :brand_profile_id
                    AND meta_status = :meta_status_active
                )
                AND meta_status = :meta_status_active
            """)
            conn.execute(query, meta_status="deleted", deletion_user_id=g.user_id, deletion_timestamp=action_timestamp, brand_profile_id=brand_profile_id, meta_status_active="active").rowcount
            
            query = text("""
                UPDATE plan
                SET meta_status = :meta_status,
                deletion_user_id = :deletion_user_id,
                deletion_timestamp = :deletion_timestamp
                WHERE brand_profile_id = :brand_profile_id
                AND meta_status = :meta_status_active
            """)
            conn.execute(query, meta_status="deleted", deletion_user_id=g.user_id, deletion_timestamp=action_timestamp, brand_profile_id=brand_profile_id, meta_status_active="active").rowcount

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
        results = conn.execute(query, meta_status="active").fetchall()
        brand_profile_list = [dict(row) for row in results]

    response_body = {
        "data": brand_profile_list,
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
