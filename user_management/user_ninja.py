import re
import os
import requests
from datetime import datetime
from dateutil.relativedelta import relativedelta

from sqlalchemy.sql import text

from utils import jqutils, jqsecurity
from data_migration_management.data_migration_manager import DataMigrationManager

def get_user_details_by_code(user_code):
    query = text(f"""
        SELECT
            u.user_id,
            u.username,
            umm.merchant_id,
            m.merchant_id
        FROM
            user u
        JOIN
           user_merchant_map umm on umm.user_id = u.user_id
        JOIN
            merchant m on m.merchant_id = umm.merchant_id
        WHERE
            u.user_code = '{user_code}'
        AND
            u.meta_status = 'active'
        AND
            umm.meta_status = 'active'
        AND
            m.meta_status = 'active'
    """)
    db_engine = jqutils.get_db_engine()
    with db_engine.connect() as conn:
        result = conn.execute(query).fetchone()
        return dict(result)

def get_third_party_access_token(third_party_credential_type, merchant_id, user_id=None):
    db_engine = jqutils.get_db_engine()

    user_filter_statement = ""
    if user_id:
        user_filter_statement = "AND user_id = :user_id"

    query = text(f"""
        SELECT merchant_third_party_credential_id, username, user_id, password, access_token, access_token_expiry_timestamp
        FROM merchant_third_party_credential
        WHERE third_party_credential_type = :third_party_credential_type
        AND merchant_id = :merchant_id
        {user_filter_statement}
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, third_party_credential_type=third_party_credential_type, merchant_id=merchant_id,
                              user_id=user_id, meta_status='active').fetchone()

    if not result:
        return None, None

    # Check whether the token already exists and hasn't expired
    get_fresh_access_token = False
    external_user_id = result["user_id"]
    access_token = result["access_token"]
    access_token_expiry_timestamp = result['access_token_expiry_timestamp']
    merchant_third_party_credential_id = result['merchant_third_party_credential_id']

    if access_token is None or access_token_expiry_timestamp is None or access_token_expiry_timestamp < datetime.utcnow():
        get_fresh_access_token = True

    if get_fresh_access_token:
        password_manager = DataMigrationManager()
        password = password_manager.decrypt_password(result["password"].encode()).decode()
        username = result["username"]

        if third_party_credential_type == "neighbourhood-pulse":
            payload = {
                "email": username,
                "password": password
            }
        elif third_party_credential_type == "financials":
            payload = {
                "username": username,
                "password": password
            }
        elif third_party_credential_type == "supplyblox-full":
            payload = {
                "username": username,
                "password": password
            }

        access_token, access_token_expiry_timestamp = fetch_access_token(payload, third_party_credential_type)

        # Update access token
        query = text("""
                    UPDATE merchant_third_party_credential
                    SET access_token = :access_token, access_token_expiry_timestamp = :access_token_expiry_timestamp
                    WHERE merchant_third_party_credential_id = :merchant_third_party_credential_id
                """)
        with db_engine.connect() as conn:
            result = conn.execute(query, access_token=access_token, access_token_expiry_timestamp=access_token_expiry_timestamp,
                                  merchant_third_party_credential_id=merchant_third_party_credential_id).rowcount
            assert result, "Failed to update access token"

    return access_token, external_user_id


def fetch_access_token(payload, third_party_credential_type):
    if third_party_credential_type == "neighbourhood-pulse":
        request_url = f"{os.getenv('NEIGHBORHOOD_PULSE_URL')}/api/login"
        if os.getenv("MOCK_NEIGHBORHOOD_PULSE") == "0":
            response = requests.post(request_url, json=payload)
            status_code = response.status_code

            if status_code != 200:
                return None, None

            response_body = response.json()
            if response_body["status"] != "successful":
                return None, None

            access_token = response.headers['X-Access-Token']
            access_token_expiry_timestamp = response.headers['X-Access-Token-Expiry-Timestamp']
        else:
            access_token = "1Xapmdawodmo121mMoadkp1"
            access_token_expiry_timestamp = "2023-04-05 12:12:12.121212"

    elif third_party_credential_type == "financials":
        request_url = f"{os.getenv('FINANCIAL_SERVICE_BASE_URL')}/login"
        if os.getenv("MOCK_FINANCIALS") == "0":
            response = requests.post(request_url, json=payload)
            status_code = response.status_code

            if status_code != 200:
                return None, None

            response_body = response.json()
            if response_body["status"] != "successful":
                return None, None

            access_token = response.headers['X-Access-Token']
            access_token_expiry_timestamp = response_body['data']['access_token_expiry_timestamp']
        else:
            access_token = "1Xapmdawodmo121mMoadkp1"
            access_token_expiry_timestamp = "2023-04-05 12:12:12.121212"

    elif third_party_credential_type == "supplyblox-full":
        request_url = f"{os.getenv('SUPPLYBLOX_API_BASE_URL')}/api/login"
        if os.getenv("MOCK_SUPPLYBLOX") == "0":
            response = requests.post(request_url, json=payload)
            status_code = response.status_code

            if status_code != 200:
                return None, None

            response_body = response.json()
            if response_body["status"] != "successful":
                return None, None

            access_token = response.headers['X-Access-Token']
            access_token_expiry_timestamp = response.headers['X-Token-Expiry-Timestamp']
        else:
            access_token = "1Xapmdawodmo121mMoadkp1"
            access_token_expiry_timestamp = "2023-04-05 12:12:12.121212"

    return access_token, access_token_expiry_timestamp

def create_neighborhood_pulse_credentials(user_id, merchant_id, merchant_name, key_string_db_bytes):
    db_engine = jqutils.get_db_engine()

    query = text("""
        SELECT first_names_en, last_name_en, phone_nr, email
        FROM user
        WHERE user_id = :user_id
    """)
    with db_engine.connect() as conn:
        user_result = conn.execute(query, user_id=user_id).fetchone()
        assert user_result, "user_id not found"

    request_url = f"{os.getenv('NEIGHBORHOOD_PULSE_URL')}/api/signup"
    username = jqutils.create_code_from_title(merchant_name, 6)
    password = jqutils.get_random_alphanumeric(16)
    request_body = {
        "first_names_en":  user_result['first_names_en'],
        "last_name_en": user_result['last_name_en'],
        "phone_nr": user_result['phone_nr'],
        "email": user_result['email'],
        "username": username,
        "password": password,
    }

    if os.getenv("MOCK_NEIGHBORHOOD_PULSE") == "0":
        neighborhood_pulse_response = requests.post(request_url, json=request_body)
        assert neighborhood_pulse_response.status_code == 200, "neighborhood pulse response not successful"
        neighborhood_pulse_user_id = neighborhood_pulse_response.headers['X-User-Id']
        neighborhood_pulse_access_token = neighborhood_pulse_response.headers['X-Access-Token']
        neighborhood_pulse_access_token_expiry_timestamp = neighborhood_pulse_response.headers['X-Access-Token-Expiry-Timestamp']

    else:
        neighborhood_pulse_user_id = "1"
        neighborhood_pulse_access_token = "Am1pdaodmcaixwi1"
        neighborhood_pulse_access_token_expiry_timestamp = "2023-09-04 12:12:12.121212"

    encrypted_password = jqsecurity.encrypt_bytes_symmetric_to_bytes(password.encode(), key_string_db_bytes)

    query = text("""
        INSERT INTO merchant_third_party_credential(merchant_id, third_party_credential_type, user_id, username, password, access_token,
                                                        access_token_expiry_timestamp, meta_status)
        VALUES (:merchant_id, :third_party_credential_type, :user_id, :username, :password, :access_token, :access_token_expiry_timestamp, :meta_status)
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, merchant_id=merchant_id, third_party_credential_type='neighbourhood-pulse',
                                                        user_id=neighborhood_pulse_user_id, username=username, password=encrypted_password,
                                                        access_token=neighborhood_pulse_access_token,
                                                        access_token_expiry_timestamp=neighborhood_pulse_access_token_expiry_timestamp,
                                                        meta_status='active').lastrowid
        assert result, "unable to add user_neighborhood_pulse_credentials"

