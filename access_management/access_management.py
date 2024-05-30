import json
import random
import datetime
import os

from flask import request, Response, Blueprint
from sqlalchemy.sql import text
from utils import jqutils, jqsecurity, my_utils, aws_utils
from access_management import access_ninja
from data_migration_management.data_migration_manager import DataMigrationManager

access_management_blueprint = Blueprint('access_management_blueprint', __name__)

@access_management_blueprint.route('/login', methods=['POST'])
def login():
    response = Response(content_type='application/json')
    request_body = request.json
    username = request_body['username']
    candidate_password = request_body['password']
    candidate_password_bytes = candidate_password.encode()

    db_engine = jqutils.get_db_engine()
    
    # get symmetric key from db
    query = text("""
        select symmetric_key
        from payment_api_secret 
        where description = 'password-protector-key'
        and meta_status = 'active'
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query).fetchone()
        assert result, "missing password protector key"
    
    key_string_db = result['symmetric_key']

    # get user details
    query = text("""
        select user_id, password, phone_verified_p, first_names_en, last_name_en
        from user
        where username = :username
        and meta_status = 'active'
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, username=username).fetchone()
    
    if not result:
        response_body = {
            'action': 'login',
            'status': 'failed',
            'message': 'invalid username or password',
        }

        response.data = json.dumps(response_body, default=str)
        return response
    
    user_id = result['user_id']
    phone_verified_p = result["phone_verified_p"]
    first_name = result["first_names_en"]
    last_name = result["last_name_en"]
    reference_password_ciphered_bytes = result['password'].encode()
    reference_password_deciphered = jqsecurity.decrypt_bytes_symmetric_to_bytes(reference_password_ciphered_bytes, key_string_db)

    # match encrypted candidate with reference password
    if reference_password_deciphered == candidate_password_bytes:
        
        # get access token for user
        access_token = access_ninja.get_user_access_token(user_id)

        # get role for user
        get_role_query = text("""
            select r.role_id, r.role_name
            from user_role_map urm
            inner join role r on r.role_id = urm.role_id
            where urm.user_id = :user_id
            and r.meta_status = :meta_status
            and urm.meta_status = :meta_status
        """)
        with db_engine.connect() as conn:
            role_permissions_result = conn.execute(get_role_query, user_id=user_id, meta_status='active').fetchone()
            
            if not role_permissions_result:
                response_body = {
                    'action': 'login',
                    'status': 'failed',
                    'message': 'user has no assigned role',
                }

                response.data = json.dumps(response_body, default=str)
                return response

        role_id = role_permissions_result['role_id']
        role_name = role_permissions_result['role_name']

        # get merchant details for the user
        merchant_details = access_ninja.get_merchant_details_for_user(user_id)
        
        customer = None
        if role_name == "customer":
            
            query = text("""
                SELECT c.customer_id, ucm.user_customer_map_id, c.customer_code, c.stripe_customer_id, c.merchant_id, c.customer_first_name, c.customer_last_name, c.customer_email, c.customer_phone_nr, c.customer_remote_id, c.customer_gender, c.customer_dob
                FROM customer c
                LEFT JOIN user_customer_map ucm ON c.customer_id = ucm.customer_id
                WHERE ucm.user_id = :user_id
                AND c.meta_status = 'active'
            """)
            with db_engine.connect() as conn:
                result = conn.execute(query, user_id=user_id).fetchone()
            customer = dict(result)
        # log user session
        session_insert_query = text(""" 
            insert into user_session (user_id, action, meta_status)
            values(:user_id, :action, 'active') 
        """)
        with db_engine.connect() as conn:
            result = conn.execute(session_insert_query, user_id=user_id, action='login').lastrowid

        response.headers['X-Access-Token'] = access_token
        response.headers['X-User-ID'] = user_id
        
        response_body = {
            'username': username,
            'role_id': role_id,
            'role_name': role_name,
            'user_details': {
                'user_id': user_id,
                'first_name': first_name,
                'last_name': last_name,
                'phone_verified_p': phone_verified_p,
            },
            'merchant': merchant_details,
        }
        if customer:
            response_body['customer'] = customer
        
        response_body['action_name'] = 'login'
        response_body['status'] = 'successful'
    else:
        response_body = {
            'action': 'login',
            'status': 'failed',
            'message': 'invalid username or password',
        }

    response.data = json.dumps(response_body, default=str)
    return response

@access_management_blueprint.route('/logout', methods=['POST'])
def logout():
    access_token = request.headers['X-Access-Token']
    user_id = request.headers['X-User-ID']

    assert access_token, "access token error"

    db_engine = jqutils.get_db_engine()
    with db_engine.connect() as conn:
        query = text("""
            UPDATE
                user 
            SET
                access_token = NULL 
            WHERE
                user_id = :user_id
            AND
                access_token = :access_token
            AND
                meta_status = 'active'
        """)
        result = conn.execute(query, user_id=user_id, access_token=access_token)

        query = text("""
            INSERT INTO user_session (user_id, action, meta_status)
            VALUES(:user_id, :action, 'active') 
        """)
        result = conn.execute(query, user_id=user_id, action='logout').lastrowid

    response = Response(content_type='application/json')
    if result:
        response_body = {
            'user_id': user_id,
            'action': 'logout',
            'status': 'successful'
        }
    else:
        response_body = {
            'user_id': user_id,
            'action': 'logout',
            'status': 'failed'
        }
    response.data = json.dumps(response_body)
    return response

