from flask import Blueprint, request, jsonify, g
from sqlalchemy import text, Table, MetaData

from utils import jqutils
from plan_management import plan_ninja

plan_management_blueprint = Blueprint('plan_management', __name__)

@plan_management_blueprint.route('/plan/availability', methods=['POST'])
def check_plan_availability():
    request_data = request.get_json()

    external_plan_id = request_data["external_plan_id"]

    availability_p = plan_ninja.check_plan_availability(external_plan_id)

    response_body = {
        "data": {
            "availability_p": availability_p
        },
        "action": "check_plan_availability",
        "status": "successful"
    }
    return jsonify(response_body)

@plan_management_blueprint.route('/plan', methods=['POST'])
def add_plan():
    request_data_list = request.get_json()

    dict_list = []
    for request_data in request_data_list:
        external_plan_id = request_data["external_plan_id"]
        availability_p = plan_ninja.check_plan_availability(external_plan_id)
        if availability_p == 0:
            response_body = {
                "data": {},
                "action": "add_plan",
                "status": "failed",
                "message": f"External Brand Profile ID: '{external_plan_id}' already exists"
            }
            return jsonify(response_body)

        dict_list.append({
            "external_plan_id": request_data["external_plan_id"],
            "plan_name": request_data["plan_name"],
            "brand_profile_id": request_data["brand_profile_id"],
            "meta_status": "active",
            "creation_user_id": g.user_id
        })

    plan_id_list = []
    db_engine = jqutils.get_db_engine()
    metadata = MetaData(bind=db_engine)
    plan_table = Table('PLAN', metadata, autoload_with=db_engine)

    with db_engine.connect() as conn:
        for row in dict_list:
            result = conn.execute(plan_table.insert(), row)
            plan_id_list.append(result.inserted_primary_key[0])

    response_body = {
        "data": {
            "plan_id_list": plan_id_list
        },
        "action": "add_plan",
        "status": "successful"
    }
    return jsonify(response_body)

@plan_management_blueprint.route('/plan/<plan_id>', methods=['GET'])
def get_plan(plan_id):
    db_engine = jqutils.get_db_engine()

    query = text("""
        SELECT plan_id, external_plan_id, brand_profile_id, plan_name
        FROM plan
        WHERE plan_id = :plan_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, plan_id=plan_id, meta_status="active").fetchone()

    if result:
        response_body = {
            "data": dict(result),
            "action": "get_plan",
            "status": "successful"
        }
    else:
        response_body = {
            "data": {},
            "action": "get_plan",
            "status": "successful",
            "message": "No data found"
        }
    return jsonify(response_body)

@plan_management_blueprint.route('/plan/<plan_id>', methods=['PUT'])
def update_plan(plan_id):
    request_data = request.get_json()

    external_plan_id = request_data["external_plan_id"]
    brand_profile_id = request_data["brand_profile_id"]
    plan_name = request_data["plan_name"]

    availability_p = plan_ninja.check_plan_availability(external_plan_id)
    if availability_p == 0:
        response_body = {
            "data": {},
            "action": "update_plan",
            "status": "failed",
            "message": "External Brand Profile ID already exists"
        }
        return jsonify(response_body)

    one_dict = {
        "external_plan_id": external_plan_id,
        "brand_profile_id": brand_profile_id,
        "plan_name": plan_name,
        "modification_user_id": g.user_id
    }

    condition = {
        "plan_id": str(plan_id),
        "meta_status": 'active'
    }

    jqutils.update_single_db_entry(one_dict, "plan", condition)
   
    response_body = {
        "action": "update_plan",
        "status": "successful"
    }
    return jsonify(response_body)

@plan_management_blueprint.route('/plan/<plan_id>', methods=['DELETE'])
def delete_plan(plan_id):
    one_dict = {
        "meta_status": "deleted",
        "deletion_user_id": g.user_id,
        "deletion_timestamp": jqutils.get_utc_datetime()
    }

    condition = {
        "plan_id": str(plan_id)
    }

    jqutils.update_single_db_entry(one_dict, "plan", condition)
   
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