def create_user(user_detail, creation_user_id, tenant_id, role_id=None, merchant_id=None, facility_id_list=[]):
    db_engine = jqutils.get_db_engine()

    meta_status = 'active'
    all_facility_access_p = user_detail.get('all_facility_access_p', 0)
    username = user_detail['username']
    password = user_detail['password']
    email = user_detail['email']
    phone_nr = user_detail['phone_nr']
    user_code = jqutils.create_code_from_title(username,4)
    password_bytes = password.encode()

    query = text(""" 
        select symmetric_key 
        from payment_api_secret 
        where description = 'password-protector-key' and
        meta_status = 'active'
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query).fetchone()
        key_string_db = result['symmetric_key']
        key_string_db_bytes = key_string_db.encode()
    
    cipher_text_bytes = jqsecurity.encrypt_bytes_symmetric_to_bytes(password_bytes, key_string_db_bytes)
    access_token = jqsecurity.generate_secret(16)
    
    now = datetime.now()
    password_expiry_timestamp = now + relativedelta(year=6)
    token_expiry_timestamp = now + relativedelta(year=6)

    query = text("""
        SELECT username, email, phone_nr
        FROM user
        WHERE (username = :username OR email = :email OR phone_nr = :phone_nr) AND
        meta_status = 'active'
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, username=username, email=email, phone_nr=phone_nr).fetchone()
        if result:
            if result['username'] == username:
                return None, 'username already exists'
            if result['email'] == email:
                return None, 'email already exists'
            if result['phone_nr'] == phone_nr:
                return None, 'phone number already exists'
        
    user_payload = {
        "username": username,
        "email": email,
        "completed_signup_p": user_detail['completed_signup_p'],
        "business_designation": user_detail['business_designation'],
        "first_names_en": user_detail['first_names_en'],
        "last_name_en": user_detail['last_name_en'],
        "first_names_ar": user_detail['first_names_ar'],
        "last_name_ar": user_detail['last_name_ar'],
        "phone_nr": phone_nr,
        "password": cipher_text_bytes,
        "password_expiry_timestamp": password_expiry_timestamp,
        "access_token": access_token,
        "user_code": user_code,
        "soft_login_required_p": user_detail['soft_login_required_p'],
        "personal_access_code": user_detail['personal_access_code'],
        "token_expiry_timestamp": token_expiry_timestamp,
        "root_p": user_detail['root_p'],
        "phone_verified_p": user_detail['phone_verified_p'],
        "email_verified_p": user_detail['email_verified_p'],
        "verification_status": user_detail['verification_status'],
        "all_facility_access_p": all_facility_access_p,
        "meta_status": meta_status,
        "system_user_p": user_detail['system_user_p'],
        "creation_user_id": creation_user_id,
        "tenant_id": tenant_id
    }

    query = text("""
        insert into user (
            username, email, business_designation, completed_signup_p,
            first_names_en, last_name_en, first_names_ar, last_name_ar,
            phone_nr, password, password_expiry_timestamp, access_token, user_code, soft_login_required_p,
            personal_access_code, token_expiry_timestamp, root_p, phone_verified_p, email_verified_p,
            verification_status, all_facility_access_p, meta_status, system_user_p, creation_user_id, tenant_id
        ) 
        values (
            :username, :email, :business_designation, :completed_signup_p,
            :first_names_en, :last_name_en, :first_names_ar,
            :last_name_ar, :phone_nr, :password,
            :password_expiry_timestamp, :access_token, :user_code, :soft_login_required_p,
            :personal_access_code, :token_expiry_timestamp, :root_p, :phone_verified_p, :email_verified_p,
            :verification_status, :all_facility_access_p, :meta_status, :system_user_p, :creation_user_id, :tenant_id
        )
    """)
    with db_engine.connect() as conn:
        user_id = conn.execute(query, **user_payload).lastrowid
        assert user_id, "failed to insert user"

    if role_id:
        query = text("""
                INSERT INTO user_role_map(role_id, user_id, meta_status, creation_user_id)
                VALUES(:role_id, :user_id, :meta_status, :creation_user_id)
            """)
        with db_engine.connect() as conn:
            result = conn.execute(query, role_id=role_id, user_id=user_id, meta_status=meta_status, creation_user_id=creation_user_id)
            assert result, f"Role with id ({role_id}) not created for user id ({user_id})"

    if merchant_id:
        query = text("""
                INSERT INTO user_merchant_map(merchant_id, user_id, meta_status, creation_user_id)
                VALUES(:merchant_id, :user_id, :meta_status, :creation_user_id)
            """)
        with db_engine.connect() as conn:
            result = conn.execute(query, merchant_id=merchant_id, user_id=user_id, meta_status=meta_status, creation_user_id=creation_user_id)
            assert result, f"User Merchant Map with merchant_id ({merchant_id}) not created for user id ({user_id})"


        if len(facility_id_list) and not all_facility_access_p:
            for facility_id in facility_id_list:    
                insert_user_facility_query = text("""
                    insert into user_facility_map (user_id, facility_id, meta_status, creation_user_id)
                    values (:user_id, :facility_id, :meta_status, :creation_user_id)
                """)
                with db_engine.connect() as conn:
                    user_facility_id = conn.execute(insert_user_facility_query, user_id=user_id, facility_id=facility_id, meta_status=meta_status, creation_user_id=creation_user_id).lastrowid 
                    assert user_facility_id, 'Unable to create user_facility'
                    
        query = text("""
                SELECT payment_point_area_id
                FROM payment_point_area
                WHERE merchant_id = :merchant_id
                AND meta_status = :meta_status
            """)
        with db_engine.connect() as conn:
            result = conn.execute(query, merchant_id=merchant_id, meta_status='active').fetchone()
            if result:
                payment_point_area_id = result['payment_point_area_id']

                query = text("""
                    INSERT INTO user_payment_point_area_map(payment_point_area_id, user_id, default_p, meta_status, creation_user_id)
                    VALUES(:payment_point_area_id, :user_id, :default_p, :meta_status, :creation_user_id)
                """)
                with db_engine.connect() as conn:
                    result = conn.execute(query, payment_point_area_id=payment_point_area_id, user_id=user_id, default_p=1, meta_status=meta_status, creation_user_id=creation_user_id)
                    assert result, f"User Payment Point Area Map with payment_point_area_id ({payment_point_area_id}) not created for user id ({user_id})"

    return user_id, ""

def check_username_availability(username):
    db_engine = jqutils.get_db_engine()
    username = username.lower()

    query = text("""
        SELECT username
        FROM user
        WHERE username = :username
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, username=username, meta_status='active').fetchone()
    
    available_p = False if result else True
    
    return available_p