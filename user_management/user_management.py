import os
import uuid

from sqlalchemy import text
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, g
from utils import keycloak_utils, jqutils, jqimage_uploader, aws_utils
from user_management import user_ninja

user_management_blueprint = Blueprint('user_management', __name__)

@user_management_blueprint.route('/username-availability', methods = ['POST'])
def check_username_availability():
    request_json = request.get_json()
    username = request_json["username"]

    available_p = user_ninja.check_username_availability(username)

    response_body = {
        "data": {
            "available_p": available_p
        },
        "action": "check_username_availability",
        "status": "successful"
    }
    return jsonify(response_body)

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
    all_brand_profile_access_p = request_json.get("all_brand_profile_access_p", False)
    global_module_access_id_list = request_json.get("module_access_id_list", [])

    db_engine = jqutils.get_db_engine()
    
    with db_engine.connect() as conn:
        
        # create user
        query = text("""
            INSERT INTO user (first_names_en, last_name_en, first_names_ar, last_name_ar, phone_nr, email, all_brand_profile_access_p, meta_status, creation_user_id)
            VALUES (:first_names_en, :last_name_en, :first_names_ar, :last_name_ar, :phone_nr, :email, :all_brand_profile_access_p, :meta_status, :creation_user_id)
        """)
        user_id = conn.execute(query, first_names_en=first_names_en, last_name_en=last_name_en, first_names_ar=first_names_ar, last_name_ar=last_name_ar,
                    phone_nr=phone_nr, email=email, all_brand_profile_access_p=all_brand_profile_access_p, meta_status="active", creation_user_id=g.user_id).lastrowid
        assert user_id, "failed to create user"

        # create user roles
        query_params = ""
        for role_id in role_id_list:
            query_params += f"({user_id}, {role_id}, 'active', {g.user_id}),"
        
        if query_params:
            query_params = query_params[:-1]
            
            query = text(f"""
                INSERT INTO user_role_map (user_id, role_id, meta_status, creation_user_id)
                VALUES {query_params}
            """)
            results = conn.execute(query).rowcount
            assert results == len(role_id_list), "failed to create user roles"

        # allow access to user for all modules across all brand profiles
        if all_brand_profile_access_p:
            query_params = ""
            for module_access_id in global_module_access_id_list:
                query_params += f"({user_id}, NULL, {module_access_id}, 'active', {g.user_id}),"

            if query_params:
                query_params = query_params[:-1]
                
                query = text(f"""
                    INSERT INTO user_brand_profile_module_access (user_id, brand_profile_id, module_access_id, meta_status, creation_user_id)
                    VALUES {query_params}
                """)
                results = conn.execute(query).rowcount
                assert results == len(global_module_access_id_list), "failed to create user brand profile module access"

        # allow brand-specific access to user
        else:
            query_params = ""
            for brand_profile in brand_profile_list:
                brand_profile_id = brand_profile["brand_profile_id"]
                module_access_id_list = brand_profile["module_access_id_list"]

                for module_access_id in module_access_id_list:
                    query_params += f"({user_id}, {brand_profile_id}, {module_access_id}, 'active', {g.user_id}),"

            if query_params:
                query_params = query_params[:-1]
                
                query = text(f"""
                    INSERT INTO user_brand_profile_module_access (user_id, brand_profile_id, module_access_id, meta_status, creation_user_id)
                    VALUES {query_params}
                """)
                results = conn.execute(query).rowcount
                assert results == len(module_access_id_list), "failed to create user brand profile module access"

        # dispatch email to user for completing signup
        userdata = {
            "user_id": user_id,
            "first_names_en": first_names_en,
            "last_name_en": last_name_en,
            "email": email
        }
        user_ninja.send_user_signup_email(userdata, g.user_id)

    response_body = {
        "data": {
            "user_id": user_id
        },
        "action": "add_user",
        "status": "successful"
    }

    return jsonify(response_body)

