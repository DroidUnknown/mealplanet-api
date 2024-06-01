from flask import Blueprint, request, jsonify, g
from sqlalchemy import text

from utils import jqutils
from kitchen_profile_management import kitchen_profile_ninja

kitchen_profile_management_blueprint = Blueprint('kitchen_profile_management', __name__)

@kitchen_profile_management_blueprint.route('/kitchen-profile', methods=['POST'])
def add_kitchen_profile():
    request_data = request.get_json()

    external_kitchen_profile_id = request_data["external_kitchen_profile_id"]
    kitchen_name = request_data["kitchen_name"]
    brand_profile_id = request_data["brand_profile_id"]

    availability_p = kitchen_profile_ninja.check_kitchen_profile_availability(external_kitchen_profile_id)
    if availability_p == 0:
        response_body = {
            "data": {},
            "action": "add_kitchen_profile",
            "status": "failed",
            "message": "External kitchen Profile ID already exists"
        }
        return jsonify(response_body)

    one_dict = {
        "external_kitchen_profile_id": external_kitchen_profile_id,
        "kitchen_name": kitchen_name,
        "brand_profile_id": brand_profile_id,
        "meta_status": "active",
        "creation_user_id": g.user_id
    }

    kitchen_profile_id = jqutils.create_new_single_db_entry(one_dict, "kitchen_profile")
   
    response_body = {
        "data": {
            "kitchen_profile_id": kitchen_profile_id
        },
        "action": "add_kitchen_profile",
        "status": "successful"
    }
    return jsonify(response_body)

@kitchen_profile_management_blueprint.route('/kitchen-profile/<kitchen_profile_id>', methods=['GET'])
def get_kitchen_profile(kitchen_profile_id):
    db_engine = jqutils.get_db_engine()

    query = text("""
        SELECT kp.kitchen_profile_id, kp.external_kitchen_profile_id, kp.kitchen_name, kp.brand_profile_id, bp.brand_name
        FROM kitchen_profile kp
        JOIN brand_profile bp ON kp.brand_profile_id = bp.brand_profile_id
        WHERE kp.kitchen_profile_id = :kitchen_profile_id
        AND kp.meta_status = :meta_status
        AND bp.meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, kitchen_profile_id=kitchen_profile_id, meta_status="active").fetchone()

    if result:
        response_body = {
            "data": dict(result),
            "action": "get_kitchen_profile",
            "status": "successful"
        }
    else:
        response_body = {
            "data": {},
            "action": "get_kitchen_profile",
            "status": "successful",
            "message": "No data found"
        }
    return jsonify(response_body)

@kitchen_profile_management_blueprint.route('/kitchen-profile/<kitchen_profile_id>', methods=['PUT'])
def update_kitchen_profile(kitchen_profile_id):
    request_data = request.get_json()

    external_kitchen_profile_id = request_data["external_kitchen_profile_id"]
    kitchen_name = request_data["kitchen_name"]
    brand_profile_id = request_data["brand_profile_id"]

    availability_p = kitchen_profile_ninja.check_kitchen_profile_availability(external_kitchen_profile_id)
    if availability_p == 0:
        response_body = {
            "data": {},
            "action": "update_kitchen_profile",
            "status": "failed",
            "message": "External kitchen Profile ID already exists"
        }
        return jsonify(response_body)

    one_dict = {
        "external_kitchen_profile_id": external_kitchen_profile_id,
        "kitchen_name": kitchen_name,
        "brand_profile_id": brand_profile_id,
        "modification_user_id": g.user_id
    }

    condition = {
        "kitchen_profile_id": str(kitchen_profile_id),
        "meta_status": 'active'
    }

    jqutils.update_single_db_entry(one_dict, "kitchen_profile", condition)
   
    response_body = {
        "action": "update_kitchen_profile",
        "status": "successful"
    }
    return jsonify(response_body)

@kitchen_profile_management_blueprint.route('/kitchen-profile/<kitchen_profile_id>', methods=['DELETE'])
def delete_kitchen_profile(kitchen_profile_id):
    one_dict = {
        "meta_status": "deleted",
        "deletion_user_id": g.user_id,
        "deletion_timestamp": jqutils.get_utc_datetime()
    }

    condition = {
        "kitchen_profile_id": str(kitchen_profile_id)
    }

    jqutils.update_single_db_entry(one_dict, "kitchen_profile", condition)
   
    response_body = {
        "action": "delete_kitchen_profile",
        "status": "successful"
    }
    return jsonify(response_body)

@kitchen_profile_management_blueprint.route('/kitchen-profiles', methods=['GET'])
def get_kitchen_profiles():
    db_engine = jqutils.get_db_engine()

    query = text("""
        SELECT kp.kitchen_profile_id, kp.external_kitchen_profile_id, kp.kitchen_name, kp.brand_profile_id, bp.brand_name
        FROM kitchen_profile kp
        JOIN brand_profile bp ON kp.brand_profile_id = bp.brand_profile_id
        WHERE kp.meta_status = :meta_status
        AND bp.meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, meta_status="active").fetchall()

    response_body = {
        "data": [dict(row) for row in result],
        "action": "get_kitchen_profiles",
        "status": "successful"
    }
    return jsonify(response_body)
