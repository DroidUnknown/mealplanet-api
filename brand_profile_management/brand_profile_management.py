from flask import Blueprint, request, jsonify, g
from sqlalchemy import text

from utils import jqutils
from brand_profile_management import brand_profile_ninja

brand_profile_management_blueprint = Blueprint('brand_profile_management', __name__)

@brand_profile_management_blueprint.route('/brand-profile/availability', methods=['POST'])
def check_brand_profile_availability():
    request_data = request.get_json()

    external_brand_profile_id = request_data["external_brand_profile_id"]

    availability_p = brand_profile_ninja.check_brand_profile_availability(external_brand_profile_id)

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
    request_data = request.get_json()

    external_brand_profile_id = request_data["external_brand_profile_id"]
    brand_name = request_data["brand_name"]

    availability_p = brand_profile_ninja.check_brand_profile_availability(external_brand_profile_id)
    if availability_p == 0:
        response_body = {
            "data": {},
            "action": "add_brand_profile",
            "status": "failed",
            "message": "External Brand Profile ID already exists"
        }
        return jsonify(response_body)

    one_dict = {
        "external_brand_profile_id": external_brand_profile_id,
        "brand_name": brand_name,
        "meta_status": "active",
        "creation_user_id": g.user_id
    }

    brand_profile_id = jqutils.create_new_single_db_entry(one_dict, "brand_profile")
   
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
    db_engine = jqutils.get_db_engine()

    query = text("""
        SELECT brand_profile_id, external_brand_profile_id, brand_name
        FROM brand_profile
        WHERE brand_profile_id = :brand_profile_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, brand_profile_id=brand_profile_id, meta_status="active").fetchone()

    if result:
        response_body = {
            "data": dict(result),
            "action": "get_brand_profile",
            "status": "successful"
        }
    else:
        response_body = {
            "data": {},
            "action": "get_brand_profile",
            "status": "successful",
            "message": "No data found"
        }
    return jsonify(response_body)

@brand_profile_management_blueprint.route('/brand-profile/<brand_profile_id>', methods=['PUT'])
def update_brand_profile(brand_profile_id):
    request_data = request.get_json()

    external_brand_profile_id = request_data["external_brand_profile_id"]
    brand_name = request_data["brand_name"]

    availability_p = brand_profile_ninja.check_brand_profile_availability(external_brand_profile_id, brand_profile_id)
    if availability_p == 0:
        response_body = {
            "data": {},
            "action": "update_brand_profile",
            "status": "failed",
            "message": "External Brand Profile ID already exists"
        }
        return jsonify(response_body)

    one_dict = {
        "external_brand_profile_id": external_brand_profile_id,
        "brand_name": brand_name,
        "modification_user_id": g.user_id
    }

    condition = {
        "brand_profile_id": str(brand_profile_id),
        "meta_status": 'active'
    }

    jqutils.update_single_db_entry(one_dict, "brand_profile", condition)
   
    response_body = {
        "action": "update_brand_profile",
        "status": "successful"
    }
    return jsonify(response_body)

@brand_profile_management_blueprint.route('/brand-profile/<brand_profile_id>', methods=['DELETE'])
def delete_brand_profile(brand_profile_id):
    one_dict = {
        "meta_status": "deleted",
        "deletion_user_id": g.user_id,
        "deletion_timestamp": jqutils.get_utc_datetime()
    }

    condition = {
        "brand_profile_id": str(brand_profile_id)
    }

    jqutils.update_single_db_entry(one_dict, "brand_profile", condition)
   
    response_body = {
        "action": "delete_brand_profile",
        "status": "successful"
    }
    return jsonify(response_body)

@brand_profile_management_blueprint.route('/brand-profiles', methods=['GET'])
def get_brand_profiles():
    db_engine = jqutils.get_db_engine()

    query = text("""
        SELECT brand_profile_id, external_brand_profile_id, brand_name
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
    db_engine = jqutils.get_db_engine()

    query = text("""
        SELECT brand_profile_id
        FROM brand_profile
        WHERE brand_profile_id = :brand_profile_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, brand_profile_id=brand_profile_id, meta_status="active").fetchone()

    if result:
        query = text("""
            SELECT plan_id, external_plan_id, brand_profile_id, plan_name
            FROM plan
            WHERE brand_profile_id = :brand_profile_id
            AND meta_status = :meta_status
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, brand_profile_id=brand_profile_id, meta_status="active").fetchall()

        response_body = {
            "data": [dict(row) for row in result],
            "action": "get_plans_by_brand_profile",
            "status": "successful"
        }
    else:
        response_body = {
            "data": {},
            "action": "get_plans_by_brand_profile",
            "status": "successful",
            "message": "No data found"
        }
    return jsonify(response_body)