@user_management_blueprint.route('/user/<user_id>', methods=['PUT'])
def update_user(user_id):

    request_json = request.get_json()

    first_names_en = request_json["first_names_en"]
    last_name_en = request_json["last_name_en"]
    first_names_ar = request_json["first_names_ar"]
    last_name_ar = request_json["last_name_ar"]
    phone_nr = request_json["phone_nr"]
    email = request_json["email"]
    role_id_list = request_json["role_id_list"]
    brand_profile_list = request_json["brand_profile_list"]
    all_brand_profile_access_p = request_json.get("all_brand_profile_access_p", False)
    module_access_id_list = request_json.get("module_access_id_list", [])

    one_dict = {
        "first_names_en": first_names_en,
        "last_name_en": last_name_en,
        "first_names_ar": first_names_ar,
        "last_name_ar": last_name_ar,
        "phone_nr": phone_nr,
        "email": email,
        "all_brand_profile_access_p": all_brand_profile_access_p,
        "meta_status": "active",
        "modification_user_id": g.user_id,
        "modification_timestamp": jqutils.get_utc_datetime()
    }

    condition = {
        "user_id": str(user_id)
    }

    jqutils.update_single_db_entry(one_dict, "user", condition)

    db_engine = jqutils.get_db_engine()

    # delete existing user roles
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

        one_dict = {
            "meta_status": "deleted",
            "deletion_user_id": g.user_id,
            "deletion_timestamp": jqutils.get_utc_datetime()
        }

        condition = {
            "user_role_map_id": str(user_role_map_id)
        }

        jqutils.update_single_db_entry(one_dict, "user_role_map", condition)

    # add new user roles
    for role_id in role_id_list:
        one_dict = {
            "user_id": user_id,
            "role_id": role_id,
            "meta_status": "active",
            "creation_user_id": g.user_id
        }
        jqutils.create_new_single_db_entry(one_dict, "user_role_map")

    if all_brand_profile_access_p:
            
            # delete existing user brand profile module access
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
            
                one_dict = {
                    "meta_status": "deleted",
                    "deletion_user_id": g.user_id,
                    "deletion_timestamp": jqutils.get_utc_datetime()
                }
    
                condition = {
                    "user_brand_profile_module_access_id": str(user_brand_profile_module_access_id)
                }
    
                jqutils.update_single_db_entry(one_dict, "user_brand_profile_module_access", condition)
    
            # add new user brand profile module access
            for module_access_id in module_access_id_list:
    
                one_dict = {
                    "user_id": user_id,
                    "brand_profile_id": None,
                    "module_access_id": module_access_id,
                    "meta_status": "active",
                    "creation_user_id": g.user_id
                }
    
                jqutils.create_new_single_db_entry(one_dict, "user_brand_profile_module_access")
    
            # get all brand profiles
            db_engine = jqutils.get_db_engine()
    
            query = text("""
                SELECT brand_profile_id
                FROM brand_profile
                WHERE meta_status = :meta_status
            """)
            with db_engine.connect() as conn:
                result = conn.execute(query, meta_status="active").fetchall()
    
            brand_profile_id_list = [row["brand_profile_id"] for row in result]
    
            for brand_profile_id in brand_profile_id_list:
                for module_access_id in module_access_id_list:
    
                    one_dict = {
                        "user_id": user_id,
                        "brand_profile_id": brand_profile_id,
                        "module_access_id": module_access_id,
                        "meta_status": "active",
                        "creation_user_id": g.user_id
                    }
                    jqutils.create_new_single_db_entry(one_dict, "user_brand_profile_module_access")

    else:

        # delete existing user brand profile module access
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
        
            one_dict = {
                "meta_status": "deleted",
                "deletion_user_id": g.user_id,
                "deletion_timestamp": jqutils.get_utc_datetime()
            }

            condition = {
                "user_brand_profile_module_access_id": str(user_brand_profile_module_access_id)
            }

            jqutils.update_single_db_entry(one_dict, "user_brand_profile_module_access", condition)

        # add new user brand profile module access
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

    # update user in keycloak
    keycloak_user_id = jqutils.get_column_by_id(user_id, "keycloak_user_id", "user")
        
    if keycloak_user_id:
        keycloak_utils.update_user(keycloak_user_id, first_names_en, last_name_en, email)

    response_body = {
        "action": "update_user",
        "status": "successful"
    }
    return jsonify(response_body)

