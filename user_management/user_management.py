from dateutil.relativedelta import relativedelta
from datetime import datetime
import logging
import json
import re
import uuid
import os
import requests

from flask import request, Response, g
from sqlalchemy.sql import text
from flask import Blueprint

from utils import jqutils, jqsecurity, jqaccess_control_engine, my_utils, aws_utils
from data_migration_management.data_migration_manager import DataMigrationManager
from user_management import user_ninja
from feature_management import feature_ninja
from facility_management import facility_ninja

logger = logging.getLogger(__name__)
user_management_blueprint = Blueprint('user_management_blueprint', __name__)

@user_management_blueprint.route('/financial-credentials', methods = ['GET'])
def get_financial_credentials():
    access_token, user_id = user_ninja.get_third_party_access_token('financials', g.merchant_id)

    response = Response(content_type='application/json')
    response_body = {
        'data': {
            'access_token': access_token,
            'user_id': user_id
        },
        'action': 'get_financial_credentials',
        'status': 'successful'
    }
    response.data = json.dumps(response_body)
    return response

############################
# GET CURRENT USER BEGIN
############################
@user_management_blueprint.route('/current-user', methods = ['GET'])
def get_current_user():  
    # request_body = request.get_json()
    request_header = request.headers

    user_id = request_header['X-User-ID']
    access_token = request_header['X-Access-Token']

    db_engine = jqutils.get_db_engine()

    # check if user is logged in
    query = text("""
        SELECT us.action, us.action_timestamp
        FROM user_session us
        WHERE us.user_id = :user_id
        AND us.action <> :action
        ORDER BY us.action_timestamp DESC
    """)
    with db_engine.connect() as conn:
        session_result = conn.execute(query, user_id=user_id, action='logout').fetchone()
        assert session_result, "User is not logged-in!"

    # get user details
    query = text("""
        SELECT u.user_id, r.role_id, u.username, u.first_names_en, u.last_name_en, u.phone_nr, u.email, u.business_designation, u.completed_signup_p,
        u.token_expiry_timestamp, u.root_p, u.modification_timestamp, u.phone_verified_p, u.email_verified_p, u.verification_status, cn.country_alpha_2, cn.country_code,
        r.role_name, r.role_description, u.personal_access_code, u.meta_status, m.default_currency_id, c.currency_alpha_3, m.default_country_id, cn.country_alpha_3,
        m.merchant_id, m.merchant_type_id, m.merchant_name, m.merchant_code, m.merchant_email, m.merchant_website_url, m.merchant_description,m.merchant_api_key,
        mi.merchant_image_bucket_name, mi.merchant_image_object_key, mt.merchant_type_name, m.financial_merchant_id, m.financial_organization_id,
        m.scheduled_order_prior_notification_duration, cn.default_timezone_offset_hour, u.all_facility_access_p, u.soft_login_required_p, m.merchant_group_id,
        mg.merchant_group_name, mba.merchant_billing_alert_id, mba.trial_start_date, mba.trial_end_date, mba.billing_start_date, mba.alert_type, mba.screen_alert_status,
        mba.account_suspend_p, m.billing_enabled_p, mba.override_alert_p, mba.billing_suspend_p
        FROM user u
        JOIN user_role_map ur on u.user_id = ur.user_id
        JOIN role r on r.role_id = ur.role_id
        LEFT JOIN user_merchant_map umm on umm.user_id = u.user_id
        LEFT JOIN merchant m on m.merchant_id = umm.merchant_id
        LEFT JOIN merchant_type mt on mt.merchant_type_id = m.merchant_type_id
        LEFT JOIN merchant_image mi on m.merchant_id = mi.merchant_id
        LEFT JOIN merchant_group mg on mg.merchant_group_id = m.merchant_group_id
        LEFT JOIN merchant_billing_alert mba on mba.merchant_id = m.merchant_id and mba.meta_status = :meta_status
        LEFT JOIN currency c on c.currency_id = m.default_currency_id
        LEFT JOIN country cn on cn.country_id = m.default_country_id
        WHERE u.user_id = :user_id and access_token = :access_token
        AND u.meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        user_result = conn.execute(query, user_id=user_id, access_token=access_token, meta_status='active').fetchone()
        assert user_result, "User not found!"

    merchant_sqs_queue_list = []
    query = text("""
        SELECT msqm.use_case, sq.sqs_queue_id, msqm.facility_id, sq.queue_name, sq.queue_description, sq.queue_arn
        FROM merchant_sqs_queue_map msqm
        JOIN sqs_queue sq on sq.sqs_queue_id = msqm.sqs_queue_id
        WHERE msqm.merchant_id = :merchant_id
        AND msqm.meta_status = :meta_status
        AND sq.meta_status = :meta_status
    """)
    db_engine = jqutils.get_db_engine()
    with db_engine.connect() as conn:
        merchant_sqs_queue_result = conn.execute(query, merchant_id=user_result['merchant_id'], meta_status='active').fetchall()

    if merchant_sqs_queue_result:
        merchant_sqs_queue_list = [dict(row) for row in merchant_sqs_queue_result]
    
    query = text("""
        SELECT mfm.feature_id, f.feature_name, mfm.enabled_p, mfm.billing_suspend_p, mfm.tags
        FROM merchant_feature_map mfm
        JOIN merchant m on m.merchant_id = mfm.merchant_id
        JOIN feature f on f.feature_id = mfm.feature_id
        WHERE m.merchant_id = :merchant_id
        AND m.merchant_group_id = :merchant_group_id
        AND mfm.meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        merchant_feature_result = conn.execute(query, merchant_id=user_result['merchant_id'], merchant_group_id=2, meta_status='active').fetchall()
        merchant_feature_list = [dict(row) for row in merchant_feature_result]

    for one_feature in merchant_feature_list:
        tags = one_feature['tags']
        if tags is None:
            tags = "{}"
        tags_dict = json.loads(tags)
        one_feature['tags'] = tags_dict

    station_result = None
    customer_result = None
    if user_result["role_name"] == "station":
        query = text("""
            SELECT usm.user_station_map_id, s.station_id, s.station_name, s.station_code, s.station_access_code, s.access_code_expiry_timestamp,
            s.preparation_station_p, s.dispatch_station_p
            FROM user_station_map usm
            JOIN station s on s.station_id = usm.station_id
            WHERE usm.user_id = :user_id
            AND usm.meta_status = :meta_status
            AND s.meta_status = :meta_status
        """)
        with db_engine.connect() as conn:
            station_result = conn.execute(query, user_id=user_id, meta_status='active').fetchone()
            assert station_result, "Station not found!"
    
    elif user_result["role_name"] == "customer":
        query = text("""
            SELECT ucm.customer_id, ucm.user_customer_map_id, cus.customer_code
            FROM user_customer_map ucm
            JOIN customer cus on cus.customer_id = ucm.customer_id
            WHERE ucm.user_id = :user_id
            AND ucm.meta_status = :meta_status
            AND cus.meta_status = :meta_status
        """)
        with db_engine.connect() as conn:
            customer_result = conn.execute(query, user_id=user_id, meta_status='active').fetchone()
            assert customer_result, "Customer not found!"

    # get user facility list
    if user_result["all_facility_access_p"]:
        query = text("""
            SELECT f.facility_id, f.facility_name, f.facility_code, f.merchant_id, f.city_id, c.city_name, f.country_id, cn.country_name,
            f.timezone, f.landline_phone_number, f.latitude, f.longitude, f.kitchen_display_system_enabled_p
            FROM facility f
            LEFT JOIN city c on c.city_id = f.city_id
            LEFT JOIN country cn on cn.country_id = f.country_id
            WHERE f.merchant_id = :merchant_id
            AND f.meta_status = :meta_status
        """)
        with db_engine.connect() as conn:
            facility_result = conn.execute(query, merchant_id=user_result['merchant_id'], meta_status='active').fetchall()
            facility_list = [dict(row) for row in facility_result]

    else:
        query = text("""
            SELECT f.facility_id, f.facility_name, f.facility_code, f.merchant_id, f.city_id, c.city_name, f.country_id, cn.country_name,
            f.timezone, f.landline_phone_number, f.latitude, f.longitude, f.kitchen_display_system_enabled_p
            FROM user_facility_map ufm
            JOIN facility f on f.facility_id = ufm.facility_id
            LEFT JOIN city c on c.city_id = f.city_id
            LEFT JOIN country cn on cn.country_id = f.country_id
            WHERE ufm.user_id = :user_id
            AND ufm.meta_status = :meta_status
        """)
        with db_engine.connect() as conn:
            facility_result = conn.execute(query, user_id=user_id, meta_status='active').fetchall()
            facility_list = [dict(row) for row in facility_result]

    facility_id_list = [facility['facility_id'] for facility in facility_list]

    if facility_id_list:
        query = text("""
            SELECT facility_config_id, facility_id
            FROM facility_config
            WHERE facility_id in :facility_id_list
            AND meta_status = :meta_status
        """)
        with db_engine.connect() as conn:
            facility_config_result = conn.execute(query, facility_id_list=facility_id_list, meta_status='active').fetchall()

        for facility in facility_list:
            facility['facility_config_p'] = False
            for facility_config in facility_config_result:
                if facility['facility_id'] == facility_config['facility_id']:
                    facility['facility_config_p'] = True
                    break

    user_facility_session = {}
    # get user facility session
    query = text("""
        SELECT ufss.facility_id, ufss.login_timestamp, ufss.logout_timestamp, f.facility_name
        FROM user_facility_soft_session ufss
        JOIN facility f on f.facility_id = ufss.facility_id
        WHERE ufss.user_id = :user_id
        AND ufss.meta_status = :meta_status
        ORDER BY ufss.login_timestamp DESC
    """)
    with db_engine.connect() as conn:
        user_facility_soft_session_result = conn.execute(query, user_id=user_id, meta_status='active').fetchone()

    if user_facility_soft_session_result:
        if user_facility_soft_session_result['logout_timestamp']:
            status = 'logged_out'
        else:
            status = 'logged_in'

        user_facility_session = {
            'facility_id': user_facility_soft_session_result['facility_id'],
            'facility_name': user_facility_soft_session_result['facility_name'],
            'login_timestamp': user_facility_soft_session_result['login_timestamp'],
            'logout_timestamp': user_facility_soft_session_result['logout_timestamp'],            
            'status': status
        }

    query = text("""
        SELECT emrm.merchant_role_id
        FROM (SELECT employee_id FROM employee WHERE user_id = :user_id) e
        JOIN employee_merchant_role_map emrm on emrm.employee_id = e.employee_id
        WHERE emrm.meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        employee_merchant_role_result = conn.execute(query, user_id=user_id, meta_status='active').fetchall()
        merchant_role_id_list = [merchant_role['merchant_role_id'] for merchant_role in employee_merchant_role_result]

    ############## GET Policies allowed for this user - START ######################
    merchant_role_policy_list = []
    if merchant_role_id_list:
        query = text("""
            SELECT p.policy_id, p.module_name, p.full_access_p, p.policy_name, p.policy_description
            FROM merchant_role_policy_map mrpm
            JOIN policy p on p.policy_id = mrpm.policy_id
            WHERE mrpm.merchant_role_id in :merchant_role_id_list
            AND mrpm.meta_status = :meta_status
            GROUP BY p.policy_id, p.module_name, p.full_access_p, p.policy_name, p.policy_description
            ORDER BY p.module_name, p.policy_id
        """)
        with db_engine.connect() as conn:
            policy_result = conn.execute(query, merchant_role_id_list=merchant_role_id_list, meta_status='active').fetchall()
            merchant_role_policy_list = [dict(row) for row in policy_result]    

    query = text("""
        SELECT p.policy_id, p.module_name, p.full_access_p, p.policy_name, p.policy_description
        FROM employee_policy_map epm
        JOIN policy p on p.policy_id = epm.policy_id
        WHERE epm.employee_id in (SELECT employee_id FROM employee WHERE user_id = :user_id)
        AND epm.meta_status = :meta_status
        GROUP BY p.policy_id, p.module_name, p.full_access_p, p.policy_name, p.policy_description
        ORDER BY p.module_name, p.policy_id
    """)
    with db_engine.connect() as conn:
        employee_policy_result = conn.execute(query, user_id=user_id, meta_status='active').fetchall()
        employee_policy_list = [dict(row) for row in employee_policy_result]
    merchant_role_policy_list.extend(employee_policy_list)

    query = text("""
        SELECT p.policy_id, p.module_name, p.full_access_p, p.policy_name, p.policy_description
        FROM user_policy_map upm
        JOIN policy p on p.policy_id = upm.policy_id
        WHERE upm.user_id = :user_id
        AND upm.meta_status = :meta_status
        GROUP BY p.policy_id, p.module_name, p.full_access_p, p.policy_name, p.policy_description
        ORDER BY p.module_name, p.policy_id
    """)
    with db_engine.connect() as conn:
        user_policy_result = conn.execute(query, user_id=user_id, meta_status='active').fetchall()
        user_policy_list = [dict(row) for row in user_policy_result]
    merchant_role_policy_list.extend(user_policy_list)

    query = text("""
        SELECT p.policy_id, p.module_name, p.full_access_p, p.policy_name, p.policy_description
        FROM role_policy_map rpm
        JOIN policy p on p.policy_id = rpm.policy_id
        WHERE rpm.role_id = :role_id
        AND rpm.meta_status = :meta_status
        GROUP BY p.policy_id, p.module_name, p.full_access_p, p.policy_name, p.policy_description
        ORDER BY p.module_name, p.policy_id
    """)
    with db_engine.connect() as conn:
        role_policy_result = conn.execute(query, role_id=user_result['role_id'], meta_status='active').fetchall()
        role_policy_list = [dict(row) for row in role_policy_result]
    merchant_role_policy_list.extend(role_policy_list)

    # distinct
    viewed_policy_id_list = set()
    policy_list = []
    for policy in merchant_role_policy_list:
        if policy['policy_id'] not in viewed_policy_id_list:
            viewed_policy_id_list.add(policy['policy_id'])
            policy_list.append(policy)    

    ############## GET Policies allowed for this user - END ######################
    ############## GET Unread Notification Count - START ######################
    query = text("""
        SELECT COUNT(1) as notification_unread_count
        FROM notification_recipient_map
        WHERE user_id = :user_id
        AND meta_status = :meta_status
        AND read_p = :read_p
    """)
    with db_engine.connect() as conn:
        notification_unread_count = conn.execute(query, user_id=user_id, meta_status='active', read_p=0).scalar()
    
    # Get overdue billing invoices
    oldest_invoice_due_date = None
    billing_enabled_p = user_result["billing_enabled_p"]
    
    if billing_enabled_p:
        pending_status_list = ['pending', 'overdue']
        
        query = text("""
            SELECT invoice_due_date
            FROM billing_invoice
            WHERE merchant_id = :merchant_id
            AND invoice_status IN :pending_status_list
            AND meta_status = :meta_status
            ORDER BY invoice_due_date ASC
        """)
        with db_engine.connect() as conn:
            pending_invoice_result = conn.execute(query, merchant_id=user_result['merchant_id'], pending_status_list=pending_status_list, meta_status='active').fetchone()
            if pending_invoice_result:
                oldest_invoice_due_date = pending_invoice_result['invoice_due_date']
            
        
    query = text("""
        SELECT e.employee_id, emrm.merchant_role_id, mr.merchant_role_name
        FROM employee e
        LEFT JOIN employee_merchant_role_map emrm on emrm.employee_id = e.employee_id
        LEFT JOIN merchant_role mr on mr.merchant_role_id = emrm.merchant_role_id
        WHERE e.user_id = :user_id
        AND e.meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        employee_result = conn.execute(query, user_id=user_id, meta_status='active').fetchone()
        employee_result = dict(employee_result) if employee_result else None
    if user_result:
        logo_url = None
        if (user_result["merchant_image_bucket_name"] and user_result["merchant_image_object_key"]):
            logo_url = jqutils.create_presigned_get_url(user_result["merchant_image_bucket_name"], user_result["merchant_image_object_key"], expiration=3600)

        merchant_api_key = user_result['merchant_api_key']
        if merchant_api_key is not None:
            merchant_api_key = jqaccess_control_engine.decrypt_password(merchant_api_key).decode()

        neighborhood_pulse_access_token, neighborhood_pulse_user_id = user_ninja.get_third_party_access_token('neighbourhood-pulse', user_result['merchant_id'])

        response_body = {
            'user': {
                'user_id': user_id,
                'username' : user_result['username'],
                'phone_nr': user_result['phone_nr'],
                'email' : user_result['email'],
                'business_designation': user_result['business_designation'],
                'first_names_en' : user_result['first_names_en'],
                'last_name_en' : user_result['last_name_en'],
                'token_expiry_timestamp' : user_result['token_expiry_timestamp'].__str__(),
                'completed_signup_p': user_result['completed_signup_p'],
                'root_p' : user_result['root_p'],
                'user_status' : user_result['meta_status'],
                'soft_login_required_p': user_result['soft_login_required_p'],
                'personal_access_code': user_result['personal_access_code'],
                'all_facility_access_p': user_result['all_facility_access_p']
            },
            'verification_status': {
                'phone_verified_p': user_result['phone_verified_p'],
                'email_verified_p': user_result['email_verified_p'],
                'verification_status': user_result['verification_status']
            },
            'merchant': {
                'merchant_id' : user_result['merchant_id'],
                'merchant_type': {
                    'merchant_type_id': user_result['merchant_type_id'],
                    "merchant_type_name": user_result['merchant_type_name'],
                },
                'merchant_group': {
                    'merchant_group_id': user_result['merchant_group_id'],
                    'merchant_group_name': user_result['merchant_group_name'],
                },
                'default_currency': {
                    'currency_id': user_result['default_currency_id'],
                    'currency_alpha_3': user_result['currency_alpha_3']
                },
                'default_country': {
                    'country_id': user_result['default_country_id'],
                    'country_alpha_2': user_result['country_alpha_2'],
                    'country_alpha_3': user_result['country_alpha_3'],
                    'country_code': user_result['country_code'],
                    'timezone': user_result['default_timezone_offset_hour']
                },
                'financials': {
                    'financial_merchant_id': user_result['financial_merchant_id'],
                    'financial_organization_id': user_result['financial_organization_id']
                },
                'merchant_billing_alert': {
                    'merchant_billing_alert_id': user_result['merchant_billing_alert_id'],
                    'trial_start_date': user_result['trial_start_date'],
                    'trial_end_date': user_result['trial_end_date'],
                    'billing_start_date': user_result['billing_start_date'],
                    'alert_type': user_result['alert_type'],
                    'screen_alert_status': user_result['screen_alert_status'],
                    'override_alert_p': user_result['override_alert_p'],
                    'billing_suspend_p': user_result['billing_suspend_p'],
                    'account_suspend_p': user_result['account_suspend_p'],
                    'oldest_invoice_due_date': oldest_invoice_due_date
                },
                'merchant_website_url' : user_result['merchant_website_url'],
                'merchant_code' : user_result['merchant_code'],
                'merchant_name' : user_result['merchant_name'],
                'merchant_email' : user_result['merchant_email'],
                'merchant_logo_url': logo_url,
                'merchant_description' : user_result['merchant_description'],
                'scheduled_order_prior_notification_duration': user_result['scheduled_order_prior_notification_duration'],
                'merchant_api_key' :  merchant_api_key,
                'merchant_sqs_queue_list': merchant_sqs_queue_list,
                'merchant_feature_list': merchant_feature_list
            },
            'neighborhood_pulse':{
                'access_token': neighborhood_pulse_access_token,
                'user_id': neighborhood_pulse_user_id
            },
            'role': {
                'role_id' : user_result['role_id'],
                'role_name' : user_result['role_name'],
                'role_description' : user_result['role_description'],
            },
            'policy_list': policy_list,
            'facility_list': facility_list,
            'user_facility_session': user_facility_session,
            'session_status' : session_result['action'],
            'notification_unread_count': notification_unread_count,
            'modification_timestamp' :  user_result['modification_timestamp'].__str__(),
            'action': 'get_current_user',
            'status': 'successful'
        }

        if station_result:
            response_body['station'] = {
                'station_id': station_result['station_id'],
                'station_name': station_result['station_name'],
                'station_code': station_result['station_code'],
                'station_access_code': station_result['station_access_code'],
                'access_code_expiry_timestamp': station_result['access_code_expiry_timestamp'].__str__(),
                'preparation_station_p': station_result['preparation_station_p'],
                'dispatch_station_p': station_result['dispatch_station_p']
            }
        elif customer_result:
            response_body['customer'] = {
                'user_customer_map_id': customer_result['user_customer_map_id'],
                'customer_id': customer_result['customer_id'],
                'customer_code': customer_result['customer_code']
            }
        if employee_result:
            response_body['employee'] = {
                'employee_id': employee_result['employee_id'],
                'merchant_role_id': employee_result['merchant_role_id'],
                'merchant_role_name': employee_result['merchant_role_name']
            }
    else:
        response_body = {
            'user_id': user_id,
            'action': 'get_current_user',
            'status': 'failed'
        }
    response = Response(content_type='application/json')
    response.data = json.dumps(response_body, default=str)
    return response

############################
# GET CURRENT USER END
############################

##########################
# ADD A USER
##########################
@user_management_blueprint.route('/user', methods=['POST'])
def add_user():
    logger.debug('SERVER SIDE: IN user POST METHOD')

    request_body = request.json
    response = Response(content_type='application/json')

    username = request_body['username']
    email = request_body['email']
    business_designation = request_body['business_designation']
    first_names_en = jqutils.cleanse_for_db(request_body['first_names_en'])
    last_name_en = jqutils.cleanse_for_db(request_body['last_name_en'])
    first_names_ar = request_body['first_names_ar']
    last_name_ar = request_body['last_name_ar']
    phone_nr = request_body['phone_nr']
    password = request_body['password']
    personal_access_code = request_body['personal_access_code'] if 'personal_access_code' in request_body else ""
    root_p = request_body['root_p']
    role_id = request_body['role_id']
    merchant_id = request_body['merchant_id'] if "merchant_id" in request_body else None
    request_otp = request_body['request_otp'] if "request_otp" in request_body else False
    completed_signup_p = request_body['completed_signup_p'] if "completed_signup_p" in request_body else False
    facility_id_list= request_body['facility_id_list']
    all_facility_access_p = int(request_body['all_facility_access_p']) if "all_facility_access_p" in request_body else 0
    soft_login_required_p = request_body['soft_login_required_p'] if "soft_login_required_p" in request_body else 0
    phone_verified_p = False
    email_verified_p = False
    verification_status = "pending"
    
    # mark user as phone_verified_p if request_otp is False
    if request_otp == False:
        phone_verified_p = True
        email_verified_p = True
        verification_status = "verified"

    meta_status = 'active'
    creation_user_id = g.user_id
    system_user_p = request_body.get('system_user_p', False)
    tenant_id = request_body.get('tenant_id', 1)

    if role_id:
        assert jqutils.check_record_by_id(role_id , 'role'), f"role_id is invalid"

    one_user = {
        "username": username,
        "email": email,
        "password": password,
        "completed_signup_p": completed_signup_p,
        "business_designation": business_designation,
        "first_names_en": first_names_en,
        "last_name_en": last_name_en,
        "first_names_ar": first_names_ar,
        "last_name_ar": last_name_ar,
        "phone_nr": phone_nr,
        "soft_login_required_p": soft_login_required_p,
        "personal_access_code": personal_access_code,
        "root_p": root_p,
        "phone_verified_p": phone_verified_p,
        "email_verified_p": email_verified_p,
        "verification_status": verification_status,
        "all_facility_access_p": all_facility_access_p,
        "meta_status": meta_status,
        "system_user_p": system_user_p,
        "creation_user_id": creation_user_id,
        "tenant_id": tenant_id
    }
    user_id, message = user_ninja.create_user(one_user, creation_user_id, tenant_id, role_id=role_id, merchant_id=merchant_id, facility_id_list=facility_id_list)

    if not user_id:
        response_body = {
            'action': 'add_user',
            'status': 'failed',
            'message': message
        }
    else:
        response_body = {
            'user_id': user_id,
            'action': 'add_user',
            'status': 'successful'
        }
    response.data = json.dumps(response_body)
    return response

@user_management_blueprint.route('/username-availability', methods = ['POST'])
def check_username_availability():

    request_body = request.json
    username = request_body["username"]

    username = username.lower()
    username_invalid = False
    # check if username contains special characters except underscore, hyphen and dot
    if not re.match(r'^[a-zA-Z0-9_.-]+$', username):
        username_invalid = True
    
    if not username_invalid:

        db_engine = jqutils.get_db_engine()

        query = text("""
            SELECT username
            FROM user
            WHERE username = :username AND
            meta_status = 'active'
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, username=username).fetchone()
        
        available_p = False if result else True
    
    response = Response(content_type='application/json')
    
    if username_invalid:
        response_body = {
            'action': 'check_username_availability',
            'status': 'failed',
            'error': 'username contains invalid characters'
        }
    else:
        response_body = {
            'username': username,
            'available_p': available_p,
            'action': 'check_username_availability',
            'status': 'successful',
        }
    response.data = json.dumps(response_body, default=str)
    return response

@user_management_blueprint.route('/user-credentials', methods = ['PUT'])
def update_user_credentials():
    request_body = request.json

    user_id = request_body["user_id"]
    email = request_body["email"]
    username = request_body["username"]
    password = request_body["password"]
    password_bytes = password.encode()

    assert g.user_id == int(user_id), "access denied"

    username = username.lower()
    username_invalid = False
    # check if username contains special characters except underscore, hyphen and dot
    if not re.match(r'^[a-zA-Z0-9_.-]+$', username):
        username_invalid = True
    
    if not username_invalid:
        db_engine = jqutils.get_db_engine()

        query = text("""
            SELECT user_id, phone_verified_p, email_verified_p
            FROM user
            WHERE user_id = :user_id
            AND meta_status = :meta_status
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, user_id=user_id, meta_status='active').fetchone()
            assert result, f"no valid user found for user_id: {user_id}"

        phone_verified_p = result["phone_verified_p"] if result["phone_verified_p"] else 0
        email_verified_p = result["email_verified_p"] if result["email_verified_p"] else 0

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
        
        cipher_text_bytes = jqsecurity.encrypt_bytes_symmetric_to_bytes(password_bytes, key_string_db_bytes)

        query = text("""
            UPDATE user
            SET username = :username, email = :email, password = :password
            WHERE user_id = :user_id
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, username=username, email=email, password=cipher_text_bytes, user_id=user_id).rowcount
            assert result, f"failed to update user credentials for user_id: {user_id}"
        
        # Check if merchant already assigned to the user (aka signed up via invite)
        merchant_id = None
        verification_status = "pending"
        query = text("""
            SELECT merchant_id
            FROM user_merchant_map 
            WHERE user_id = :user_id
            AND meta_status = :meta_status
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, user_id=user_id, meta_status='active').fetchone()

            if result:
                merchant_id = result['merchant_id']

                # update user and merchant verification_statuses to under-review
                verification_status = "under-review"

                query = text("""
                    UPDATE user SET verification_status = :verification_status
                    WHERE user_id = :user_id
                    AND meta_status = :meta_status
                """)
                with db_engine.connect() as conn:
                    result = conn.execute(query, user_id=user_id, verification_status=verification_status, meta_status='active').rowcount
                    assert result, "unable to update user verification status"
                    
    my_utils.publish_tech_support_message(f"Username: {username} has started his verification process.", "update-user-credentials", user_id=user_id)
    
    response = Response(content_type='application/json')

    if username_invalid:
        response_body = {
            'action': 'update_user_credentials',
            'status': 'failed',
            'error': 'username_invalid'
        }
    else:
        response_body = {
            'user_id': user_id,
            'merchant_id': merchant_id,
            'verification_status': {
                'verification_status': verification_status,
                'phone_verified_p': phone_verified_p,
                'email_verified_p': email_verified_p
            },
            'action': 'update_user_credentials',
            'status': 'successful'
        }
    response.data = json.dumps(response_body, default=str)
    return response

@user_management_blueprint.route('/forgot-password', methods = ['POST'])
def initiate_forgot_password_request():
    request_body = request.json
    response = Response(content_type='application/json')
    
    username = request_body["username"]
    email = request_body["email"]

    db_engine = jqutils.get_db_engine()
    
    # check if user exists and their password is set
    query = text("""
        SELECT user_id, username, password, email
        FROM user
        WHERE username = :username
        OR email = :email
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
        response.data = json.dumps(response_body, default=str)
        return response
    
    user_id = result["user_id"]
    username = result["username"]
    encoded_password = result["password"]
    email = result["email"]
    contact_method = "email"

    if encoded_password is None:
        response_body = {
            "message": "Password not set for user. Try soft-login.",
            "action": "initiate_forgot_password_request",
            "status": "failed",
        }
        response.data = json.dumps(response_body, default=str)
        return response
    
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
                "user_id": user_id,
                "contact_method": contact_method,
                "action": "initiate_forgot_password_request",
                "status": "successful",
            }
            response.data = json.dumps(response_body, default=str)
            return response

    # create OTP request for user
    otp = str(uuid.uuid4())
    intent = "forgot_password"
    otp_request_count = 0
    otp_requested_timestamp = datetime.now()
    otp_status = "pending"

    query = text("""
        INSERT INTO one_time_password (user_id, otp, intent, contact_method, otp_request_count, otp_requested_timestamp, otp_status, meta_status)
        VALUES(:user_id, :otp, :intent, :contact_method, :otp_request_count, :otp_requested_timestamp, :otp_status, :meta_status)
    """)
    with db_engine.connect() as conn:
        one_time_password_id = conn.execute(query, user_id=user_id, otp=otp, intent=intent, contact_method=contact_method, otp_request_count=otp_request_count,
                                otp_requested_timestamp=otp_requested_timestamp, otp_status=otp_status, meta_status='active').lastrowid
        assert one_time_password_id, "otp request insert error"
    
    # generate reset password link
    fe_base_url = os.getenv("FE_PAYMENT_WEB_URL")
    reset_password_link = fe_base_url + "/reset-password/" + otp

    # send otp
    if os.getenv("MOCK_AWS_NOTIFICATIONS") != "1":
        if contact_method == 'email':
            aws_utils.publish_email(
                source="noreply@iblinknext.com",
                destination={
                    "ToAddresses": [email],
                },
            subject=f"Forgot Password",
                text=f"Hi,\n\nYou can reset your password by opening this link: {reset_password_link}\n\nRegards,\niBlinkPay Team",
                html=f"Hi,\n\nYou can reset your password by opening this link: {reset_password_link}\n\nRegards,\niBlinkPay Team"
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
        "user_id": user_id,
        "contact_method": contact_method,
        "action": "initiate_forgot_password_request",
        "status": "successful",
    }
    response.data = json.dumps(response_body, default=str)
    return response

@user_management_blueprint.route('/forgot-password/<otp>', methods = ['GET'])
def get_forgot_password_request(otp):
    db_engine = jqutils.get_db_engine()
    response = Response(content_type='application/json')
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
            "message": "OTP not valid or already processed",
            "action": "get_forgot_password_request",
            "status": "failed",
        }
        response.data = json.dumps(response_body, default=str)
        return response
    
    otp_status = result["otp_status"]

    if otp_status != "sent":
        response_body = {
            "message": "OTP not valid or already processed",
            "action": "get_forgot_password_request",
            "status": "failed",
        }
        response.data = json.dumps(response_body, default=str)
        return response
    
    response_body = {
        "otp_status": otp_status,
        "action": "get_forgot_password_request",
        "status": "successful",
    }
    response.data = json.dumps(response_body, default=str)
    return response

@user_management_blueprint.route('/reset-password', methods = ['POST'])
def reset_user_password():
    request_body = request.json
    response = Response(content_type='application/json')

    otp = request_body["otp"]
    password = request_body["password"]
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
            "message": "OTP not valid or already processed",
            "action": "reset_user_password",
            "status": "failed",
        }
        response.data = json.dumps(response_body, default=str)
        return response

    # encrypt password and update user
    password_manager = DataMigrationManager()
    encrypted_password = password_manager.encrypt_password(password)

    query = text("""
        UPDATE user
        SET password = :password
        WHERE user_id = :user_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, password=encrypted_password, user_id=user_id, meta_status='active').rowcount
        assert result, "password update error"
    
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
    
    response_body = {
        "user_id": user_id,
        "action": "reset_user_password",
        "status": "successful",
    }
    response.data = json.dumps(response_body, default=str)
    return response

@user_management_blueprint.route('/user/<user_id>/details', methods=['PUT'])
def update_user_details(user_id):
    request_body = request.json

    first_names_en = request_body['first_names_en']
    last_name_en = request_body['last_name_en']
    phone_nr = request_body['phone_nr']
    business_designation = request_body['business_designation']

    db_engine = jqutils.get_db_engine()

    query = text("""
        UPDATE user
        SET first_names_en = :first_names_en, last_name_en = :last_name_en, phone_nr = :phone_nr,
        business_designation = :business_designation
        WHERE user_id = :user_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, first_names_en=first_names_en, last_name_en=last_name_en, phone_nr=phone_nr,
                    business_designation=business_designation, user_id=user_id, meta_status='active').rowcount
        assert result, "user_id not found"

    response = Response(content_type='application/json')
    response_body = {
        'action': 'update_user_details',
        'status': 'successful'
    }
    response.data = json.dumps(response_body, default=str)
    return response

@user_management_blueprint.route('/user/<user_id>/merchant', methods=['PUT'])
def update_merchant_details(user_id):
    request_body = request.json

    brand_name = request_body['brand_name'].strip().lower()
    merchant_name = request_body['merchant_name'].strip().lower()
    merchant_address_line_1 = request_body['merchant_address_line_1'].strip().lower()
    merchant_address_line_2 = request_body['merchant_address_line_2'].strip().lower() if request_body['merchant_address_line_2'] else None
    area_name = request_body['area_name'].strip().lower()
    city_id = request_body['city_id']
    country_id = request_body['country_id']
    merchant_group_id = request_body['merchant_group_id'] if 'merchant_group_id' in request_body else None

    facility_name_list = request_body['facility_name_list']
    creation_user_id = g.user_id

    try:
        timezone = jqutils.get_column_by_id(country_id, 'timezone', 'country')
    except:
        timezone = 4 # dubai timezone as default

    db_engine = jqutils.get_db_engine()

    query = text("""
        select symmetric_key 
        from payment_api_secret
        where description = 'password-protector-key' and meta_status = 'active'
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query).fetchone()
        assert result, "Failed to get password protector key"

        key_string_db = result['symmetric_key']
        key_string_db_bytes = key_string_db.encode()

    query = text("""
        SELECT m.merchant_id, m.merchant_api_key
        FROM merchant m
        JOIN user_merchant_map umm ON umm.merchant_id = m.merchant_id
        WHERE umm.user_id = :user_id
        AND umm.meta_status = :meta_status
        AND m.meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, user_id=user_id, meta_status='active').fetchone()

    if result:
        merchant_id = result['merchant_id']
        encrypted_merchant_api_key = result['merchant_api_key']
        unencrypted_merchant_api_key = jqaccess_control_engine.decrypt_password(encrypted_merchant_api_key).decode()

        query = text("""
            UPDATE merchant
            SET merchant_name = :merchant_name, merchant_address_line_1 = :merchant_address_line_1,
            merchant_address_line_2 = :merchant_address_line_2, area_name = :area_name, city_id = :city_id,
            default_country_id = :default_country_id
            WHERE merchant_id = :merchant_id
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, merchant_name=merchant_name, merchant_address_line_1=merchant_address_line_1,
                        merchant_address_line_2=merchant_address_line_2, area_name=area_name, city_id=city_id,
                        default_country_id=country_id, merchant_id=merchant_id).rowcount
            assert result, "merchant_id not found"

        # ASSUMPTION: merchant can only have 1 brand
        query = text("""
            UPDATE brand
            SET brand_name = :brand_name
            WHERE merchant_id = :merchant_id
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, brand_name=brand_name, merchant_id=merchant_id).rowcount
            assert result, "merchant_id not found"

        query = text("""
            SELECT facility_id, facility_name
            FROM facility
            WHERE merchant_id = :merchant_id
        """)
        with db_engine.connect() as conn:
            results = conn.execute(query, merchant_id=merchant_id).fetchall()

            to_add = []
            to_delete = []
            for one_facility in results:
                cand_facility_name = one_facility['facility_name'].strip().lower()
                if cand_facility_name not in facility_name_list:
                    to_delete.append(one_facility['facility_id'])

            for one_facility in facility_name_list:
                if one_facility.strip().lower() not in [x['facility_name'].strip().lower() for x in results]:
                    to_add.append(one_facility)

        # create facility
        for facility_name in to_add:
            facility_name = facility_name.strip().lower()
            facility_code = jqutils.create_code_from_title(facility_name, 4)

            facility_ninja.create_facility(facility_name, facility_code, merchant_id, timezone, city_id, country_id, creation_user_id, tenant_id=1)

        # check if neighborhood pulse credentials already exist
        query = text("""
            SELECT username
            FROM merchant_third_party_credential
            WHERE third_party_credential_type = :third_party_credential_type
            AND merchant_id = :merchant_id
            AND meta_status = :meta_status
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, third_party_credential_type='neighbourhood-pulse', merchant_id=merchant_id, meta_status='active').fetchone()

        if not result:
            user_ninja.create_neighborhood_pulse_credentials(user_id, merchant_id, merchant_name, key_string_db_bytes)
    else:
        merchant_type_id = 1
        merchant_code = jqutils.create_code_from_title(merchant_name, 4)
        unencrypted_merchant_api_key = jqutils.get_random_alphanumeric(24)
        encrypted_merchant_api_key = jqsecurity.encrypt_bytes_symmetric_to_bytes(unencrypted_merchant_api_key.encode(), key_string_db_bytes)
        
        if country_id:
            default_currency_id = jqutils.get_id_by_name(str(country_id), "country_id", "currency")
        else:
            default_currency_id = None

        query = text("""
            INSERT INTO merchant (merchant_name, merchant_code, merchant_type_id, merchant_address_line_1, merchant_address_line_2, area_name,
                city_id, default_currency_id, default_country_id, merchant_api_key, merchant_group_id, meta_status)
            VALUES (:merchant_name, :merchant_code, :merchant_type_id, :merchant_address_line_1, :merchant_address_line_2, :area_name,
                :city_id, :default_currency_id, :default_country_id, :merchant_api_key, :merchant_group_id, :meta_status)
        """)
        with db_engine.connect() as conn:
            merchant_id = conn.execute(query, merchant_name=merchant_name, merchant_address_line_1=merchant_address_line_1, merchant_address_line_2=merchant_address_line_2,
                            area_name=area_name, merchant_code=merchant_code, merchant_api_key=encrypted_merchant_api_key, merchant_type_id=merchant_type_id, city_id=city_id,
                            default_currency_id=default_currency_id, default_country_id=country_id, merchant_group_id=merchant_group_id, meta_status='active').lastrowid

        # map user_id to merchant
        query = text("""
            INSERT INTO user_merchant_map(user_id, merchant_id, meta_status)
            VALUES (:user_id, :merchant_id, :meta_status)
        """)
        with db_engine.connect() as conn:
            user_merchant_map_id = conn.execute(query, user_id=user_id, merchant_id=merchant_id, meta_status='active').lastrowid
            assert user_merchant_map_id, "unable to add user_merchant_map"

        # Set default merchant features and disable all of them
        query = text("""
            SELECT feature_id, feature_name, merchant_default_p
            FROM feature
            WHERE meta_status = :meta_status
        """)
        with db_engine.connect() as conn:
            results = conn.execute(query, meta_status='active').fetchall()
            assert results, "Failed to get feature ids"
        
        # create brand
        query = text("""
            INSERT INTO brand(brand_name, brand_code, merchant_id, meta_status)
            VALUES (:brand_name, :brand_code, :merchant_id, :meta_status)
        """)
        with db_engine.connect() as conn:
            brand_code = jqutils.create_code_from_title(brand_name, 4)
            brand_id = conn.execute(query, brand_name=brand_name, brand_code=brand_code, merchant_id=merchant_id,
                        meta_status='active').lastrowid
            assert brand_id, "unable to add brand"

        # create facility
        for facility_name in facility_name_list:
            facility_name = facility_name.strip().lower()
            facility_code = jqutils.create_code_from_title(facility_name, 4)
            
            facility_ninja.create_facility(facility_name, facility_code, merchant_id, timezone, city_id, country_id, creation_user_id, tenant_id=1)
            
        # create neighborhood pulse credentials
        user_ninja.create_neighborhood_pulse_credentials(user_id, merchant_id, merchant_name, key_string_db_bytes)

        for result in results:
            feature_id = result['feature_id']
            enabled_p = result['merchant_default_p'] if result['merchant_default_p'] else 0
            feature_name = result['feature_name']

            query = text("""
                INSERT INTO merchant_feature_map (merchant_id, feature_id, enabled_p, meta_status, creation_user_id, tenant_id)
                VALUES (:merchant_id, :feature_id, :enabled_p, :meta_status, :creation_user_id, :tenant_id)
            """)
            with db_engine.connect() as conn:
                merchant_feature_map_id = conn.execute(query, merchant_id=merchant_id, feature_id=feature_id, enabled_p=enabled_p, meta_status='active', creation_user_id=g.user_id, tenant_id=g.tenant_id).lastrowid
                assert merchant_feature_map_id, "unable to create new merchant feature"

            old_enabled_p = 0
            new_enabled_p = enabled_p
            params = {
                "merchant_id": merchant_id,
                "user_id": user_id
            }
            success_p, message = feature_ninja.handle_feature_specific_setup(feature_name, old_enabled_p, new_enabled_p, params)

    response = Response(content_type='application/json')
    response_body = {
        'data': {
            'merchant_id': merchant_id,
            'merchant_api_key': unencrypted_merchant_api_key,
        },
        'action': 'update_merchant_details',
        'status': 'successful'
    }
    response.data = json.dumps(response_body, default=str)
    return response

@user_management_blueprint.route('/user/<user_id>/signup', methods=['PUT'])
def mark_signup_completed(user_id):
    request_body = request.json

    completed_signup_p = request_body['completed_signup_p']

    db_engine = jqutils.get_db_engine()

    query = text("""
        UPDATE user
        SET completed_signup_p = :completed_signup_p
        WHERE user_id = :user_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, completed_signup_p=completed_signup_p, user_id=user_id, meta_status='active').rowcount
        assert result, "user_id not found"

    response = Response(content_type='application/json')
    response_body = {
        'action': 'mark_signup_completed',
        'status': 'successful'
    }
    response.data = json.dumps(response_body, default=str)
    return response

@user_management_blueprint.route('/user/<user_id>/facility', methods=['POST'])
def add_facility_to_user(user_id):
    request_body = request.json

    facility_id_list = request_body['facility_id_list']

    db_engine = jqutils.get_db_engine()

    query=text("""
        select facility_id, meta_status
        from user_facility_map
        where user_id = :user_id
    """)
    with db_engine.connect() as conn:
        results = conn.execute(query,user_id=user_id).fetchall()
        results = [dict(row) for row in results]
        
    #Update table if added facility exists but is not active
    user_facility_map_id_count = 0
    facility_id_list_active=[]
    for one_result in results:
        facility_id = one_result["facility_id"]
        meta_status = one_result["meta_status"]

        if meta_status != 'active' and facility_id in facility_id_list:
            query = text("""
                Update user_facility_map
                set meta_status = :meta_status
                where user_id = :user_id
                and facility_id = :facility_id
            """)
            with db_engine.connect() as conn:
                result = conn.execute(query, user_id=user_id, facility_id=facility_id, meta_status='active').rowcount
            user_facility_map_id_count = user_facility_map_id_count+1
        facility_id_list_active.append(facility_id)
   
    for facility_id in facility_id_list:
        if facility_id in facility_id_list_active:
            continue
        query = text("""
            insert into user_facility_map (user_id, facility_id, meta_status, creation_user_id)
            values (:user_id, :facility_id, :meta_status, :created_by)
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, user_id=user_id, facility_id=facility_id, meta_status='active', 
                                    created_by=g.user_id).lastrowid
        user_facility_map_id_count = user_facility_map_id_count+1 

    response = Response(content_type='application/json')
    if user_facility_map_id_count:

        response_body = {
            'facilities_added': user_facility_map_id_count,
            'action': 'add_facility_to_user',
            'status': 'successful'
        }
    else:
         response_body = {
            
            'action': 'add_facility_to_user',
            'status': 'failed'
        }   
    response.data = json.dumps(response_body, default=str)
    return response    

@user_management_blueprint.route('/user/facility', methods=['DELETE'])
def delete_user_facility():
    request_body = request.json

    user_id = request_body['user_id']
    facility_id = request_body['facility_id']

    db_engine = jqutils.get_db_engine()

    query = text("""
        UPDATE user_facility_map
        SET meta_status = :meta_status
        WHERE user_id = :user_id
        AND facility_id = :facility_id
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, meta_status='deleted', user_id=user_id, facility_id=facility_id).rowcount
        assert result, "user_id or facility_id not found"

    response = Response(content_type='application/json')
    response_body = {
        'action': 'delete_user_facility',
        'status': 'successful'
    }
    response.data = json.dumps(response_body, default=str)
    return response


@user_management_blueprint.route('/user/<user_id>/update-password', methods=['POST'])
def update_user_password(user_id):

    if g.user_id != int(user_id):
        assert False, "access denied"

    request_body = request.json
    old_password = request_body['old_password']
    new_password = request_body['new_password']

    db_engine = jqutils.get_db_engine()
    password_manager = DataMigrationManager()

    query = text("""
        SELECT u.user_id, u.password
        FROM user u
        JOIN user_role_map urm on urm.user_id = u.user_id
        JOIN role r on r.role_id = urm.role_id
        WHERE u.user_id = :user_id
        AND u.meta_status = :meta_status
        AND urm.meta_status = :meta_status
        AND r.meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, merchant_id=g.merchant_id, user_id=user_id, meta_status="active").fetchone()
        assert result, "user not found"

        db_password = password_manager.decrypt_password(result["password"].encode())

        # convert bytes to string
        db_password = db_password.decode()

        print(db_password, old_password)

        assert db_password == old_password, "old password is incorrect"

    # update password
    query = text("""
        UPDATE user
        SET password = :password
        WHERE user_id = :user_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, password=password_manager.encrypt_password(new_password), user_id=user_id, meta_status="active").rowcount
        assert result, "failed to update password"

    response = Response(content_type='application/json')
    response_body = {
        'action': 'update_user_password',
        'status': 'successful'
    }
    response.data = json.dumps(response_body, default=str)
    return response

@user_management_blueprint.route('/user/<user_id>', methods=['GET'])
def get_one_user(user_id):
    db_engine = jqutils.get_db_engine()
    
    query = text("""
        SELECT u.user_id, u.username, u.first_names_en, u.last_name_en, u.first_names_ar, u.last_name_ar, u.phone_nr, u.email,
                u.creation_user_id, all_facility_access_p, soft_login_required_p, personal_access_code
        FROM user u
        WHERE u.user_id = :user_id
        AND u.meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, user_id=user_id, meta_status='active').fetchone()
        assert result, "user_id not found"
        result = dict(result)
        
    query = text("""
        SELECT urm.role_id, r.role_name
        FROM user_role_map urm
        JOIN role r on r.role_id = urm.role_id
        WHERE urm.user_id = :user_id
        AND urm.meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        results = conn.execute(query, user_id=user_id, meta_status='active').fetchall()
        results = [dict(row) for row in results]
        result['roles'] = results
        
    query = text("""
        SELECT ufm.facility_id, f.facility_name
        FROM user_facility_map ufm
        JOIN facility f on f.facility_id = ufm.facility_id
        WHERE ufm.user_id = :user_id
        AND ufm.meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        results = conn.execute(query, user_id=user_id, meta_status='active').fetchall()
        results = [dict(row) for row in results]
        result['facility_list'] = results
        
    query = text("""
        SELECT umm.merchant_id, m.merchant_name
        FROM user_merchant_map umm
        JOIN merchant m on m.merchant_id = umm.merchant_id
        WHERE umm.user_id = :user_id
        AND umm.meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        merchant = conn.execute(query, user_id=user_id, meta_status='active').fetchone()
        merchant = dict(merchant)
        result['merchant'] = merchant
        
    user_id = result['creation_user_id']
    
    query = text("""
        SELECT u.user_id, u.first_names_en, u.last_name_en
        FROM user u
        WHERE u.user_id = :user_id
        AND u.meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        creation_user = conn.execute(query, user_id=user_id, meta_status='active').fetchone()
        creation_user = dict(creation_user)
        result['creation_user'] = creation_user
        
    response = Response(content_type='application/json')
    
    response_body = {
        'data': result,
        'action': 'get_one_user',
        'status': 'successful'
    }
    response.data = json.dumps(response_body, default=str)
    return response
    
@user_management_blueprint.route('/user/<user_id>', methods=['PUT'])
def update_user(user_id):
    
    request_body = request.json
    db_engine = jqutils.get_db_engine()
    
    username = request_body["username"] 
    first_names_en = request_body["first_names_en"]
    last_name_en = request_body["last_name_en"] 
    first_names_ar = request_body["first_names_ar"]
    last_name_ar = request_body["last_name_ar"] 
    phone_nr = request_body["phone_nr"]
    password = request_body["password"] if "password" in request_body else None
    email = request_body["email"]  
    role_id =  request_body["role_id"]
    facility_id_list = request_body["facility_id_list"]
    personal_access_code = request_body["personal_access_code"]
    all_facility_access_p = request_body["all_facility_access_p"]
    soft_login_required_p = request_body["soft_login_required_p"]
    password_query = ""
    if password:
        password_manager = DataMigrationManager()
        password = password_manager.encrypt_password(password)
        password_query = "password = :password,"
        
    query = text(f"""
        UPDATE user
        SET username = :username, 
        first_names_en = :first_names_en, 
        last_name_en = :last_name_en, 
        first_names_ar = :first_names_ar,
        last_name_ar = :last_name_ar,
        phone_nr = :phone_nr,
        {password_query}
        email = :email,
        personal_access_code = :personal_access_code,
        all_facility_access_p = :all_facility_access_p,
        soft_login_required_p = :soft_login_required_p
        WHERE user_id = :user_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, username=username, first_names_en=first_names_en, last_name_en=last_name_en, first_names_ar=first_names_ar,
                    last_name_ar=last_name_ar, phone_nr=phone_nr, password=password, email=email, personal_access_code=personal_access_code,
                    all_facility_access_p=all_facility_access_p, soft_login_required_p=soft_login_required_p, user_id=user_id, meta_status='active').rowcount
    
    query = text("""
        UPDATE user_role_map
        SET role_id = :role_id
        WHERE user_id = :user_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, role_id=role_id, user_id=user_id, meta_status='active').rowcount
        
    query = text("""
        SELECT facility_id
        FROM user_facility_map
        WHERE user_id = :user_id
    """)
    with db_engine.connect() as conn:
        results = conn.execute(query, user_id=user_id).fetchall()
        previous_facility_id_list = [row['facility_id'] for row in results]
    
    if not all_facility_access_p:
        saved_facility_id_list = []
        for facility_id in facility_id_list:
            saved_facility_id_list.append(facility_id)
            if facility_id in previous_facility_id_list:
                query = text("""
                    UPDATE user_facility_map
                    SET meta_status = :meta_status
                    WHERE user_id = :user_id
                    AND facility_id = :facility_id
                """)
                with db_engine.connect() as conn:
                    result = conn.execute(query, meta_status='active', user_id=user_id, facility_id=facility_id).rowcount
            else:
                query = text("""
                    INSERT INTO user_facility_map (user_id, facility_id, meta_status, creation_user_id)
                    VALUES (:user_id, :facility_id, :meta_status, :created_by)
                """)
                with db_engine.connect() as conn:
                    result = conn.execute(query, user_id=user_id, facility_id=facility_id, meta_status='active', 
                                            created_by=g.user_id).lastrowid
    
        delete_facility_id_list = list(set(previous_facility_id_list) - set(saved_facility_id_list))

        if delete_facility_id_list:
            query = text("""
                UPDATE user_facility_map
                SET meta_status = :meta_status
                WHERE user_id = :user_id
                AND facility_id NOT IN :facility_id_list
            """)
            with db_engine.connect() as conn:
                result = conn.execute(query, meta_status='deleted', user_id=user_id, facility_id_list=delete_facility_id_list).rowcount
        
    response = Response(content_type='application/json')
    
    response_body = {
        'data': {
            'user_id': user_id,
        },
        'action': 'update_user',
        'status': 'successful'
    }
    response.data = json.dumps(response_body, default=str)
    
    return response
    

@user_management_blueprint.route('/user/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    db_engine = jqutils.get_db_engine()
    
    query = text("""
        UPDATE user
        SET meta_status = :meta_status
        WHERE user_id = :user_id
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, meta_status='deleted', user_id=user_id).rowcount
        
    query = text("""
        UPDATE user_role_map
        SET meta_status = :meta_status
        WHERE user_id = :user_id
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, meta_status='deleted', user_id=user_id).rowcount
        
    query = text("""
        UPDATE user_facility_map
        SET meta_status = :meta_status
        WHERE user_id = :user_id
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, meta_status='deleted', user_id=user_id).rowcount
        
    query = text("""
        UPDATE user_merchant_map
        SET meta_status = :meta_status
        WHERE user_id = :user_id
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, meta_status='deleted', user_id=user_id).rowcount
        
    response = Response(content_type='application/json')
    
    response_body = {
        'data': {
            'user_id': user_id,
        },
        'action': 'delete_user',
        'status': 'successful'
    }
    response.data = json.dumps(response_body, default=str)
    
    return response

@user_management_blueprint.route('/user/<user_id>/organizations', methods=['GET'])
def get_user_organizations(user_id):

    organization_list = []
    if os.getenv("MOCK_FINANCIALS") == "0":

        merchant_id = g.merchant_id

        financial_user_id = jqutils.get_column_by_id(user_id, "financial_user_id", "user")
        access_token, external_user_id = user_ninja.get_third_party_access_token("financials", merchant_id, financial_user_id)

        # Headers for Financial
        financial_headers = {
            'X-Access-Token': access_token,
            'X-User-Id': external_user_id,
        }

        request_url = f"{os.getenv('FINANCIAL_SERVICE_BASE_URL')}/user/{external_user_id}/organizations"

        response = requests.get(request_url, headers=financial_headers)
        assert response.status_code == 200, f"Failed to get organizations from financials. {response.text}"
        response_body = response.json()
        
        organization_list = response_body['data']

    response = Response(content_type='application/json')
    
    response_body = {
        'data': organization_list,
        'action': 'get_user_organizations',
        'status': 'successful'
    }
    response.data = json.dumps(response_body, default=str)
    
    return response