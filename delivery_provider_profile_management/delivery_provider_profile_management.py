from flask import Blueprint, request, jsonify, g
from sqlalchemy import text

from utils import jqutils
from delivery_provider_profile_management import delivery_provider_profile_ninja

delivery_provider_profile_management_blueprint = Blueprint('delivery_provider_profile_management', __name__)

@delivery_provider_profile_management_blueprint.route('/delivery-provider-profile', methods=['POST'])
def add_delivery_provider_profile():
    request_data = request.get_json()

    external_delivery_provider_profile_id = request_data["external_delivery_provider_profile_id"]
    delivery_provider_name = request_data["delivery_provider_name"]

    availability_p = delivery_provider_profile_ninja.check_delivery_provider_profile_availability(external_delivery_provider_profile_id)
    if availability_p == 0:
        response_body = {
            "data": {},
            "action": "add_delivery_provider_profile",
            "status": "failed",
            "message": "External Delivery Provider Profile ID already exists"
        }
        return jsonify(response_body)

    one_dict = {
        "external_delivery_provider_profile_id": external_delivery_provider_profile_id,
        "delivery_provider_name": delivery_provider_name,
        "meta_status": "active",
        "creation_user_id": g.user_id
    }

    delivery_provider_profile_id = jqutils.create_new_single_db_entry(one_dict, "delivery_provider_profile")
    
    response_body = {
        "data": {
            "delivery_provider_profile_id": delivery_provider_profile_id
        },
        "action": "add_delivery_provider_profile",
        "status": "successful"
    }
    return jsonify(response_body)

@delivery_provider_profile_management_blueprint.route('/delivery-provider-profile/<delivery_provider_profile_id>', methods=['GET'])
def get_delivery_provider_profile(delivery_provider_profile_id):
    db_engine = jqutils.get_db_engine()

    query = text("""
        SELECT delivery_provider_profile_id, external_delivery_provider_profile_id, delivery_provider_name
        FROM delivery_provider_profile
        WHERE delivery_provider_profile_id = :delivery_provider_profile_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, delivery_provider_profile_id=delivery_provider_profile_id, meta_status="active").fetchone()

    if result:
        response_body = {
            "data": dict(result),
            "action": "get_delivery_provider_profile",
            "status": "successful"
        }
    else:
        response_body = {
            "data": {},
            "action": "get_delivery_provider_profile",
            "status": "successful",
            "message": "No data found"
        }
    return jsonify(response_body)

@delivery_provider_profile_management_blueprint.route('/delivery-provider-profile/<delivery_provider_profile_id>', methods=['PUT'])
def update_delivery_provider_profile(delivery_provider_profile_id):
    request_data = request.get_json()

    external_delivery_provider_profile_id = request_data["external_delivery_provider_profile_id"]
    delivery_provider_name = request_data["delivery_provider_name"]

    availability_p = delivery_provider_profile_ninja.check_delivery_provider_profile_availability(external_delivery_provider_profile_id)
    if availability_p == 0:
        response_body = {
            "data": {},
            "action": "update_delivery_provider_profile",
            "status": "failed",
            "message": "External delivery_provider Profile ID already exists"
        }
        return jsonify(response_body)

    one_dict = {
        "external_delivery_provider_profile_id": external_delivery_provider_profile_id,
        "delivery_provider_name": delivery_provider_name,
        "modification_user_id": g.user_id
    }

    condition = {
        "delivery_provider_profile_id": str(delivery_provider_profile_id),
        "meta_status": 'active'
    }

    jqutils.update_single_db_entry(one_dict, "delivery_provider_profile", condition)
   
    response_body = {
        "action": "update_delivery_provider_profile",
        "status": "successful"
    }
    return jsonify(response_body)

@delivery_provider_profile_management_blueprint.route('/delivery-provider-profile/<delivery_provider_profile_id>', methods=['DELETE'])
def delete_delivery_provider_profile(delivery_provider_profile_id):
    one_dict = {
        "meta_status": "deleted",
        "deletion_user_id": g.user_id,
        "deletion_timestamp": jqutils.get_utc_datetime()
    }

    condition = {
        "delivery_provider_profile_id": str(delivery_provider_profile_id)
    }

    jqutils.update_single_db_entry(one_dict, "delivery_provider_profile", condition)
   
    response_body = {
        "action": "delete_delivery_provider_profile",
        "status": "successful"
    }
    return jsonify(response_body)

@delivery_provider_profile_management_blueprint.route('/delivery-provider-profiles', methods=['GET'])
def get_delivery_provider_profiles():
    db_engine = jqutils.get_db_engine()

    query = text("""
        SELECT delivery_provider_profile_id, external_delivery_provider_profile_id, delivery_provider_name
        FROM delivery_provider_profile
        WHERE meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, meta_status="active").fetchall()

    response_body = {
        "data": [dict(row) for row in result],
        "action": "get_delivery_provider_profiles",
        "status": "successful"
    }
    return jsonify(response_body)