@user_management_blueprint.route('/user/<user_id>', methods=['GET'])
def get_user(user_id):
    user_id = int(user_id)
    
    db_engine = jqutils.get_db_engine()

    # get user details
    query = text("""
        SELECT keycloak_user_id, username, first_names_en, last_name_en, first_names_ar,
            last_name_ar, phone_nr, email, all_brand_profile_access_p
        FROM user
        WHERE user_id = :user_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, user_id=user_id, meta_status="active").fetchone()
        assert result, "failed to get user details"

    user_dict = {
        "user_id": user_id,
        "keycloak_user_id": result["keycloak_user_id"],
        "username": result["username"],
        "first_names_en": result["first_names_en"],
        "last_name_en": result["last_name_en"],
        "first_names_ar": result["first_names_ar"],
        "last_name_ar": result["last_name_ar"],
        "phone_nr": result["phone_nr"],
        "email": result["email"],
        "all_brand_profile_access_p": result["all_brand_profile_access_p"],
        "role_list": [],
        "user_image_list": [],
        "module_access_list": [],
        "brand_profile_list": []
    }

    # get user roles
    query = text("""
        SELECT urm.user_role_map_id, urm.role_id, r.role_name
        FROM user_role_map urm
        JOIN role r ON urm.role_id = r.role_id
        WHERE urm.user_id = :user_id
        AND urm.meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        results = conn.execute(query, user_id=user_id, meta_status="active").fetchall()
        user_dict["role_list"] = [dict(row) for row in results]

    # get user images
    query = text("""
        SELECT user_image_id, image_type, image_bucket_name, image_object_key
        FROM user_image
        WHERE user_id = :user_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        results = conn.execute(query, user_id=user_id, meta_status="active").fetchall()
        
        for one_image in results:
            image_bucket_name = one_image["image_bucket_name"]
            image_object_key = one_image["image_object_key"]
                
            if os.getenv("MOCK_S3_UPLOAD") != '1':
                user_image_url = jqimage_uploader.create_presigned_url(image_bucket_name, image_object_key)
            else:
                user_image_url = f"https://s3.amazonaws.com/{image_bucket_name}/{image_object_key}"
            
            user_dict["user_image_list"].append({
                "user_image_id": one_image["user_image_id"],
                "image_type": one_image["image_type"],
                "user_image_url": user_image_url
            })

    # get all brand profiles module access
    if user_dict["all_brand_profile_access_p"]:
        query = text("""
            SELECT ubpma.module_access_id, m.module_id, m.module_name, ma.module_access_id, ma.access_level
            FROM user_brand_profile_module_access ubpma
            JOIN module_access ma ON ubpma.module_access_id = ma.module_access_id
            JOIN module m ON ma.module_id = m.module_id
            WHERE ubpma.user_id = :user_id
            AND ubpma.brand_profile_id IS NULL
            AND ubpma.meta_status = :meta_status
        """)
        with db_engine.connect() as conn:
            results = conn.execute(query, user_id=user_id, meta_status="active").fetchall()
            user_dict["module_access_list"] = [dict(row) for row in results]

    # get brand profile and specific module access
    query = text("""
        SELECT ubpma.brand_profile_id, ubpma.module_access_id, bp.brand_profile_name as brand_profile_name, m.module_id, m.module_name, ma.module_access_id, ma.access_level
        FROM user_brand_profile_module_access ubpma
        JOIN brand_profile bp ON ubpma.brand_profile_id = bp.brand_profile_id
        JOIN module_access ma ON ubpma.module_access_id = ma.module_access_id
        JOIN module m ON ma.module_id = m.module_id
        WHERE ubpma.user_id = :user_id
        AND ubpma.brand_profile_id IS NOT NULL
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
                "brand_profile_name": row["brand_profile_name"],
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

    response_body = {
        "data": user_dict,
        "action": "get_user",
        "status": "successful"
    }

    return jsonify(response_body)

@user_management_blueprint.route('/users', methods=['GET'])
def get_users():
    db_engine = jqutils.get_db_engine()

    query = text("""
        SELECT user_id, keycloak_user_id, username, first_names_en, last_name_en,
            first_names_ar, last_name_ar, phone_nr, email
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
        "data": user_list,
        "action": "get_users",
        "status": "successful"
    }
    return jsonify(response_body)

@user_management_blueprint.route('/user/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    db_engine = jqutils.get_db_engine()

    with db_engine.connect() as conn:
        
        # Get user details
        query = text("""
            SELECT keycloak_user_id, meta_status
            FROM user u
            WHERE user_id = :user_id
        """)
        result = conn.execute(query, user_id=user_id, meta_status="active").fetchone()
        assert result, "failed to get user details"

        if result["meta_status"] != "deleted":
            action_timestamp = jqutils.get_utc_datetime()
    
            # Delete user from keycloak
            keycloak_user_id = result["keycloak_user_id"]
            if keycloak_user_id:
                keycloak_utils.disassociate_user_from_policies(keycloak_user_id)
                keycloak_utils.delete_user(keycloak_user_id)
                
                # Remove keycloak id from database to prevent re-deletion on keycloak
                query = text("""
                    UPDATE user
                    SET keycloak_user_id = :keycloak_user_id,
                    modification_user_id = :modification_user_id
                    WHERE user_id = :user_id
                """)
                result = conn.execute(query, keycloak_user_id=None, modification_user_id=g.user_id, user_id=user_id).rowcount
                assert result, "failed to remove user keycloak id"

            # Delete user from DB
            query = text("""
                UPDATE user
                SET meta_status = :meta_status,
                deletion_user_id = :deletion_user_id,
                deletion_timestamp = :deletion_timestamp
                WHERE user_id = :user_id
            """)
            result = conn.execute(query, meta_status="deleted", deletion_user_id=g.user_id, deletion_timestamp=action_timestamp, user_id=user_id).rowcount
            assert result, "failed to delete user"

            # Delete user role mappings
            query = text("""
                UPDATE user_role_map
                SET meta_status = :meta_status,
                deletion_user_id = :deletion_user_id,
                deletion_timestamp = :deletion_timestamp
                WHERE user_id = :user_id
                AND meta_status = :meta_status_active
            """)
            conn.execute(query, meta_status="deleted", deletion_user_id=g.user_id, deletion_timestamp=action_timestamp, user_id=user_id, meta_status_active="active")

            # Delete user brand profile module access
            query = text("""
                UPDATE user_brand_profile_module_access
                SET meta_status = :meta_status,
                deletion_user_id = :deletion_user_id,
                deletion_timestamp = :deletion_timestamp
                WHERE user_id = :user_id
                AND meta_status = :meta_status_active
            """)
            conn.execute(query, meta_status="deleted", deletion_user_id=g.user_id, deletion_timestamp=action_timestamp, user_id=user_id, meta_status_active="active")

            # Delete user images
            query = text("""
                UPDATE user_image
                SET meta_status = :meta_status,
                deletion_user_id = :deletion_user_id,
                deletion_timestamp = :deletion_timestamp
                WHERE user_id = :user_id
                AND meta_status = :meta_status_active
            """)
            conn.execute(query, meta_status="deleted", deletion_user_id=g.user_id, deletion_timestamp=action_timestamp, user_id=user_id, meta_status_active="active")

    response_body = {
        "action": "delete_user",
        "status": "successful"
    }
    return jsonify(response_body)

# OTP verification
#--------------------------------------------
@user_management_blueprint.route('/user/<user_id>/verify-otp', methods=['POST'])
def verify_user_otp(user_id):
    user_id = int(user_id)
    request_json = request.get_json()

    username = request_json["username"]
    password = request_json["password"]
    otp = request_json["otp"]
    intent = request_json["intent"]

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
                        assert result, "failed to get user details"

                    first_names_en = result["first_names_en"]
                    last_name_en = result["last_name_en"]
                    email = result["email"]

                    # create keycloak user
                    keycloak_user_id = keycloak_utils.create_user(username, password, first_names_en, last_name_en, email)

                    # update user details
                    query = text("""
                        UPDATE user
                        SET keycloak_user_id = :keycloak_user_id,
                        username = :username
                        WHERE user_id = :user_id
                    """)
                    with db_engine.connect() as conn:
                        conn.execute(query, keycloak_user_id=keycloak_user_id, username=username, user_id=user_id)

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

# Forgot / Reset password
#--------------------------------------------
@user_management_blueprint.route('/forgot-password', methods = ['POST'])
def initiate_forgot_password_request():
    request_json = request.get_json()
    
    username = request_json["username"]
    email = request_json["email"]

    db_engine = jqutils.get_db_engine()
    
    # check if user exists
    query = text("""
        SELECT user_id, username, keycloak_user_id, email
        FROM user
        WHERE username = :username
        AND email = :email
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, username=username, email=email, meta_status='active').fetchone()
    
    if not result:
        response_body = {
            "message": "User not found",
            "action": "initiate_forgot_password_request",
            "status": "failed",
        }
        return jsonify(response_body)
    
    user_id = result["user_id"]
    username = result["username"]
    keycloak_user_id = result["keycloak_user_id"]
    email = result["email"]
    contact_method = "email"

    if not keycloak_user_id:
        response_body = {
            "data": {},
            "action": "initiate_forgot_password_request",
            "status": "failed",
            "message": "Password not set for user. Try soft-login.",
        }
    
    # check if OTP already exists for user
    query = text("""
        SELECT one_time_password_id, otp_status
        FROM one_time_password
        WHERE user_id = :user_id
        AND intent = :intent
        AND meta_status = :meta_status
        ORDER BY otp_requested_timestamp DESC
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, user_id=user_id, intent='forgot_password', meta_status='active').fetchone()
    
    if result:
        if result["otp_status"] == "sent":
            response_body = {
                "data": {
                    "user_id": user_id,
                    "contact_method": contact_method
                },
                "action": "initiate_forgot_password_request",
                "status": "successful",
            }
            return jsonify(response_body)

    # create OTP request for user
    otp = str(uuid.uuid4())
    intent = "forgot_password"
    otp_request_count = 0
    otp_requested_timestamp_str = jqutils.get_utc_datetime()
    otp_requested_timestamp = datetime.strptime(otp_requested_timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
    otp_expiry_timestamp = otp_requested_timestamp + timedelta(days=7)
    otp_status = "pending"

    query = text("""
        INSERT INTO one_time_password (user_id, otp, intent, contact_method, otp_request_count, otp_requested_timestamp, otp_expiry_timestamp, otp_status, meta_status)
        VALUES(:user_id, :otp, :intent, :contact_method, :otp_request_count, :otp_requested_timestamp, :otp_expiry_timestamp, :otp_status, :meta_status)
    """)
    with db_engine.connect() as conn:
        one_time_password_id = conn.execute(query, user_id=user_id, otp=otp, intent=intent, contact_method=contact_method, otp_request_count=otp_request_count,
                                otp_requested_timestamp=otp_requested_timestamp, otp_expiry_timestamp=otp_expiry_timestamp, otp_status=otp_status, meta_status='active').lastrowid
        assert one_time_password_id, "otp request insert error"
    
    # send otp
    if os.getenv("MOCK_AWS_NOTIFICATIONS") != "1":
        if contact_method == 'email':
            aws_utils.publish_email(
                source="haseeb.ahmed@globalvertices.com",
                destination={
                    "ToAddresses": [email],
                },
            subject=f"Forgot Password",
                text=f"Hi,\n\nYou can reset your password. Your OTP is: {otp}\n\nRegards,\nThank you,\nMealPlanet",
                html=f"Hi,<br><br>You can reset your password. Your OTP is: {otp}<br><br>Regards,<br>Thank you,<br>MealPlanet"
            )

    # update otp status
    otp_status = 'sent'
    otp_requested_timestamp = datetime.now()
    query = text("""
        UPDATE one_time_password
        SET otp_status = :otp_status,
        otp_request_count = :otp_request_count,
        otp_requested_timestamp = :otp_requested_timestamp
        WHERE one_time_password_id = :one_time_password_id
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, one_time_password_id=one_time_password_id, otp_status=otp_status, otp_request_count=otp_request_count,
                                otp_requested_timestamp=otp_requested_timestamp).rowcount
        assert result, "otp status update error"
    
    response_body = {
        "data": {
            "user_id": user_id,
            "contact_method": contact_method
        },
        "action": "initiate_forgot_password_request",
        "status": "successful",
    }
    return jsonify(response_body)

@user_management_blueprint.route('/forgot-password/<otp>', methods = ['GET'])
def get_forgot_password_request(otp):
    db_engine = jqutils.get_db_engine()

    intent = "forgot_password"

    query = text("""
        SELECT one_time_password_id, otp_status
        FROM one_time_password
        WHERE otp = :otp
        AND intent = :intent
        AND meta_status = :meta_status
        ORDER BY otp_requested_timestamp DESC
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, otp=otp, intent=intent, meta_status='active').fetchone()
    
    if not result:
        response_body = {
            "data": {},
            "action": "get_forgot_password_request",
            "status": "failed",
            "message": "OTP not valid or already processed",
        }
        return jsonify(response_body)
        
    otp_status = result["otp_status"]

    if otp_status != "sent":
        response_body = {
            "data": {},
            "action": "get_forgot_password_request",
            "status": "failed",
            "message": "OTP not valid or already processed",
        }
        return jsonify(response_body)
    
    response_body = {
        "data": {
            "otp_status": otp_status
        },
        "action": "get_forgot_password_request",
        "status": "successful",
    }
    return jsonify(response_body)

@user_management_blueprint.route('/reset-password', methods = ['POST'])
def reset_user_password():
    request_json = request.get_json()

    otp = request_json["otp"]
    password = request_json["password"]
    intent = 'forgot_password'

    db_engine = jqutils.get_db_engine()

    # check if otp is valid
    query = text("""
        SELECT one_time_password_id, user_id, otp_status
        FROM one_time_password
        WHERE otp = :otp
        AND intent = :intent
        AND meta_status = :meta_status
        ORDER BY otp_requested_timestamp DESC
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, otp=otp, intent=intent, meta_status='active').fetchone()
        assert result, "invalid otp code provided"
    
    one_time_password_id = result["one_time_password_id"]
    user_id = result["user_id"]
    otp_status = result["otp_status"]

    if otp_status != "sent":
        response_body = {
            "data": {},
            "action": "reset_user_password",
            "status": "failed",
            "message": "OTP not valid or already processed",
        }
        return jsonify(response_body)
    
    # update otp status
    otp_status = 'verified'
    otp_verified_timestamp = datetime.now()

    query = text("""
        UPDATE one_time_password
        SET otp_status = :otp_status,
        otp_verified_timestamp = :otp_verified_timestamp
        WHERE one_time_password_id = :one_time_password_id
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, one_time_password_id=one_time_password_id, otp_status=otp_status, otp_verified_timestamp=otp_verified_timestamp).rowcount
        assert result, "otp status update error"

    # update keycloak user password
    keycloak_user_id = jqutils.get_column_by_id(user_id, "keycloak_user_id", "user")

    keycloak_utils.update_user_password(keycloak_user_id, password)
    
    response_body = {
        "data": {
            "user_id": user_id
        },
        "action": "reset_user_password",
        "status": "successful",
    }
    return jsonify(response_body)