@access_management_blueprint.route('/soft-login', methods=['POST'])
def soft_login():
    request_body = request.json
    employee_id = request_body['employee_id']
    facility_id = request_body['facility_id']
    personal_access_code = request_body['personal_access_code']

    db_engine = jqutils.get_db_engine()

    # validate personal code
    query = text("""
        SELECT personal_access_code
        FROM employee
        WHERE employee_id = :employee_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, employee_id=employee_id, meta_status='active').fetchone()
        assert result, f"employee_id not found {employee_id}"

        personal_access_code_db = result['personal_access_code']

    if personal_access_code != personal_access_code_db:
        response_body = {
            'action': 'soft-login',
            'status': 'failed',
            'message': 'invalid personal code'
        }
        response = Response(content_type='application/json')
        response.data = json.dumps(response_body, default=str)
        return response

    # get latest employee_soft_session
    query = text(""" 
        SELECT employee_session_id, start_timestamp, end_timestamp
        FROM employee_soft_session
        WHERE employee_id = :employee_id
        AND facility_id = :facility_id
        AND meta_status = :meta_status
        ORDER BY start_timestamp DESC
        LIMIT 1
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, employee_id=employee_id, facility_id=facility_id, meta_status='active').fetchone()
    
    latest_state = 'logout'
    employee_session_id = None
    if result:
        latest_state = 'logout' if result['end_timestamp'] else 'login'
        employee_session_id = result['employee_session_id']

    action = 'login' if latest_state == 'logout' else 'logout'
    action_timestamp = jqutils.get_utc_datetime()

    if action == 'login':
        query = text(""" 
            INSERT INTO employee_soft_session (employee_id, facility_id, start_timestamp, meta_status)
            VALUES(:employee_id, :facility_id, :action_timestamp, :meta_status)
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, employee_id=employee_id, facility_id=facility_id, action_timestamp=action_timestamp, meta_status='active').lastrowid
            assert result, "employee soft session insert error"
    else:
        query = text(""" 
            UPDATE employee_soft_session
            SET end_timestamp = :action_timestamp
            WHERE employee_session_id = :employee_session_id
            AND meta_status = :meta_status
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, employee_id=employee_id, employee_session_id=employee_session_id, facility_id=facility_id, action_timestamp=action_timestamp, meta_status='active').rowcount
            assert result, "employee soft session update error"

        # mark this user as inactive if logging out
        query = text("""
            UPDATE employee_soft_session
            SET active_user_p = :inactive
            WHERE employee_id = :employee_id
            AND active_user_p = :active_user_p
            AND facility_id = :facility_id
            AND meta_status = :meta_status
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, employee_id=employee_id, facility_id=facility_id, active_user_p=1, inactive=0, meta_status='active').rowcount

    response = Response(content_type='application/json')
    response_body = {
        'employee_id': employee_id,
        'action_name': 'soft-login',
        'status': 'successful'
    }
    response.data = json.dumps(response_body, default=str)
    return response

@access_management_blueprint.route('/signup', methods=['POST'])
def signup():
    request_body = request.json
    response = Response(content_type='application/json')

    first_names_en = request_body['first_names_en']
    last_name_en = request_body['last_name_en']
    phone_nr = request_body['phone_nr']
    email = request_body['email'] if 'email' in request_body else None
    company_name = request_body['company_name'] if 'company_name' in request_body else None
    message = request_body['message'] if 'message' in request_body else None
    merchant_code = request_body['merchant_code'] if 'merchant_code' in request_body else None
    password = request_body['password'] if 'password' in request_body else None

    intent = request_body['intent'] if 'intent' in request_body else 'otp'

    invitation_code = request_body['invitation_code'] if 'invitation_code' in request_body else None
    invitation_id = None

    device_information = request_body['device_information']
    device_id = device_information['device_id']
    device_name = device_information['device_name']
    app_version = device_information['app_version']

    db_engine = jqutils.get_db_engine()

    merchant_id = None
    merchant_name = None
    
    if merchant_code:
        query = text("""
            SELECT merchant_id, merchant_name
            FROM merchant
            WHERE merchant_code = :merchant_code
            AND meta_status = :meta_status
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, merchant_code=merchant_code, meta_status='active').fetchone()
            assert result, f"merchant not found with code: {merchant_code}"
            merchant_id = result['merchant_id']
            merchant_name = result['merchant_name']

    if intent == 'otp':
        
        merchant_filter_statement = ""
        if merchant_id:
            merchant_filter_statement = "AND merchant_id = :merchant_id"
        
        query = text(f"""
            SELECT signup_request_id
            FROM signup_request
            WHERE phone_nr = :phone_nr
            {merchant_filter_statement}
            AND meta_status = :meta_status
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, phone_nr=phone_nr, merchant_id=merchant_id, meta_status='active').fetchone()
        
        merchant_filter_statement = ""
        if merchant_id:
            merchant_filter_statement = "AND umm.merchant_id = :merchant_id"
        
        query = text(f"""
            SELECT u.user_id
            FROM user u
            LEFT JOIN user_merchant_map umm ON u.user_id = umm.user_id
            WHERE u.phone_nr = :phone_nr
            {merchant_filter_statement}
            AND u.meta_status = :meta_status
        """)
        with db_engine.connect() as conn:
            result2 = conn.execute(query, phone_nr=phone_nr, merchant_id=merchant_id, meta_status='active').fetchone()

        if result or result2:
            response_body = {
                'action': 'signup',
                'status': 'failed',
                'message': 'phone number already exists.'
            }
            response.data = json.dumps(response_body)
            return response

        intent = 'customer_signup' if merchant_code else 'merchant_signup'
        user_id = None

        # Handle invitation code at time of signing up
        if invitation_code:
            invitation_type_list = ['join-merchant']
            
            # joining with role table to check if the invitation code is valid
            query = text("""
                SELECT i.invitation_id, i.invitation_expiry_timestamp, i.invitation_status
                FROM invitation i
                JOIN role r ON r.role_id = i.recipient_role_id
                WHERE i.invitation_code = :invitation_code
                AND i.invitation_type in :invitation_type_list
                AND i.meta_status = :meta_status
                ORDER BY i.insertion_timestamp DESC
            """)
            with db_engine.connect() as conn:
                result = conn.execute(query, invitation_code=invitation_code, invitation_type_list=invitation_type_list, meta_status='active').fetchone()

                if not result:
                    response_body = {
                        'action': 'signup',
                        'status': 'failed',
                        'message': 'invalid invitation code.'
                    }
                    response.data = json.dumps(response_body)
                    return response

                invitation_id = result['invitation_id']
                invitation_expiry_timestamp = result['invitation_expiry_timestamp']
                invitation_status = result['invitation_status']
                current_timestamp = datetime.datetime.now()

                if invitation_expiry_timestamp:
                    if current_timestamp > invitation_expiry_timestamp:
                        
                        # update invitation status if not already expired
                        if invitation_status != 'expired':
                            query = text("""
                                UPDATE invitation
                                SET invitation_status = :invitation_status
                                WHERE invitation_id = :invitation_id
                            """)
                            result = conn.execute(query, invitation_status='expired', invitation_id=invitation_id).rowcount
                            assert result, "invitation status update error"
                        
                        response_body = {
                            'action': 'signup',
                            'status': 'failed',
                            'message': 'invitation code expired.'
                        }
                        response.data = json.dumps(response_body)
                        return response
                    
                elif invitation_status != 'pending':
                    response_body = {
                        'action': 'signup',
                        'status': 'failed',
                        'message': 'invitation code already used or cancelled.'
                    }
                    response.data = json.dumps(response_body)
                    return response

        # Create user if customer is signing up
        if intent == 'customer_signup':
            phone_verified_p = False
            email_verified_p = False
            verification_status = "pending"
            business_designation = None
            root_p = 0
            user_code = jqutils.create_code_from_title(f"{first_names_en} {last_name_en}", 4)
            tenant_id = 1
            system_user_p = False

            # encrypt password if provided
            if password:
                password_manager = DataMigrationManager()
                password = password_manager.encrypt_password(password)
            
            query = text("""
                INSERT INTO user (username, password, user_code, first_names_en, last_name_en, business_designation, phone_nr, phone_verified_p, email, email_verified_p, verification_status, root_p, tenant_id, system_user_p, meta_status)
                VALUES (:username, :password, :user_code, :first_names_en, :last_name_en, :business_designation, :phone_nr, :phone_verified_p, :email, :email_verified_p, :verification_status, :root_p, :tenant_id, :system_user_p, :meta_status)
            """)
            with db_engine.connect() as conn:
                user_id = conn.execute(query, password=password, user_code=user_code, first_names_en=first_names_en, last_name_en=last_name_en, phone_nr=phone_nr, root_p=root_p, system_user_p=system_user_p, verification_status = verification_status,
                            username=phone_nr, business_designation=business_designation, phone_verified_p=phone_verified_p, email=email, email_verified_p=email_verified_p, tenant_id=tenant_id, meta_status="pending").lastrowid
                assert user_id, "unable to create user"
            
            role_id = jqutils.get_id_by_name("customer", "role_name", "role")

            query = text("""
                INSERT INTO user_role_map (user_id, role_id, meta_status)
                VALUES (:user_id, :role_id, :meta_status)
            """)
            with db_engine.connect() as conn:
                result = conn.execute(query, user_id=user_id, role_id=role_id, meta_status="active").lastrowid
                assert result, "unable to create user role map"

            query = text("""
                INSERT INTO user_merchant_map (user_id, merchant_id, meta_status)
                VALUES (:user_id, :merchant_id, :meta_status)
            """)
            with db_engine.connect() as conn:
                result = conn.execute(query, user_id=user_id, merchant_id=merchant_id, meta_status="active").lastrowid
                assert result, "unable to create user merchant map"

        # generate signup request
        query = text("""
            INSERT INTO signup_request (first_names_en, last_name_en, user_id, merchant_id, phone_nr, email, company_name, message, device_id, device_name, app_version, invitation_id, signup_request_status, meta_status)
            VALUES(:first_names_en, :last_name_en, :user_id, :merchant_id, :phone_nr, :email, :company_name, :message, :device_id, :device_name, :app_version, :invitation_id, :signup_request_status, :meta_status)
        """)
        with db_engine.connect() as conn:
            signup_request_id = conn.execute(query, first_names_en=first_names_en, last_name_en=last_name_en, phone_nr=phone_nr, device_id=device_id, invitation_id=invitation_id, user_id=user_id, merchant_id=merchant_id,
                    email=email, company_name=company_name, message=message, device_name=device_name, app_version=app_version, signup_request_status='pending', meta_status='active').lastrowid
            assert signup_request_id, "signup request insert error"

        # send out phone sms otp
        contact_method = 'sms'
        access_ninja.generate_otp(contact_method, intent, signup_request_id=signup_request_id, phone_nr=phone_nr, merchant_name=merchant_name)

        # inform tech support of signup request
        if intent == "customer_signup":            
            my_utils.publish_tech_support_message(f"{first_names_en} {last_name_en} with phone_nr: {phone_nr} has tried to sign up on MyApp ({merchant_name})", "customer-signup", signup_request_id=signup_request_id)
        else:
            my_utils.publish_tech_support_message(f"{first_names_en} {last_name_en} with phone_nr: {phone_nr} has tried to sign up on iBlinkPay", "user-signup", signup_request_id=signup_request_id)
    
    else:
        # generate signup request
        query = text("""
            INSERT INTO signup_request (first_names_en, last_name_en, phone_nr, email, company_name, message, device_id, device_name, app_version, invitation_id, signup_request_status, meta_status)
            VALUES(:first_names_en, :last_name_en, :phone_nr, :email, :company_name, :message, :device_id, :device_name, :app_version, :invitation_id, :signup_request_status, :meta_status)
        """)
        with db_engine.connect() as conn:
            signup_request_id = conn.execute(query, first_names_en=first_names_en, last_name_en=last_name_en, phone_nr=phone_nr, device_id=device_id, invitation_id=invitation_id, email=email,
                    company_name=company_name, message=message, device_name=device_name, app_version=app_version, signup_request_status='pending', meta_status='active').lastrowid
            assert signup_request_id, "signup request insert error"
        
        my_utils.publish_tech_support_message(f"{first_names_en} {last_name_en} with phone_nr: {phone_nr} has reached out for details", "contact-us", signup_request_id=signup_request_id)
        
        if os.getenv("ENV") == "production":
            aws_utils.publish_email(
                source="noreply@iblinknext.com",
                destination={
                    "ToAddresses": ["sales@iblinkx.com"],
                },
                subject=f"New Contact Us Request from {first_names_en} {last_name_en}",
                text=f"{first_names_en} {last_name_en} with phone_nr: {phone_nr} email: {email} company_name: {company_name} has reached out for details",
                html=f"{first_names_en} {last_name_en} with phone_nr: {phone_nr} email: {email} company_name: {company_name} has reached out for details"
            )
    
    response_body = {
        'action': 'signup',
        'status': 'successful'
    }
    response.data = json.dumps(response_body, default=str)
    return response

@access_management_blueprint.route('/email-signup', methods=['POST'])
def emailSignup():
    request_body = request.json
    response = Response(content_type='application/json')

    email = request_body['email']
    signup_request_id = None
    one_time_password_id = None
    user_id = None

    db_engine = jqutils.get_db_engine()

    query = text("""
        SELECT signup_request_id, user_id, signup_request_status
        FROM signup_request
        WHERE email = :email
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, email=email, meta_status='active').fetchone()

    if result:
        signup_request_status = result["signup_request_status"]
        if signup_request_status == "verified":
            response_body = {
                'user_id': result["user_id"],
                'action': 'signup',
                'status': 'failed',
                'message': 'signup request already completed.'
            }
            response.data = json.dumps(response_body, default=str)
            return response

        signup_request_id = result["signup_request_id"]

        query = text("""
            SELECT one_time_password_id
            FROM one_time_password
            WHERE signup_request_id = :signup_request_id
            AND meta_status = :meta_status
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, signup_request_id=signup_request_id, meta_status='active').fetchone()
            one_time_password_id = result["one_time_password_id"]

    query = text("""
        SELECT user_id, email_verified_p
        FROM user
        WHERE email = :email
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, email=email, meta_status='active').fetchone()

    if result:
        email_verified_p = result["email_verified_p"]
        if email_verified_p:
            response_body = {
                'user_id': result["user_id"],
                'action': 'signup',
                'status': 'failed',
                'message': 'user already exists. log-in instead.'
            }
            response.data = json.dumps(response_body, default=str)
            return response

        user_id = result["user_id"]
    
    if not signup_request_id and not user_id:
        # generate signup request
        query = text("""
            INSERT INTO signup_request (email, signup_request_status, meta_status)
            VALUES(:email, :signup_request_status, :meta_status)
        """)
        with db_engine.connect() as conn:
            signup_request_id = conn.execute(query, email=email, signup_request_status='pending', meta_status='active').lastrowid
            assert signup_request_id, "signup request insert error"

    my_utils.publish_tech_support_message(f"A user with email: {email} has tried to sign up on iBlinkPay", "user-signup", user_id=user_id, signup_request_id=signup_request_id)

    # send out email otp
    contact_method = 'email'
    intent = 'merchant_signup'
    access_ninja.generate_otp(contact_method, intent, signup_request_id=signup_request_id, one_time_password_id=one_time_password_id, user_id=user_id, email=email, email_intent='account_setup')
    
    response_body = {
        'signup_request_id': signup_request_id,
        'action': 'email-signup',
        'status': 'successful'
    }
    response.data = json.dumps(response_body, default=str)
    return response

