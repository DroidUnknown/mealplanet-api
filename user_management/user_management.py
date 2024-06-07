import os
import json
import traceback
import logging
import uuid

from datetime import datetime, timedelta
from sqlalchemy import text
from flask import Blueprint, request, jsonify, g
from utils import keycloak_utils, jqutils, jqimage_uploader, aws_utils, jqsecurity
from data_migration_management.data_migration_manager import DataMigrationManager

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger.setLevel(logging.INFO)

user_management_blueprint = Blueprint('user_management', __name__)

@user_management_blueprint.route('/user', methods=['POST'])
def add_user():
    request_json = request.get_json()

    first_names_en = request_json["first_names_en"]
    last_name_en = request_json["last_name_en"]
    first_names_ar = request_json["first_names_ar"]
    last_name_ar = request_json["last_name_ar"]
    phone_nr = request_json["phone_nr"]
    email = request_json["email"]
    role_id_list = request_json["role_id_list"]
    brand_profile_list = request_json["brand_profile_list"]

    one_dict = {
        "first_names_en": first_names_en,
        "last_name_en": last_name_en,
        "first_names_ar": first_names_ar,
        "last_name_ar": last_name_ar,
        "phone_nr": phone_nr,
        "email": email,
        "meta_status": "active",
        "creation_user_id": g.user_id
    }

    user_id = jqutils.create_new_single_db_entry(one_dict, "user")

    for role_id in role_id_list:
        one_dict = {
            "user_id": user_id,
            "role_id": role_id,
            "meta_status": "active",
            "creation_user_id": g.user_id
        }
        jqutils.create_new_single_db_entry(one_dict, "user_role_map")

    for brand_profile in brand_profile_list:
        brand_profile_id = brand_profile["brand_profile_id"]
        module_access_id_list = brand_profile["module_access_id_list"]

        for module_access_id in module_access_id_list:

            one_dict = {
                "user_id": user_id,
                "brand_profile_id": brand_profile_id,
                "module_access_id": module_access_id,
                "meta_status": "active",
                "creation_user_id": g.user_id
            }
            jqutils.create_new_single_db_entry(one_dict, "user_brand_profile_module_access")

    # create OTP request
    otp = str(uuid.uuid4())
    otp_requested_timestamp_str = jqutils.get_utc_datetime()

    # convert str to datetime
    otp_requested_timestamp = datetime.strptime(otp_requested_timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
    otp_expiry_timestamp = otp_requested_timestamp + timedelta(minutes=5)

    contact_method = "email"

    one_dict = {
        "user_id": user_id,
        "intent": "user_signup",
        "contact_method": contact_method,
        "otp": otp,
        "otp_request_count": 0,
        "otp_requested_timestamp": otp_requested_timestamp_str,
        "otp_expiry_timestamp": otp_expiry_timestamp,
        "otp_status": "pending",
        "meta_status": "active",
        "creation_user_id": g.user_id
    }
    one_time_password_id = jqutils.create_new_single_db_entry(one_dict, "one_time_password")

    # generate verification link
    fe_base_url = os.getenv("FE_PORTAL_WEB_URL")
    verification_link = fe_base_url + "/reset-password/" + otp
    
    # send OTP to user email
    if os.getenv("MOCK_AWS_NOTIFICATIONS") != "1":
        if contact_method == 'email':
            aws_utils.publish_email(
                source="noreply@iblinknext.com",
                destination={
                    "ToAddresses": [email],
                },
            subject=f"OTP Verification Link",
                text=f"Hi,\n\nYou can verify your otp by opening this link: {verification_link}\n\nRegards,\nMP Team",
                html=f"Hi,\n\nYou can verify your otp by opening this link: {verification_link}\n\nRegards,\nMP Team"
            )

    # update OTP status to sent
    one_dict = {
        "otp_status": "sent"
    }
    condition = {
        "one_time_password_id": str(one_time_password_id)
    }
    jqutils.update_single_db_entry(one_dict, "one_time_password", condition)

    response_body = {
        "data": {
            "user_id": user_id
        },
        "action": "add_user",
        "status": "successful"
    }
    return jsonify(response_body)

@user_management_blueprint.route('/user/<user_id>/upload-image', methods=['POST'])
def add_user_image(user_id):
    request_dict = request.form.to_dict()

    image_type = request_dict["image_type"]

    user_image = request.files.get('user_image')

    # upload user image to S3
    user_image_url = None

    if user_image:
        file_name = user_image.filename

        if file_name != '':

            file_extension = file_name.rsplit('.', 1)[1].lower()
            image_bucket_name = os.getenv("S3_BUCKET_NAME")
            image_object_key = f"user-images/{user_id}/{file_name}.{file_extension}"

            # Upload image to S3 if not mocking
            if os.getenv("MOCK_S3_UPLOAD") != '1':
                    
                is_uploaded = jqimage_uploader.upload_fileobj(user_image, image_bucket_name, image_object_key)
                assert is_uploaded, "failed to upload item image to S3"
    
                user_image_url = jqimage_uploader.create_presigned_url(image_bucket_name, image_object_key)

                one_dict = {
                    "user_id": user_id,
                    "image_type": image_type,
                    "image_bucket_name": image_bucket_name,
                    "image_object_key": image_object_key,
                    "meta_status": "active",
                    "creation_user_id": g.user_id
                }

                jqutils.create_new_single_db_entry(one_dict, "user_image_map")

    response_body = {
        "data": {
            "user_image_url": user_image_url
        },
        "action": "add_user_image",
        "status": "successful"
    }
    return jsonify(response_body)

@user_management_blueprint.route('/user/<user_id>/verify-otp', methods=['POST'])
def verify_user_otp(user_id):
    request_json = request.get_json()

    username = request_json["username"]
    password = request_json["password"]
    otp = request_json["otp"]
    intent = request_json["intent"]

    db_engine = jqutils.get_db_engine()
    
    # encrypt password and update user
    password_manager = DataMigrationManager()
    encrypted_password = password_manager.encrypt_password(password)

    db_engine = jqutils.get_db_engine()
    
    if intent == "user_signup":
        query = text("""
            SELECT one_time_password_id, user_id, intent, contact_method, otp, otp_request_count,
            otp_requested_timestamp, otp_expiry_timestamp, otp_verified_timestamp, otp_status
            FROM one_time_password
            WHERE user_id = :user_id
            AND intent = :intent
            AND contact_method = :contact_method
            AND meta_status = :meta_status
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, user_id=user_id, intent=intent, contact_method="email", meta_status="active").fetchone()

        if result:
            otp_db = result["otp"]
            otp_expiry_timestamp = result["otp_expiry_timestamp"]

            if otp_db == otp:
                # convert str to datetime
                current_timestamp_str = jqutils.get_utc_datetime()
                current_timestamp = datetime.strptime(current_timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
                one_time_password_id = result["one_time_password_id"]

                if otp_expiry_timestamp > current_timestamp:
                    if result["otp_status"] == "verified":
                        response_body = {
                            "data": {},
                            "action": "verify_otp",
                            "status": "failed",
                            "message": "OTP already verified"
                        }
                        return jsonify(response_body)
                    
                    query = text("""
                        UPDATE one_time_password
                        SET otp_status = :otp_status
                        WHERE one_time_password_id = :one_time_password_id
                    """)
                    with db_engine.connect() as conn:
                        conn.execute(query, otp_status="verified", one_time_password_id=one_time_password_id)

                    # get user details
                    query = text("""
                        SELECT first_names_en, last_name_en, email
                        FROM user
                        WHERE user_id = :user_id
                        AND meta_status = :meta_status
                    """)
                    with db_engine.connect() as conn:
                        result = conn.execute(query, user_id=user_id, meta_status="active").fetchone()

                    first_names_en = result["first_names_en"]
                    last_name_en = result["last_name_en"]
                    email = result["email"]

                    # create keycloak user
                    keycloak_user_id = keycloak_utils.create_user(username, password, first_names_en, last_name_en, email)

                    # update user details
                    query = text("""
                        UPDATE user
                        SET keycloak_user_id = :keycloak_user_id,
                        username = :username,
                        password = :password
                        WHERE user_id = :user_id
                    """)
                    with db_engine.connect() as conn:
                        conn.execute(query, keycloak_user_id=keycloak_user_id, username=username, password=encrypted_password, user_id=user_id)

                    response_body = {
                        "data": {
                            "username": username,
                            "keycloak_user_id": keycloak_user_id,
                        },
                        "action": "verify_otp",
                        "status": "successful"
                    }
                    return jsonify(response_body)
                else:
                    query = text("""
                        UPDATE one_time_password
                        SET otp_status = :otp_status
                        WHERE one_time_password_id = :one_time_password_id
                    """)
                    with db_engine.connect() as conn:
                        conn.execute(query, otp_status="expired", one_time_password_id=one_time_password_id)

                    response_body = {
                        "data": {},
                        "action": "verify_otp",
                        "status": "failed",
                        "message": "OTP expired"
                    }
                    return jsonify(response_body)
            else:
                response_body = {
                    "data": {},
                    "action": "verify_otp",
                    "status": "failed",
                    "message": "Invalid OTP"
                }
                return jsonify(response_body)
        else:
            response_body = {
                "data": {},
                "action": "verify_otp",
                "status": "failed",
                "message": "No OTP found"
            }
            return jsonify(response_body)
        
    else:
        response_body = {
            "data": {},
            "action": "verify_otp",
            "status": "failed",
            "message": "Invalid intent"
        }
        return jsonify(response_body)
    
@user_management_blueprint.route('/user/<user_id>', methods=['GET'])
def get_user(user_id):
    db_engine = jqutils.get_db_engine()

    query = text("""
        SELECT u.keycloak_user_id, u.username, u.first_names_en, u.last_name_en, u.first_names_ar, u.last_name_ar, u.phone_nr, u.email,
        uim.image_bucket_name, uim.image_object_key
        FROM user u
        LEFT JOIN user_image_map uim ON u.user_id = uim.user_id
        WHERE u.user_id = :user_id
        AND u.meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        user_result = conn.execute(query, user_id=user_id, meta_status="active").fetchone()

    if user_result:
        user_dict = dict(user_result)

        query = text("""
            SELECT urm.role_id, r.role_name
            FROM user_role_map urm
            JOIN role r ON urm.role_id = r.role_id
            WHERE urm.user_id = :user_id
            AND urm.meta_status = :meta_status
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, user_id=user_id, meta_status="active").fetchall()

        user_dict["role_list"] = [dict(row) for row in result]

        query = text("""
            SELECT ubpma.brand_profile_id, ubpma.module_access_id, bp.brand_name, m.module_id, m.module_name, ma.module_access_id, ma.access_level
            FROM user_brand_profile_module_access ubpma
            JOIN brand_profile bp ON ubpma.brand_profile_id = bp.brand_profile_id
            JOIN module_access ma ON ubpma.module_access_id = ma.module_access_id
            JOIN module m ON ma.module_id = m.module_id
            WHERE ubpma.user_id = :user_id
            AND ubpma.meta_status = :meta_status
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, user_id=user_id, meta_status="active").fetchall()

        brand_profile_list = []
        for row in result:
            brand_profile_id = row["brand_profile_id"]

            brand_profile = next((item for item in brand_profile_list if item["brand_profile_id"] == brand_profile_id), None)
            if not brand_profile:
                brand_profile = {
                    "brand_profile_id": brand_profile_id,
                    "brand_name": row["brand_name"],
                    "module_access_list": []
                }
                brand_profile_list.append(brand_profile)

            module_access = {
                "module_id": row["module_id"],
                "module_name": row["module_name"],
                "module_access_id": row["module_access_id"],
                "access_level": row["access_level"]
            }
            brand_profile["module_access_list"].append(module_access)

        user_dict["brand_profile_list"] = brand_profile_list

    # get presigned url for user image
    user_image_url = None
    if user_result["image_bucket_name"] and user_result["image_object_key"]:
        user_image_url = jqutils.create_presigned_get_url(user_result["image_bucket_name"], user_result["image_object_key"], expiration=3600)

    user_dict["user_image_url"] = user_image_url

    if result:
        response_body = {
            "data": user_dict,
            "action": "get_user",
            "status": "successful"
        }
    else:
        response_body = {
            "data": {},
            "action": "get_user",
            "status": "successful",
            "message": "No data found"
        }
    return jsonify(response_body)

@user_management_blueprint.route('/user/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    db_engine = jqutils.get_db_engine()

    # Get user details
    query = text("""
        SELECT u.keycloak_user_id
        FROM user u
        WHERE u.user_id = :user_id
        AND u.meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, user_id=user_id, meta_status="active").fetchone()

    if result:
        keycloak_user_id = result["keycloak_user_id"]

        # Delete user from keycloak
        keycloak_utils.delete_user(keycloak_user_id)

        # Delete user from DB
        one_dict = {
            "meta_status": "deleted",
            "deletion_user_id": g.user_id,
            "deletion_timestamp": jqutils.get_utc_datetime()
        }

        condition = {
            "user_id": str(user_id)
        }

        jqutils.update_single_db_entry(one_dict, "user", condition)

        query = text("""
            SELECT user_role_map_id
            FROM user_role_map
            WHERE user_id = :user_id
            AND meta_status = :meta_status
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, user_id=user_id, meta_status="active").fetchall()

        user_role_map_id_list = [row["user_role_map_id"] for row in result]

        for user_role_map_id in user_role_map_id_list:

            # Delete user roles
            condition = {
                "user_role_map_id": str(user_role_map_id)
            }

            jqutils.update_single_db_entry(one_dict, "user_role_map", condition)

        query = text("""
            SELECT user_brand_profile_module_access_id
            FROM user_brand_profile_module_access
            WHERE user_id = :user_id
            AND meta_status = :meta_status
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, user_id=user_id, meta_status="active").fetchall()

        user_brand_profile_module_access_id_list = [row["user_brand_profile_module_access_id"] for row in result]

        for user_brand_profile_module_access_id in user_brand_profile_module_access_id_list:
                
            # Delete user brand profile module access
            condition = {
                "user_brand_profile_module_access_id": str(user_brand_profile_module_access_id)
            }

            jqutils.update_single_db_entry(one_dict, "user_brand_profile_module_access", condition)

        query = text("""
            SELECT user_image_map_id
            FROM user_image_map
            WHERE user_id = :user_id
            AND meta_status = :meta_status
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, user_id=user_id, meta_status="active").fetchall()

        user_image_map_id_list = [row["user_image_map_id"] for row in result]

        for user_image_map_id in user_image_map_id_list:
                
            # Delete user image map
            condition = {
                "user_image_map_id": str(user_image_map_id)
            }

            jqutils.update_single_db_entry(one_dict, "user_image_map", condition)

    response_body = {
        "action": "delete_user",
        "status": "successful"
    }
    return jsonify(response_body)

@user_management_blueprint.route('/users', methods=['GET'])
def get_users():
    db_engine = jqutils.get_db_engine()

    query = text("""
        SELECT user_id, keycloak_user_id, username, first_names_en, last_name_en, first_names_ar, last_name_ar, phone_nr, email
        FROM user
        WHERE meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, meta_status="active").fetchall()

    user_list = [dict(row) for row in result]

    # get role list for each user
    for one_user in user_list:
        user_id = one_user["user_id"]

        query = text("""
            SELECT urm.role_id, r.role_name
            FROM user_role_map urm
            JOIN role r ON urm.role_id = r.role_id
            WHERE urm.user_id = :user_id
            AND urm.meta_status = :meta_status
        """)
        with db_engine.connect() as conn:
            role_result = conn.execute(query, user_id=user_id, meta_status="active").fetchall()

        one_user["role_list"] = [dict(role) for role in role_result]

    response_body = {
        "data": [dict(row) for row in result],
        "action": "get_users",
        "status": "successful"
    }
    return jsonify(response_body)