@access_management_blueprint.route('/request-otp', methods=['POST'])
def request_otp():

    request_body = request.json
    phone_nr = request_body['phone_nr']
    email = request_body['email']
    intent = request_body['intent']
    contact_method = request_body['contact_method'] if 'contact_method' in request_body else None
    
    response = Response(content_type='application/json')
    db_engine = jqutils.get_db_engine()

    if intent == 'soft_login':
        query = text("""
            SELECT u.user_id, otp.otp_request_count, otp.one_time_password_id, otp.otp_requested_timestamp,
            otp.otp_status, otp.contact_method
            FROM user u
            LEFT JOIN one_time_password otp ON otp.user_id = u.user_id
            AND otp.intent = :intent
            WHERE u.phone_nr = :phone_nr
            AND u.meta_status = :status
            ORDER BY otp.otp_requested_timestamp DESC
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, phone_nr=phone_nr, intent=intent, status='active').fetchone()
            
            if not result:
                response_body = {
                    'action': 'request_otp',
                    'status': 'failed',
                    'message': 'phone number not found.'
                }
                response.data = json.dumps(response_body)
                return response

            user_id = result['user_id']
    
    elif intent == 'email_verification':
        query = text("""
            SELECT u.user_id, otp.otp_request_count, otp.one_time_password_id, otp.otp_requested_timestamp,
            otp.otp_status, otp.contact_method
            FROM user u
            LEFT JOIN one_time_password otp ON otp.user_id = u.user_id
            AND otp.intent = :intent
            WHERE u.email = :email
            AND u.meta_status = :status
            ORDER BY otp.otp_requested_timestamp DESC
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, email=email, intent=intent, status='active').fetchone()
            
            if not result:
                response_body = {
                    'action': 'request_otp',
                    'status': 'failed',
                    'message': 'email not found.'
                }
                response.data = json.dumps(response_body)
                return response

            user_id = result['user_id']
    
    else:
        query = text("""
            SELECT sr.signup_request_id, sr.signup_request_status, sr.user_id, m.merchant_name, otp.one_time_password_id,
            otp.otp_request_count, otp.otp_requested_timestamp, otp.otp_status, otp.contact_method
            FROM signup_request sr
            LEFT JOIN one_time_password otp ON sr.signup_request_id = otp.signup_request_id
            LEFT JOIN merchant m ON sr.merchant_id = m.merchant_id
            AND otp.intent = :intent
            WHERE ( sr.phone_nr = :phone_nr OR sr.email = :email )
            AND sr.meta_status = :status
            ORDER BY otp.otp_requested_timestamp DESC
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, phone_nr=phone_nr, email=email, status='active', intent=intent).fetchone()
            assert result, "phone number not found"

        signup_request_id = result['signup_request_id']
        signup_request_status = result['signup_request_status']
        user_id = result['user_id']
        merchant_name = result['merchant_name']
        if signup_request_status == "verified":
            response_body = {
                'action': 'request_otp',
                'status': 'failed',
                'message': 'phone number already verified.'
            }
            response.data = json.dumps(response_body, default=str)
            return response

    one_time_password_id = result['one_time_password_id']
    otp_status = result['otp_status']
    otp_request_count = result['otp_request_count']
    if not contact_method:
        contact_method = result['contact_method']

    # handle existing otp request, if exists
    if one_time_password_id and otp_status == 'sent':
        otp_requested_timestamp = result['otp_requested_timestamp']
        otp_request_count = otp_request_count + 1
        current_timestamp = datetime.datetime.now()

        if current_timestamp - otp_requested_timestamp < datetime.timedelta(seconds=30):
            response_body = {
                'action': 'request_otp',
                'status': 'failed',
                'message': 'please wait 30 seconds before requesting another otp.'
            }
            response.data = json.dumps(response_body, default=str)
            return response
    
    # generate random numeric 6 digit otp
    otp = random.randint(100000, 999999)
    otp_requested_timestamp = datetime.datetime.now()

    # create a new otp request if not exists or if previous otp request isn't pending
    if ( not one_time_password_id or otp_status != "sent"):

        if intent == 'soft_login':
            # send out phone sms otp
            contact_method = "sms"
            access_ninja.generate_otp(contact_method, intent, user_id=user_id, phone_nr=phone_nr)
        
        elif intent == 'email_verification':
            # send out email otp
            contact_method = "email"
            access_ninja.generate_otp(contact_method, intent, user_id=user_id, email=email)
            
        elif intent == 'merchant_signup':
            # send out email otp
            contact_method = "email"
            access_ninja.generate_otp(contact_method, intent, user_id=user_id, email=email, email_intent="account_setup")
        
        elif intent == 'customer_signup':
            # send out phone sms otp
            contact_method = "sms"
            access_ninja.generate_otp(contact_method, intent, user_id=user_id, phone_nr=phone_nr, merchant_name=merchant_name)

    # handle existing otp request
    else:

        if intent == 'merchant_signup':
            access_ninja.generate_otp(contact_method, intent, one_time_password_id=one_time_password_id, signup_request_id=signup_request_id, phone_nr=phone_nr, email=email, email_intent="account_setup")
        elif intent == 'customer_signup':
            access_ninja.generate_otp(contact_method, intent, one_time_password_id=one_time_password_id, signup_request_id=signup_request_id, phone_nr=phone_nr, merchant_name=merchant_name)
        else:
            access_ninja.generate_otp(contact_method, intent, one_time_password_id=one_time_password_id, user_id=user_id, email=email, phone_nr=phone_nr)
    
    response_body = {
        'action': 'request_otp',
        'status': 'successful'
    }
    response.data = json.dumps(response_body, default=str)
    return response

@access_management_blueprint.route('/verify-otp', methods=['POST'])
def verify_otp():

    request_body = request.json
    phone_nr = request_body['phone_nr']
    email = request_body['email']
    otp = request_body['otp']
    intent = request_body['intent']

    contact_method = request_body['contact_method'] if 'contact_method' in request_body else 'sms'
    password = request_body['password'] if 'password' in request_body else None
    
    user_details = None
    merchant_id = None

    response = Response(content_type='application/json')
    db_engine = jqutils.get_db_engine()

    if intent == "soft_login":
        contact_method = "sms"
    
        query = text("""
            SELECT u.user_id, otp.one_time_password_id, otp.otp, otp.otp_status, otp.otp_expiry_timestamp
            FROM one_time_password otp
            JOIN user u ON otp.user_id = u.user_id
            WHERE u.phone_nr = :phone_nr
            AND otp.contact_method = :contact_method
            AND otp.intent = :intent
            AND u.meta_status = :status_active
            ORDER BY otp.otp_requested_timestamp DESC
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, phone_nr=phone_nr, status_active='active', contact_method=contact_method, intent=intent).fetchone()
            assert result, "soft login: no valid otp found for phone number: " + phone_nr
        
        user_id = result['user_id']
        one_time_password_id = result['one_time_password_id']
        otp_db = result['otp']
        otp_status = result['otp_status']
        otp_expiry_timestamp = result['otp_expiry_timestamp']
    
    elif intent == "email_verification":
        contact_method = "email"
    
        query = text("""
            SELECT u.user_id, otp.one_time_password_id, otp.otp, otp.otp_status, otp.otp_expiry_timestamp
            FROM one_time_password otp
            JOIN user u ON otp.user_id = u.user_id
            WHERE u.email = :email
            AND otp.contact_method = :contact_method
            AND otp.intent = :intent
            AND u.meta_status = :status_active
            ORDER BY otp.otp_requested_timestamp DESC
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, email=email, status_active='active', contact_method=contact_method, intent=intent).fetchone()
            assert result, "email verification: no valid otp found for email: " + email
        
        user_id = result['user_id']
        one_time_password_id = result['one_time_password_id']
        otp_db = result['otp']
        otp_status = result['otp_status']
        otp_expiry_timestamp = result['otp_expiry_timestamp']
    
    else:        
        # check status for otp
        query = text("""
            SELECT sr.signup_request_id, sr.user_id, sr.merchant_id, sr.signup_request_status, sr.first_names_en, sr.last_name_en, sr.invitation_id,
            otp.one_time_password_id, otp.otp, otp.otp_status, otp.otp_expiry_timestamp
            FROM signup_request sr
            LEFT JOIN one_time_password otp ON sr.signup_request_id = otp.signup_request_id
            WHERE sr.phone_nr = :phone_nr
            OR sr.email = :email
            AND otp.contact_method = :contact_method
            AND sr.meta_status = :status_active
            ORDER BY otp.otp_requested_timestamp DESC
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, phone_nr=phone_nr, email=email, status_active='active', contact_method=contact_method).fetchone()
            assert result, "signup request: no valid otp found"

        signup_request_id = result['signup_request_id']
        signup_request_status = result['signup_request_status']
        signup_request_first_name = result['first_names_en']
        signup_request_last_name = result['last_name_en']
        invitation_id = result['invitation_id']
        user_id = result['user_id']
        merchant_id = result['merchant_id']
        one_time_password_id = result['one_time_password_id']
        otp_db = result['otp']
        otp_status = result['otp_status']
        otp_expiry_timestamp = result['otp_expiry_timestamp']
    
    # TODO: handle expired otp

    if otp != otp_db:
        response_body = {
            'action': 'verify_otp',
            'status': 'failed',
            'message': 'invalid otp code'
        }
        response.data = json.dumps(response_body, default=str)
        return response

    # Handle a new user signup or login
    if intent in ["merchant_signup", "customer_signup"] or intent == "soft_login":

        # check if user already exists
        if user_id:
            query = text("""
                SELECT username, password, first_names_en, last_name_en, phone_nr, email, meta_status
                FROM user
                WHERE user_id = :user_id
            """)
            with db_engine.connect() as conn:
                result = conn.execute(query, user_id=user_id).fetchone()
                assert result, "user not found"
            
            username = result['username']
            existing_password = result['password']
            first_names_en = result['first_names_en']
            last_name_en = result['last_name_en']
            existing_phone_nr = result['phone_nr']
            existing_email = result['email']
            meta_status = result['meta_status']
            phone_verified_p = True if contact_method == 'sms' else False
            email_verified_p = True if contact_method == 'email' else False
            customer_code = jqutils.create_code_from_title(f"{first_names_en} {last_name_en}", 4)

            if password and existing_password is None:
                # encrypt password if provided
                password_manager = DataMigrationManager()
                password = password_manager.encrypt_password(password)

                # update password if not already set
                query = text(f"""
                    UPDATE user
                    SET password = :password, meta_status = :meta_status,
                    phone_verified_p = :phone_verified_p, email_verified_p = :email_verified_p
                    WHERE user_id = :user_id
                """)
                with db_engine.connect() as conn:
                    result = conn.execute(query, password=password, phone_verified_p=phone_verified_p, email_verified_p=email_verified_p,
                                            user_id=user_id, meta_status='active').rowcount
                    assert result, "user not updated"
            
            elif meta_status != 'active':
                # update status if not already active
                query = text(f"""
                    UPDATE user
                    SET meta_status = :meta_status, phone_verified_p = :phone_verified_p, email_verified_p = :email_verified_p
                    WHERE user_id = :user_id
                """)
                with db_engine.connect() as conn:
                    result = conn.execute(query, user_id=user_id, phone_verified_p=phone_verified_p, email_verified_p=email_verified_p, meta_status='active').rowcount
                    assert result, "user not updated"

            # get role for user
            get_role_query = text("""
                select r.role_id, r.role_name
                from user_role_map urm
                inner join role r on r.role_id = urm.role_id
                where urm.user_id = :user_id
                and r.meta_status = :meta_status
                and urm.meta_status = :meta_status
            """)
            with db_engine.connect() as conn:
                role_permissions_result = conn.execute(get_role_query, user_id=user_id, meta_status='active').fetchone()
                
                if not role_permissions_result:
                    response_body = {
                        'action': 'verify_otp',
                        'status': 'failed',
                        'message': 'user has no assigned role',
                    }

                    response.data = json.dumps(response_body, default=str)
                    return response

            assigned_role_id = role_permissions_result['role_id']
            role_name = role_permissions_result['role_name']

            # get merchant for user if doing customer_signup
            if intent == "customer_signup":
                
                # get merchant for user
                query = text("""
                    SELECT merchant_id
                    FROM user_merchant_map
                    WHERE user_id = :user_id
                    AND meta_status = :meta_status
                """)
                with db_engine.connect() as conn:
                    result = conn.execute(query, user_id=user_id, meta_status='active').fetchone()
                    assert result, "user not mapped to any merchant"
                    merchant_id = result['merchant_id']
                
                # create customer for the user
                query = text("""
                    INSERT INTO customer (customer_code, merchant_id, customer_first_name, customer_last_name, customer_email, customer_phone_nr, meta_status)
                    VALUES (:customer_code, :merchant_id, :customer_first_name, :customer_last_name, :customer_email, :customer_phone_nr, :meta_status)
                """)
                with db_engine.connect() as conn:
                    customer_id = conn.execute(query, customer_code=customer_code, merchant_id=merchant_id, customer_first_name=first_names_en, customer_last_name=last_name_en, customer_email=existing_email, customer_phone_nr=existing_phone_nr, meta_status="active").lastrowid
                    assert customer_id, "unable to create customer"
                
                # create user customer map
                query = text("""
                    INSERT INTO user_customer_map (user_id, customer_id, meta_status)
                    VALUES (:user_id, :customer_id, :meta_status)
                """)
                with db_engine.connect() as conn:
                    result = conn.execute(query, user_id=user_id, customer_id=customer_id, meta_status="active").rowcount
                    assert result, "unable to create user customer map"

        # signup a new user
        else:
            username = None
            phone_verified_p = True if contact_method == 'sms' else False
            email_verified_p = True if contact_method == 'email' else False
            verification_status = "pending"
            first_names_en = signup_request_first_name
            last_name_en = signup_request_last_name
            business_designation = None
            root_p = 0
            user_code = jqutils.create_code_from_title(f"{first_names_en} {last_name_en}", 4)
            tenant_id = 1
            system_user_p = False
            current_timestamp = datetime.datetime.now()
            all_facility_access_p = 1
            
            if password:
                username = email
                password_bytes = password.encode()
                
                # encrypt password and update user
                query = text(""" 
                        select symmetric_key 
                        from payment_api_secret 
                        where description = 'password-protector-key' and
                        meta_status = :meta_status
                    """)
                with db_engine.connect() as conn:
                    result = conn.execute(query, meta_status='active').fetchone()
                    assert result, "no valid symmetric key found for password protector"
                    key_string_db = result['symmetric_key']
                    key_string_db_bytes = key_string_db.encode()
                
                password = jqsecurity.encrypt_bytes_symmetric_to_bytes(password_bytes, key_string_db_bytes)
            
            query = text("""
                INSERT INTO user (username, password, user_code, first_names_en, last_name_en, business_designation, phone_nr, phone_verified_p, email, email_verified_p, verification_status, all_facility_access_p, root_p, tenant_id, system_user_p, meta_status)
                VALUES (:username, :password, :user_code, :first_names_en, :last_name_en, :business_designation, :phone_nr, :phone_verified_p, :email, :email_verified_p, :verification_status, :all_facility_access_p, :root_p, :tenant_id, :system_user_p, :meta_status)
            """)
            with db_engine.connect() as conn:
                user_id = conn.execute(query, password=password, user_code=user_code, first_names_en=first_names_en, last_name_en=last_name_en, phone_nr=phone_nr, all_facility_access_p=all_facility_access_p, root_p=root_p, system_user_p=system_user_p, verification_status = verification_status,
                            username=username, business_designation=business_designation, phone_verified_p=phone_verified_p, email=email, email_verified_p=email_verified_p, tenant_id=tenant_id, meta_status="active").lastrowid
                assert user_id, "unable to create user"

            if invitation_id:
                
                # get invitation details
                query = text("""
                    SELECT i.merchant_id, i.recipient_role_id, r.role_name
                    FROM invitation i
                    JOIN role r ON r.role_id = i.recipient_role_id
                    WHERE i.invitation_id = :invitation_id
                    AND i.meta_status = :status
                """)
                with db_engine.connect() as conn:
                    result = conn.execute(query, invitation_id=invitation_id, status='active').fetchone()
                    assert result, "invitation not found"
                    merchant_id = result['merchant_id']
                    assigned_role_id = result['recipient_role_id']
                    role_name = result['role_name']
                
                # assign user to merchant
                query = text("""
                    INSERT INTO user_merchant_map (user_id, merchant_id, meta_status)
                    VALUES (:user_id, :merchant_id, :meta_status)
                """)
                with db_engine.connect() as conn:
                    result = conn.execute(query, user_id=user_id, merchant_id=merchant_id, meta_status="active").rowcount
                    assert result, "unable to assign user to merchant"
                
                # update invitation status
                query = text("""
                    UPDATE invitation
                    SET invitation_status = :invitation_status,
                    invitation_accepted_timestamp = :invitation_accepted_timestamp
                    WHERE invitation_id = :invitation_id
                """)
                with db_engine.connect() as conn:
                    result = conn.execute(query, invitation_status="accepted", invitation_accepted_timestamp=current_timestamp, invitation_id=invitation_id).rowcount
                    assert result, "unable to update invitation status"

                # get payment point area for merchant
                query = text("""
                    SELECT payment_point_area_id
                    FROM payment_point_area
                    WHERE merchant_id = :merchant_id
                    AND meta_status = :meta_status
                    ORDER BY payment_point_area_id ASC
                """)
                with db_engine.connect() as conn:
                    result = conn.execute(query, merchant_id=merchant_id, meta_status='active').fetchone()
                    assert result, "payment point area not found"
                    payment_point_area_id = result['payment_point_area_id']

                # create user payment point area map for user
                query = text("""
                    INSERT INTO user_payment_point_area_map(payment_point_area_id, user_id, default_p, meta_status)
                    VALUES(:payment_point_area_id, :user_id, :default_p, :meta_status)
                """)
                with db_engine.connect() as conn:
                    result = conn.execute(query, payment_point_area_id=payment_point_area_id, user_id=user_id, default_p=1, meta_status='active').rowcount
                    assert result, f"User Payment Point Area Map with payment_point_area_id ({payment_point_area_id}) not created for user id ({user_id})"

            else:
                # use merchant role as default if merchant_id not provided
                role_name = "customer" if merchant_id else "merchant"
                assigned_role_id = jqutils.get_id_by_name(role_name, "role_name", "role")

                if merchant_id:
                    # assign user to merchant
                    query = text("""
                        INSERT INTO user_merchant_map (user_id, merchant_id, meta_status)
                        VALUES (:user_id, :merchant_id, :meta_status)
                    """)
                    with db_engine.connect() as conn:
                        result = conn.execute(query, user_id=user_id, merchant_id=merchant_id, meta_status="active").rowcount
                        assert result, "unable to assign user to merchant"
                    
                    # create customer for the user
                    query = text("""
                        INSERT INTO customer (customer_code, merchant_id, customer_first_name, customer_last_name, customer_email, customer_phone_nr, meta_status)
                        VALUES (:customer_code, :merchant_id, :customer_first_name, :customer_last_name, :customer_email, :customer_phone_nr, :meta_status)
                    """)
                    with db_engine.connect() as conn:
                        customer_id = conn.execute(query, customer_code=user_code, merchant_id=merchant_id, customer_first_name=first_names_en, customer_last_name=last_name_en, customer_email=email, customer_phone_nr=phone_nr, meta_status="active").lastrowid
                        assert customer_id, "unable to create customer"
                    
                    # create user customer map
                    query = text("""
                        INSERT INTO user_customer_map (user_id, customer_id, meta_status)
                        VALUES (:user_id, :customer_id, :meta_status)
                    """)
                    with db_engine.connect() as conn:
                        result = conn.execute(query, user_id=user_id, customer_id=customer_id, meta_status="active").rowcount
                        assert result, "unable to create user customer map"

            # assign role to user
            query = text("""
                INSERT INTO user_role_map (user_id, role_id, meta_status)
                VALUES (:user_id, :role_id, :meta_status)
            """)
            with db_engine.connect() as conn:
                result = conn.execute(query, user_id=user_id, role_id=assigned_role_id, meta_status="active").rowcount
                assert result, "unable to assign role to user"

            if role_name == "merchant":
                assigned_policy_id = jqutils.get_id_by_name("administrator-access", "policy_name", "policy")

                query = text("""
                    INSERT INTO employee (user_id, first_names_en, last_name_en, phone_nr, email, merchant_id, soft_login_required_p, all_facility_access_p, meta_status)
                    VALUES (:user_id, :first_names_en, :last_name_en, :phone_nr, :email, :merchant_id, :soft_login_required_p, :all_facility_access_p, :meta_status)
                """)
                with db_engine.connect() as conn:
                    result = conn.execute(query, user_id=user_id, first_names_en=first_names_en, last_name_en=last_name_en, phone_nr=phone_nr, email=email, merchant_id=merchant_id, soft_login_required_p=False, all_facility_access_p=True, meta_status="active").lastrowid
                    assert result, "unable to create employee"
                    employee_id = result

                query = text("""
                    INSERT INTO employee_policy_map (employee_id, policy_id, meta_status)
                    VALUES (:employee_id, :policy_id, :meta_status)
                """)
                with db_engine.connect() as conn:
                    result = conn.execute(query, employee_id=employee_id, policy_id=assigned_policy_id, meta_status="active").rowcount
                    assert result, "unable to assign policy to employee"

            # update signup_request
            query = text("""
                UPDATE signup_request
                SET user_id = :user_id
                WHERE signup_request_id = :signup_request_id
            """)
            with db_engine.connect() as conn:
                result = conn.execute(query, user_id=user_id, signup_request_id=signup_request_id).rowcount
                assert result, "signup_request update error"

        # get access token for user
        access_token = access_ninja.get_user_access_token(user_id)

        # get merchant details for the user
        merchant_details = access_ninja.get_merchant_details_for_user(user_id)
        
        customer = None
        if role_name == "customer":
            query = text("""
                SELECT c.customer_id, ucm.user_customer_map_id, c.customer_code, c.stripe_customer_id, c.merchant_id, c.customer_first_name, c.customer_last_name, c.customer_email, c.customer_phone_nr, c.customer_remote_id, c.customer_gender, c.customer_dob
                FROM customer c
                LEFT JOIN user_customer_map ucm ON c.customer_id = ucm.customer_id
                WHERE ucm.user_id = :user_id
                AND c.meta_status = 'active'
            """)
            with db_engine.connect() as conn:
                result = conn.execute(query, user_id=user_id).fetchone()
            customer = dict(result)
        
        # log user session
        session_insert_query = text(""" 
            insert into user_session (user_id, action, meta_status)
            values(:user_id, :action, 'active') 
        """)
        with db_engine.connect() as conn:
            result = conn.execute(session_insert_query, user_id=user_id, action='login').lastrowid

        response.headers['X-Access-Token'] = access_token
        response.headers['X-User-ID'] = user_id
        
        user_details = {
            'username': username,
            'role_id': assigned_role_id,
            'role_name': role_name,
            'user_details': {
                'user_id': user_id,
                'first_name': first_names_en,
                'last_name': last_name_en,
                'phone_verified_p': phone_verified_p,
                'email_verified_p': email_verified_p,
            },
            'merchant': merchant_details,
        }
        
        if customer:
            user_details['customer'] = customer
            
        response.headers['X-Access-Token'] = access_token
        response.headers['X-User-ID'] = user_id
    
    elif intent == "email_verification":

        # update user email verification status
        query = text("""
            UPDATE user
            SET email_verified_p = :email_verified_p
            WHERE user_id = :user_id
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, email_verified_p=True, user_id=user_id).rowcount
            assert result, "user email verification update error"

    if otp_status != "verified":
        otp_status = 'verified'
        otp_verified_timestamp = datetime.datetime.now()
        
        # update otp status
        query = text("""
            UPDATE one_time_password otp
            SET otp.otp_status = :otp_status, otp.otp_verified_timestamp = :otp_verified_timestamp
            WHERE otp.one_time_password_id = :one_time_password_id
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, otp_status=otp_status, otp_verified_timestamp=otp_verified_timestamp, one_time_password_id=one_time_password_id).rowcount
            assert result, "otp status update error"
    
    if intent in ["merchant_signup", "customer_signup"] and signup_request_status != "verified":
        signup_request_status = 'verified'

        # update signup request status
        query = text("""
            UPDATE signup_request
            SET signup_request_status = :signup_request_status
            WHERE signup_request_id = :signup_request_id
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, signup_request_id=signup_request_id, signup_request_status=signup_request_status).rowcount
            assert result, "otp status update error"

    response_body = {
        'action': 'verify_otp',
        'status': 'successful'
    }
    if user_details:
        response_body['data'] = user_details

    response.data = json.dumps(response_body, default=str)
    return response

@access_management_blueprint.route('/social-media-login', methods=['POST'])
def social_media_login():
    request_body = request.json
    response = Response(content_type='application/json')

    social_media_name = request_body["social_media_name"]
    email = request_body["email"]
    social_media_external_id = request_body["social_media_external_id"]

    db_engine = jqutils.get_db_engine()

    # get social media id
    query = text("""
        SELECT social_media_id
        FROM social_media
        WHERE social_media_name = :social_media_name
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, social_media_name=social_media_name, meta_status='active').fetchone()
        assert result, "unknown social media name"
        social_media_id = result['social_media_id']
    
    # check if user social media mapping already exists
    query = text("""
        SELECT u.user_id, u.username, u.phone_verified_p, u.first_names_en, u.last_name_en
        FROM user_social_media_map usmm
        JOIN user u ON u.user_id = usmm.user_id
        WHERE usmm.social_media_external_id = :social_media_external_id
        AND usmm.social_media_id = :social_media_id
        AND u.meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, social_media_external_id=social_media_external_id, social_media_id=social_media_id,
                                meta_status='active').fetchone()
    
    # check if user already exists
    query = text("""
        SELECT user_id, username, phone_verified_p, first_names_en, last_name_en
        FROM user
        WHERE email = :email
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        user_result = conn.execute(query, email=email, meta_status='active').fetchone()
    
    # if social media mapping exists, return user details
    if result:
        user_id = result['user_id']
        username = result['username']
        first_names_en = result['first_names_en']
        last_name_en = result['last_name_en']
        phone_verified_p = result['phone_verified_p']

        # get role for user
        get_role_query = text("""
            select r.role_id, r.role_name
            from user_role_map urm
            inner join role r on r.role_id = urm.role_id
            where urm.user_id = :user_id
            and r.meta_status = :meta_status
            and urm.meta_status = :meta_status
        """)
        with db_engine.connect() as conn:
            role_permissions_result = conn.execute(get_role_query, user_id=user_id, meta_status='active').fetchone()
            
            if not role_permissions_result:
                response_body = {
                    'action': 'social_media_login',
                    'status': 'failed',
                    'message': 'user has no assigned role',
                }

                response.data = json.dumps(response_body, default=str)
                return response

        role_id = role_permissions_result['role_id']
        role_name = role_permissions_result['role_name']

    elif user_result:
        
        user_id = user_result['user_id']
        username = user_result['username']
        first_names_en = user_result['first_names_en']
        last_name_en = user_result['last_name_en']
        phone_verified_p = user_result['phone_verified_p']

        # add missing user_social_media_map entry
        query = text("""
            INSERT INTO user_social_media_map (user_id, social_media_id, social_media_external_id, meta_status)
            VALUES (:user_id, :social_media_id, :social_media_external_id, :meta_status)
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, user_id=user_id, social_media_id=social_media_id, social_media_external_id=social_media_external_id, meta_status="active").rowcount
            assert result, "unable to assign social media to user"

        # get role for user
        get_role_query = text("""
            select r.role_id, r.role_name
            from user_role_map urm
            inner join role r on r.role_id = urm.role_id
            where urm.user_id = :user_id
            and r.meta_status = :meta_status
            and urm.meta_status = :meta_status
        """)
        with db_engine.connect() as conn:
            role_permissions_result = conn.execute(get_role_query, user_id=user_id, meta_status='active').fetchone()
            
            if not role_permissions_result:
                response_body = {
                    'action': 'social_media_login',
                    'status': 'failed',
                    'message': 'user has no assigned role',
                }

                response.data = json.dumps(response_body, default=str)
                return response

        role_id = role_permissions_result['role_id']
        role_name = role_permissions_result['role_name']

    else:

        # create a new user
        username = email
        phone_nr = None
        phone_verified_p = False
        email_verified_p = True
        verification_status = "verified"
        first_names_en = None
        last_name_en = None
        business_designation = None
        root_p = 0
        user_code = jqutils.create_code_from_title(f"{first_names_en} {last_name_en}", 4)
        tenant_id = 1
        system_user_p = False
        
        query = text("""
            INSERT INTO user (username, user_code, first_names_en, last_name_en, business_designation, phone_nr, phone_verified_p, email, email_verified_p, verification_status, root_p, tenant_id, system_user_p, meta_status)
            VALUES (:username, :user_code, :first_names_en, :last_name_en, :business_designation, :phone_nr, :phone_verified_p, :email, :email_verified_p, :verification_status, :root_p, :tenant_id, :system_user_p, :meta_status)
        """)
        with db_engine.connect() as conn:
            user_id = conn.execute(query, user_code=user_code, first_names_en=first_names_en, last_name_en=last_name_en, phone_nr=phone_nr, root_p=root_p, system_user_p=system_user_p, verification_status = verification_status,
                        username=username, business_designation=business_designation, phone_verified_p=phone_verified_p, email=email, email_verified_p=email_verified_p, tenant_id=tenant_id, meta_status="active").lastrowid
            assert user_id, "unable to create user"

        # use merchant role as default
        role_name = "merchant"

        query = text("""
            SELECT role_id
            FROM role
            WHERE role_name = :role_name
            AND meta_status = :status
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, role_name=role_name, status='active').fetchone()
            assert result, "unable to get merchant role"
            role_id = result['role_id']

        # assign role to user
        query = text("""
            INSERT INTO user_role_map (user_id, role_id, meta_status)
            VALUES (:user_id, :role_id, :meta_status)
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, user_id=user_id, role_id=role_id, meta_status="active").rowcount
            assert result, "unable to assign role to user"
        
        # assign social media to user
        query = text("""
            INSERT INTO user_social_media_map (user_id, social_media_id, social_media_external_id, meta_status)
            VALUES (:user_id, :social_media_id, :social_media_external_id, :meta_status)
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, user_id=user_id, social_media_id=social_media_id, social_media_external_id=social_media_external_id, meta_status="active").rowcount
            assert result, "unable to assign social media to user"
    
    # get access token for user
    access_token = access_ninja.get_user_access_token(user_id)

    # get merchant details for the user
    merchant_details = access_ninja.get_merchant_details_for_user(user_id)

    # log user session
    session_insert_query = text(""" 
        insert into user_session (user_id, action, meta_status)
        values(:user_id, :action, 'active') 
    """)
    with db_engine.connect() as conn:
        result = conn.execute(session_insert_query, user_id=user_id, action='login').lastrowid

    response.headers['X-Access-Token'] = access_token
    response.headers['X-User-ID'] = user_id

    response_body = {
        'username': username,
        'role_id': role_id,
        'role_name': role_name,
        'user_details': {
            'user_id': user_id,
            'first_name': first_names_en,
            'last_name': last_name_en,
            'phone_verified_p': phone_verified_p,
        },
        'merchant': merchant_details,
        'action_name': 'social_media_login',
        'status': 'successful'
    }

    response.data = json.dumps(response_body, default=str)
    return response

@access_management_blueprint.route('/contact-us', methods=['POST'])
def contact_us():
    request_body = request.json
    response = Response(content_type='application/json')

    first_name_en = request_body.get("first_name_en")
    last_name_en = request_body.get("last_name_en")
    phone_nr = request_body.get("phone_nr")
    email = request_body["email"]
    company_name = request_body.get("company_name")
    message = request_body.get("message")
    source_of_contact = request_body.get("source_of_contact")

    db_engine = jqutils.get_db_engine()

    query = text("""
        SELECT contact_us_id, retry_count
        FROM contact_us
        WHERE email = :email
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, email=email).fetchone()

    if result and result['retry_count'] >= 3:
        response_body = {
            'action': 'contact_us',
            'status': 'failed',
            'message': 'email already exists.'
        }
        response.data = json.dumps(response_body)
        return response
    else:
        # Increment the retry count or initialize it to 1 if the record doesn't exist
        retry_count = result['retry_count'] + 1 if result else 1

        if result:
            # Update the existing record with all fields and the updated retry count
            query = text("""
                UPDATE contact_us
                SET first_name_en = :first_name_en,
                    last_name_en = :last_name_en,
                    phone_nr = :phone_nr,
                    company_name = :company_name,
                    message = :message,
                    source_of_contact = :source_of_contact,
                    retry_count = :retry_count
                WHERE contact_us_id = :contact_us_id
            """)
            with db_engine.connect() as conn:
                conn.execute(query, first_name_en=first_name_en, last_name_en=last_name_en, phone_nr=phone_nr, company_name=company_name,
                            message=message, source_of_contact=source_of_contact, retry_count=retry_count, contact_us_id=result['contact_us_id'])
        else:
            # Insert a new record with all fields and the retry count
            query = text("""
                INSERT INTO contact_us (first_name_en, last_name_en, phone_nr, email, company_name, message, source_of_contact, meta_status, retry_count)
                VALUES(:first_name_en, :last_name_en, :phone_nr, :email, :company_name, :message, :source_of_contact, :meta_status, :retry_count)
            """)
            with db_engine.connect() as conn:
                contact_us_id = conn.execute(query, first_name_en=first_name_en, last_name_en=last_name_en, phone_nr=phone_nr, email=email, company_name=company_name, message=message,
                                             source_of_contact=source_of_contact, meta_status='active', retry_count=retry_count).lastrowid
                assert contact_us_id, "contact us insert error"

    # if os.getenv("ENV") == "production":
    aws_utils.publish_email(
        source="noreply@iblinknext.com",
        destination={
            "ToAddresses": ["haseeb.ahmed@iblinknext.com"],
        },
        subject=f"Iblinkpay Website Form {first_name_en} {last_name_en}",
        text=f"""
        Full Name: {first_name_en} {last_name_en}
        Phone Number: {phone_nr} 
        email: {email}
        Company Name: {company_name}, has reached out for details""",
        html=f"""
        Full Name: {first_name_en} {last_name_en}
        Phone Number: {phone_nr}
        email: {email}
        Company Name: {company_name}, has reached out for details"""
    )
    
    response_body = {
        'action': 'contact_us',
        'status': 'successful'
    }
    response.data = json.dumps(response_body, default=str)
    return response