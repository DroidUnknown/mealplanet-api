import datetime
import pytest
import json

from tests import test_login, test_user
from utils import jqutils
from sqlalchemy import text
from access_management import access_ninja
from data_migration_management.data_migration_manager import DataMigrationManager

base_api_url = "/api"

def do_get_current_user(client, access_token, user_id):
    """
    Get Current User
    """
    headers = {
        "X-Access-Token": access_token,
        "X-User-ID": user_id,
    }
    response = client.get(f'{base_api_url}/current-user', headers=headers)
    return response

def do_add_user(client, headers, data):
    """
    Add user
    """
    response = client.post(f'{base_api_url}/user', headers=headers, json=data)
    return response

def do_sign_up(client, data):
    """
    Signup using name and phone number
    """
    response = client.post(f'{base_api_url}/signup', json=data)
    return response

def do_verify_otp(client, data):
    """
    Verify user account using OTP
    """
    response = client.post(f'{base_api_url}/verify-otp', json=data)
    return response

def do_merchant_verification(client, headers, data):
    """
    Verify merchant account
    """
    response = client.post(f'{base_api_url}/merchant-verification', headers=headers, json=data)
    return response

def do_upload_merchant_document(client, headers, data):
    """
    Upload merchant document
    """
    response = client.post(f'{base_api_url}/merchant-document', headers=headers, data=data, content_type='multipart/form-data')
    return response

def do_request_otp(client, phone_nr, email, intent):
    """
    Request OTP SMS for user again
    """
    payload = {
        "phone_nr": phone_nr,
        "email": email,
        "intent": intent
    }

    response = client.post(f'{base_api_url}/request-otp', json=payload)
    return response

def do_check_username_availability(client, headers, username):
    """
    Check username availability
    """
    payload = {
        "username": username
    }

    response = client.post(f'{base_api_url}/username-availability', headers=headers, json=payload)
    return response

def do_update_user_credentials(client, headers, data):
    """
    Update user credentials for user account
    """
    response = client.put(f'{base_api_url}/user-credentials', headers=headers, json=data)
    return response

def do_initiate_forgot_password_request(client, data):
    """
    Initiate forgot password request
    """
    response = client.post(f'{base_api_url}/forgot-password', json=data)
    return response

def do_get_forgot_password_request(client, otp):
    """
    Get forgot password request
    """
    response = client.get(f'{base_api_url}/forgot-password/{otp}')
    return response

def do_reset_user_password(client, data):
    """
    Reset user password
    """
    response = client.post(f'{base_api_url}/reset-password', json=data)
    return response

def do_email_signup(client, email):
    """
    Signup using email
    """

    payload = {
        "email": email,
    }

    response = client.post(f'{base_api_url}/email-signup', json=payload)
    return response

def do_user_signup(client, phone_nr, name, invitation_code=None, password=None, role_name="merchant", merchant_code=None):
    
    db_engine = jqutils.get_db_engine()
    first_name = name.split(" ")[0]
    last_name = name.split(" ")[1]

    """
    Signup using phone number and name
    """
    payload = {
        "first_names_en": first_name,
        "last_name_en": last_name,
        "phone_nr": phone_nr,
        "password": password,
        "invitation_code": invitation_code,
        "merchant_code": merchant_code,
        "device_information": {
            "device_id": phone_nr,
            "device_name": "macbook pro",
            "app_version": "0.0.10",
        }
    }
    response = test_user.do_sign_up(client, payload)
    assert response.status_code == 200
    assert response.json['status'] == 'successful'
    assert response.json['action'] == 'signup'

    """
    Get OTP code from database
    Normally the user would receive OTP code on phone via SMS.
    """
    query = text("""
        SELECT otp.otp
        FROM one_time_password otp
        JOIN signup_request sr ON otp.signup_request_id = sr.signup_request_id
        WHERE sr.phone_nr = :phone_nr
        AND otp.contact_method = :contact_method
        AND sr.meta_status = :status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, phone_nr=phone_nr, contact_method='sms', status='active').fetchone()
        assert result, "failed to get otp_request"
        otp_code = result["otp"]
    
    merchant_id = None
    merchant_name = None
    
    """
    Get invitation details from database if applicable
    """
    if invitation_code:

        query = text("""
            SELECT i.recipient_role_id, r.role_name, m.merchant_id, m.merchant_code, m.merchant_name
            FROM invitation i
            JOIN role r ON r.role_id = i.recipient_role_id
            JOIN merchant m ON m.merchant_id = i.merchant_id
            JOIN merchant_type mt ON m.merchant_type_id = mt.merchant_type_id
            WHERE i.invitation_code = :invitation_code
            AND i.invitation_type = :invitation_type
            AND i.meta_status = :meta_status
            ORDER BY i.insertion_timestamp DESC
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, invitation_code=invitation_code, invitation_type='join-merchant', meta_status='active').fetchone()
            assert result, "failed to get invitation details"
            role_id = result["recipient_role_id"]
            role_name = result["role_name"]

            merchant_id = result["merchant_id"]
            merchant_code = result["merchant_code"]
            merchant_name = result["merchant_name"]
    
    else:
        role_id = jqutils.get_id_by_name(role_name, "role_name", "role")

        if merchant_code:
            query = text("""
                SELECT merchant_id, merchant_name
                FROM merchant
                WHERE merchant_code = :merchant_code
                AND meta_status = :meta_status
            """)
            with db_engine.connect() as conn:
                result = conn.execute(query, merchant_code=merchant_code, meta_status='active').fetchone()
                assert result, "failed to get merchant details"
                merchant_id = result["merchant_id"]
                merchant_name = result["merchant_name"]

    """
    Verify OTP code for signup for the first time
    """
    payload = {
        "phone_nr": phone_nr,
        "email": None,
        "otp": otp_code,
        "intent": f"{role_name}_signup"
    }
    response = test_user.do_verify_otp(client, payload)
    assert response.status_code == 200
    assert response.json['status'] == 'successful'
    assert response.json['action'] == 'verify_otp'

    """
    Since the intent was for signup, the user should be logged in as a role after verification
    """

    data = response.json['data']
    assert data["username"] == None if role_name == "merchant" else phone_nr
    assert data["user_details"]["user_id"] > 0
    assert data["user_details"]["first_name"] == first_name
    assert data["user_details"]["last_name"] == last_name
    assert data["user_details"]["phone_verified_p"] == True
    assert data["role_id"] == role_id
    assert data["role_name"] == role_name
    assert data["merchant"]["merchant_id"] == merchant_id
    assert data["merchant"]["merchant_code"] == merchant_code
    assert data["merchant"]["merchant_name"] == merchant_name
    
    assert response.headers["X-Access-Token"] != None
    assert int(response.headers["X-User-Id"]) > 0

    return int(response.headers["X-User-Id"]), response.headers["X-Access-Token"], otp_code

def do_update_user_details(client, headers, user_id, data):
    """
    Update user details
    """
    response = client.put(f'{base_api_url}/user/{user_id}/details', headers=headers, json=data)
    return response

def do_update_merchant_details(client, headers, user_id, data):
    """
    Update merchant details
    """
    response = client.put(f'{base_api_url}/user/{user_id}/merchant', headers=headers, json=data)
    return response

def do_social_media_login(client, data):
    """
    Attempt social media login
    """
    response = client.post(f'{base_api_url}/social-media-login', json=data)
    return response

def do_mark_signup_completed(client, headers, user_id, completed_signup_p):
    """
    Mark signup as completed
    """
    data = {
        "completed_signup_p": completed_signup_p
    }
    response = client.put(f'{base_api_url}/user/{user_id}/signup', headers=headers, json=data)
    return response

def do_contact_us(client, data):
    """
    Contact Us
    """
    response = client.post(f'{base_api_url}/contact-us', json=data)
    return response

def go_add_facility_to_user(client,headers,user_id,data):
    """
    Add facility to user
    """
    response = client.post(f'{base_api_url}/user/{user_id}/facility', headers=headers, json=data)
    return response

def do_delete_user_facility(client,headers,data):
    """
    Delete facility from user
    """
    response = client.delete(f'{base_api_url}/user/facility', headers=headers, json=data)
    return response

def do_update_user_password(client,headers,user_id,data):
    """
    Update user password
    """
    response = client.post(f'{base_api_url}user/{user_id}/update-password', headers=headers, json=data)
    return response

def do_get_user_organizations(client,headers,user_id):
    """
    Get user organizations
    """
    response = client.get(f'{base_api_url}/user/{user_id}/organizations', headers=headers)
    return response

###########
# FIXTURES
###########
@pytest.fixture(scope="module", autouse=True)
def unverified_user_header(client):
    """
    Create an unverified user and yeild header content for it
    """

    phone_nr = "+96112345679"
    full_name = "unverified user new"

    user_id, access_token, otp_code = do_user_signup(client, phone_nr, full_name)

    yield {
        "X-User-Id": user_id,
        "X-Access-Token": access_token,
        "X-Username": None
    }

###########
# TEST CASES
###########

def test_get_current_user(client):
    """
    Test get current user
    """
    response = test_login.do_login(client, 'admin', 'alburaaq424')
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'

    response = do_get_current_user(client, response.headers['X-Access-Token'], response.headers['X-User-ID'])
    assert response.status_code == 200
    j = response.json
    assert j["status"] == 'successful'

def test_add_user_successfully(client, headers):
    """
    Test add user successfully
    """

    data = {
        "username": "dummy username",
        "email": "dummy email",
        "business_designation": None,
        "first_names_en": "first_names_en",
        "last_name_en": "last_name_en",
        "first_names_ar": "first_names_ar",
        "last_name_ar": "last_name_ar",
        "phone_nr": "+9612341234",
        "password": "1234",
        "password_expiry_timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "access_token": "",
        "personal_access_code": "123456",
        "token_expiry_timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "root_p": True,
        "role_id": 2,
        "merchant_id": 1,
        "facility_id_list": [1,2,3]
    }
    
    response = do_add_user(client, headers, data)
    assert response.status_code == 200, "failed to add user"
    assert response.json['status'] == 'successful', "failed to add user"

def test_add_user_with_missing_params(client, headers):
    """
    Test add user with missing params
    """

    data = {
    }
    
    with pytest.raises(Exception):
        do_add_user(client, headers, data)

def test_signup_successfully(client):
    """
    Test successful sign up
    """

    payload = {
        "first_names_en": "john",
        "last_name_en": "doe",
        "phone_nr": "+96112345678",
        "device_information": {
            "device_id": "1234567890",
            "device_name": "iPhone 12",
            "app_version": "0.10.0",
        }
    }

    response = do_sign_up(client, payload)
    assert response.status_code == 200
    assert response.json['status'] == 'successful'
    assert response.json['action'] == 'signup'

def test_signup_if_already_existing(client):
    """
    Test sign up with phone number that already exists
    """

    payload = {
        "first_names_en": "john",
        "last_name_en": "doe",
        "phone_nr": "+96112345678",
        "device_information": {
            "device_id": "1234567890",
            "device_name": "iPhone 12",
            "app_version": "0.10.0",
        }
    }

    response = do_sign_up(client, payload)
    assert response.status_code == 200
    assert response.json['status'] == 'failed'
    assert response.json['action'] == 'signup'
    assert response.json['message'] == 'phone number already exists.'

def test_request_otp_successfully(client):
    """
    Test successful request of OTP
    """

    db_engine = jqutils.get_db_engine()

    # get timestamp 1 hour earlier than now
    otp_requested_timestamp = datetime.datetime.now() - datetime.timedelta(hours=1)
    otp_requested_timestamp_str = otp_requested_timestamp.strftime('%Y-%m-%d %H:%M:%S')

    phone_nr = '+96112345678'

    query = text("""
        UPDATE one_time_password otp
        JOIN signup_request sr ON sr.signup_request_id = otp.signup_request_id
        SET otp.otp_requested_timestamp = :otp_requested_timestamp
        WHERE sr.phone_nr = :phone_nr
        AND otp.contact_method = :contact_method
    """)
    with db_engine.connect() as conn:
        record_updated_p = conn.execute(query, otp_requested_timestamp=otp_requested_timestamp_str, phone_nr=phone_nr, contact_method='sms').rowcount
        assert record_updated_p, "failed to update otp_requested_timestamp"
    
    query = text("""
        SELECT otp.one_time_password_id, otp.otp_request_count, otp.otp_requested_timestamp
        FROM one_time_password otp
        JOIN signup_request sr ON otp.signup_request_id = sr.signup_request_id
        WHERE sr.phone_nr = :phone_nr
        AND otp.contact_method = :contact_method
        AND otp.meta_status = :meta_status
        AND sr.meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, phone_nr=phone_nr, contact_method='sms', meta_status='active').fetchone()
        assert result, "failed to get otp_request_count"
        one_time_password_id = result["one_time_password_id"]
        old_otp_request_count = result["otp_request_count"]
        old_otp_requested_timestamp = result["otp_requested_timestamp"]

    response = do_request_otp(client, phone_nr, None, intent="merchant_signup")
    assert response.status_code == 200
    assert response.json['status'] == 'successful'
    assert response.json['action'] == 'request_otp'

    query = text("""
        SELECT otp_request_count, otp_requested_timestamp
        FROM one_time_password
        WHERE one_time_password_id = :one_time_password_id
        AND contact_method = :contact_method
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, one_time_password_id=one_time_password_id,contact_method='sms',meta_status='active').fetchone()
        assert result, "failed to get otp_request_count"
        new_otp_request_count = result["otp_request_count"]
        new_otp_requested_timestamp = result["otp_requested_timestamp"]

        assert old_otp_request_count + 1 == new_otp_request_count, "failed to increment otp_request_count in db"
        assert old_otp_requested_timestamp != new_otp_requested_timestamp, f"failed to update otp_requested_timestamp in db"

def test_request_otp_debouncing(client):
    """
    Test request of OTP not being serviced in case it is done within 30 seconds of the last request
    """

    db_engine = jqutils.get_db_engine()

    # get timestamp for just now
    otp_requested_timestamp = datetime.datetime.now()
    otp_requested_timestamp_str = otp_requested_timestamp.strftime('%Y-%m-%d %H:%M:%S')
    phone_nr = '+96112345678'
    otp_status = 'sent'

    query = text("""
        UPDATE one_time_password otp
        JOIN signup_request sr ON sr.signup_request_id = otp.signup_request_id
        SET otp.otp_requested_timestamp = :otp_requested_timestamp,
        otp.otp_status = :otp_status
        WHERE sr.phone_nr = :phone_nr
    """)
    with db_engine.connect() as conn:
        record_updated_p = conn.execute(query, otp_requested_timestamp=otp_requested_timestamp_str, otp_status=otp_status, phone_nr=phone_nr).rowcount
        assert record_updated_p, "failed to update otp_requested_timestamp"
    
    response = do_request_otp(client, phone_nr, None, intent="merchant_signup")
    assert response.status_code == 200
    assert response.json['status'] == 'failed'
    assert response.json['action'] == 'request_otp'
    assert response.json['message'] == 'please wait 30 seconds before requesting another otp.'

def test_verify_wrong_otp(client):
    """
    Test otp validation with wrong OTP code
    """

    payload = {
        "phone_nr": "+96112345678",
        "email": None,
        "otp": "123456",
        "intent": "merchant_signup"
    }

    response = do_verify_otp(client, payload)
    assert response.status_code == 200
    assert response.json['status'] == 'failed'
    assert response.json['action'] == 'verify_otp'
    assert response.json['message'] == 'invalid otp code'

def test_verify_otp_successfully(client):
    """
    Test successful validation of OTP
    """

    db_engine = jqutils.get_db_engine()
    phone_nr = "+96112345678"
    otp_status = "pending"

    query = text("""
        SELECT otp.one_time_password_id, otp.otp
        FROM signup_request sr
        JOIN one_time_password otp ON otp.signup_request_id = sr.signup_request_id
        WHERE sr.phone_nr = :phone_nr
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, phone_nr=phone_nr).fetchone()
        assert result, "failed to get otp"
        one_time_password_id = result["one_time_password_id"]
        otp = result["otp"]
    
    query = text("""
        UPDATE one_time_password
        SET otp_status = :otp_status,
        otp_verified_timestamp = :otp_verified_timestamp
        WHERE one_time_password_id = :one_time_password_id
    """)
    with db_engine.connect() as conn:
        updated_p = conn.execute(query, otp_verified_timestamp=None, one_time_password_id=one_time_password_id, otp_status=otp_status).rowcount
        assert updated_p, "failed to update otp_status and otp_verified_timestamp"

    payload = {
        "phone_nr": phone_nr,
        "email": None,
        "otp": otp,
        "intent": "merchant_signup"
    }

    response = do_verify_otp(client, payload)
    assert response.status_code == 200
    assert response.json['status'] == 'successful'
    assert response.json['action'] == 'verify_otp'

    query = text("""
        SELECT otp_status, otp_verified_timestamp
        FROM one_time_password
        WHERE one_time_password_id = :one_time_password_id
        AND contact_method = :contact_method
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, one_time_password_id=one_time_password_id,contact_method='sms',meta_status='active').fetchone()
        assert result, "failed to get otp_status and otp_verified_timestamp"
        otp_status = result["otp_status"]
        otp_verified_timestamp = result["otp_verified_timestamp"]
        assert otp_status == "verified", "failed to update otp_status in db"
        assert otp_verified_timestamp is not None, "failed to update otp_verified_timestamp in db"

def test_verification_otp_if_already_verified(client):
    """
    Test verificiation of OTP if it is already verified for a phone number
    """

    db_engine = jqutils.get_db_engine()
    
    # Get current timestamp
    otp_verified_timestamp = datetime.datetime.now()
    otp_verified_timestamp_str = otp_verified_timestamp.strftime('%Y-%m-%d %H:%M:%S')
    phone_nr = "+96112345678"
    otp_status = "verified"

    query = text("""
        UPDATE one_time_password otp
        JOIN signup_request sr ON sr.signup_request_id = otp.signup_request_id
        SET otp.otp_status = :otp_status,
        otp.otp_verified_timestamp = :otp_verified_timestamp
        WHERE sr.phone_nr = :phone_nr
    """)
    with db_engine.connect() as conn:
        updated_p = conn.execute(query, phone_nr=phone_nr, otp_verified_timestamp=otp_verified_timestamp_str, otp_status=otp_status).rowcount
        assert updated_p, "failed to update otp_status"
    
    query = text("""
        SELECT otp.one_time_password_id, otp.otp
        FROM one_time_password otp
        JOIN signup_request sr ON sr.signup_request_id = otp.signup_request_id
        WHERE sr.phone_nr = :phone_nr
        AND otp.contact_method = :contact_method
        AND otp.meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, phone_nr=phone_nr, contact_method='sms', meta_status='active').fetchone()
        assert result, "failed to get otp"
        one_time_password_id = result["one_time_password_id"]
        otp = result["otp"]

    payload = {
        "phone_nr": phone_nr,
        "email": None,
        "otp": otp,
        "intent": "merchant_signup"
    }

    response = do_verify_otp(client, payload)
    assert response.status_code == 200
    assert response.json['status'] == 'successful'
    assert response.json['action'] == 'verify_otp'

    query = text("""
        SELECT otp_status, otp_verified_timestamp
        FROM one_time_password
        WHERE one_time_password_id = :one_time_password_id
        AND contact_method = :contact_method
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, one_time_password_id=one_time_password_id,contact_method='sms',meta_status='active').fetchone()
        assert result, "failed to get otp_status and otp_verified_timestamp"
        otp_status = result["otp_status"]
        otp_verified_timestamp_db = result["otp_verified_timestamp"]
        otp_verified_timestamp_db_str = otp_verified_timestamp_db.strftime('%Y-%m-%d %H:%M:%S')

        assert otp_status == "verified", "failed to update otp_status in db"
        assert otp_verified_timestamp_str == otp_verified_timestamp_db_str, "otp_verified_timestamp should not be updated"

def test_check_new_username_availability_successful(client, unverified_user_header):
    """
    Check username availability for a username that is available
    """

    username = "new.dummy.merchant"

    response = do_check_username_availability(client, unverified_user_header, username)
    assert response.status_code == 200
    assert response.json['status'] == 'successful'
    assert response.json['action'] == 'check_username_availability'
    assert response.json['available_p'] == True
    assert response.json['username'] == username

def test_check_existing_username_availability_successful(client, unverified_user_header):
    """
    Check username availability for a username that is NOT available
    """

    username = "admin"

    response = do_check_username_availability(client, unverified_user_header, username)
    assert response.status_code == 200
    assert response.json['status'] == 'successful'
    assert response.json['action'] == 'check_username_availability'
    assert response.json['available_p'] == False
    assert response.json['username'] == username

def test_update_user_credentials_successful(client, unverified_user_header):
    """
    Test update user credentials
    """

    user_id = unverified_user_header["X-User-Id"]
    
    payload = {
        "user_id": user_id,
        "email": "unverified_user@integrations.com",
        "username": "unverified_user",
        "password": "123456"
    }

    response = do_update_user_credentials(client, unverified_user_header, payload)
    assert response.status_code == 200
    assert response.json['status'] == 'successful'
    assert response.json['action'] == 'update_user_credentials'
    assert response.json['user_id'] == user_id, "user_id should be the same as the one in the header"
    assert response.json['verification_status']['verification_status'] == 'pending', "verification_status should be pending"

def test_merchant_verification_successful(client, unverified_user_header):
    """
    Upload merchant verification documents for review
    """
    user_id = unverified_user_header["X-User-Id"]
    
    payload = {
        "user_id": user_id,
        "merchant_details": {
            "merchant_name": "john's autopark",
            "merchant_website_url": "https://autopark.com",
            "merchant_phone_nr": "+964123456789",
            "merchant_email": "merchant@example.com",
            "business_type_id": 1,
            "business_category_id": 1,
        },
    }

    response = do_merchant_verification(client, unverified_user_header, payload)
    assert response.status_code == 200
    assert response.json['status'] == 'successful'
    assert response.json['action'] == 'merchant_verification'
    db_engine = jqutils.get_db_engine()

    merchant_id = response.json['merchant_id']

    query = text("""
        SELECT payment_point_area_id FROM payment_point_area
        WHERE merchant_id = :merchant_id
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, merchant_id=merchant_id).fetchone()
        assert result, "failed to get payment_point_area_id"
        payment_point_area_id = result["payment_point_area_id"]

    query = text("""
        SELECT user_payment_point_area_map_id FROM user_payment_point_area_map
        WHERE user_id = :user_id and payment_point_area_id = :payment_point_area_id
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, user_id=user_id, payment_point_area_id=payment_point_area_id).fetchone()
        assert result, "failed to get user_payment_point_area_map_id"

def test_upload_merchant_document(client, unverified_user_header):
    """
    Upload merchant verification documents for review
    """
    user_id = unverified_user_header["X-User-Id"]
    
    db_engine = jqutils.get_db_engine()
    
    # get merchant_id for the user
    query = text("""
        SELECT merchant_id
        FROM user_merchant_map
        WHERE user_id = :user_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, user_id=user_id, meta_status='active').fetchone()
        assert result, "failed to get merchant_id"
        merchant_id = result["merchant_id"]
    
    with open("tests/testdata/sample_trade_license.png", "rb") as file_data:
        payload = {
            "merchant_id": merchant_id,
            "trade_license": file_data
        }
    
        response = do_upload_merchant_document(client, unverified_user_header, payload)
        assert response.status_code == 200
        assert response.json['status'] == 'successful'
        assert response.json['action'] == 'upload_merchant_document'

def test_generate_otp_successfully():

    phone_nr = "+96454345345"
    email = "admin@example.com"

    """
    Generate a new otp request using sms with the intent of testing
    """
    contact_method = 'sms'
    intent = 'test_sms'
    user_id = 1
    sms_one_time_password_id_for_user_1, existing_otp_request_count = access_ninja.generate_otp(contact_method, intent, user_id=user_id, phone_nr=phone_nr)

    assert existing_otp_request_count == 1, "if its a new otp request, it should have request count == 1"

    """
    Request otp request for an existing request using sms with the intent of testing
    """
    contact_method = 'sms'
    intent = 'test_sms'
    user_id = 1
    one_time_password_id, otp_request_count = access_ninja.generate_otp(contact_method, intent, one_time_password_id=sms_one_time_password_id_for_user_1, user_id=user_id, phone_nr=phone_nr)

    assert one_time_password_id == sms_one_time_password_id_for_user_1, "the existing request should've been updated"
    assert existing_otp_request_count + 1 == otp_request_count, "otp request count should've been incremented by 1"

    """
    Generate a new otp request using email with the intent of testing
    """
    contact_method = 'email'
    intent = 'test_email'
    user_id = 1
    email_one_time_password_id_for_user_1, existing_otp_request_count = access_ninja.generate_otp(contact_method, intent, user_id=user_id, email=email)

    assert existing_otp_request_count == 1, "if its a new otp request, it should have request count == 1"

    """
    Request otp request for an existing request using sms with the intent of testing
    """
    contact_method = 'email'
    intent = 'test_email'
    user_id = 1
    one_time_password_id, otp_request_count = access_ninja.generate_otp(contact_method, intent, one_time_password_id=email_one_time_password_id_for_user_1, user_id=user_id, email=email)

    assert one_time_password_id == email_one_time_password_id_for_user_1, "the existing request should've been updated"
    assert existing_otp_request_count + 1 == otp_request_count, "otp request should've been incremented by 1"

    """
    Requesting new otp request for a different user shouldn't conflict with existing ones
    """
    contact_method = 'sms'
    intent = 'test_sms'
    user_id = 2
    sms_one_time_password_id_for_user_2, otp_request_count = access_ninja.generate_otp(contact_method, intent, user_id=user_id, phone_nr=phone_nr)

    assert otp_request_count == 1, "if its a new otp request, it should have request count == 1"
    assert sms_one_time_password_id_for_user_2 not in [sms_one_time_password_id_for_user_1, email_one_time_password_id_for_user_1]

    """
    Requesting new otp request for a different user shouldn't conflict with existing ones
    """
    contact_method = 'email'
    intent = 'test_email'
    user_id = 2
    email_one_time_password_id_for_user_2, otp_request_count = access_ninja.generate_otp(contact_method, intent, user_id=user_id, email=email)

    assert otp_request_count == 1, "if its a new otp request, it should have request count == 1"
    assert email_one_time_password_id_for_user_2 not in [sms_one_time_password_id_for_user_1, email_one_time_password_id_for_user_1, email_one_time_password_id_for_user_1]

    """
    Requesting new otp request for the same user with different intent shouldn't conflict with existing ones
    """
    contact_method = 'sms'
    intent = 'test_different_sms'
    user_id = 1
    different_sms_one_time_password_id_for_user_1, otp_request_count = access_ninja.generate_otp(contact_method, intent, user_id=user_id, phone_nr=phone_nr)

    assert otp_request_count == 1, "if its a new otp request, it should have request count == 1"
    assert different_sms_one_time_password_id_for_user_1 not in [sms_one_time_password_id_for_user_1, sms_one_time_password_id_for_user_2, email_one_time_password_id_for_user_1, email_one_time_password_id_for_user_2]

    """
    Requesting new otp request for the same user with different intent shouldn't conflict with existing ones
    """
    contact_method = 'email'
    intent = 'test_different_email'
    user_id = 1
    different_email_one_time_password_id_for_user_1, otp_request_count = access_ninja.generate_otp(contact_method, intent, user_id=user_id, email=email)

    assert otp_request_count == 1, "if its a new otp request, it should have request count == 1"
    assert different_email_one_time_password_id_for_user_1 not in [different_sms_one_time_password_id_for_user_1, sms_one_time_password_id_for_user_1, sms_one_time_password_id_for_user_2, email_one_time_password_id_for_user_1, email_one_time_password_id_for_user_2]

def test_initiate_forgot_password_request_using_email(client):
    
    db_engine = jqutils.get_db_engine()
    user_id = 2
    
    # get email and username for company-x user
    query = text("""
        SELECT email
        FROM user
        WHERE user_id = :user_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, user_id=user_id, meta_status='active').fetchone()
        assert result, "failed to get user_id and email"
        username = None
        email = result["email"]

    payload = {
        "username": username,
        "email": email,
    }
    response = do_initiate_forgot_password_request(client, payload)
    assert response.status_code == 200
    response_body = response.json
    assert response_body["status"] == "successful"
    assert response_body["action"] == "initiate_forgot_password_request"
    assert response_body["user_id"] == user_id
    assert response_body["contact_method"] == "email"

def test_initiate_forgot_password_request_using_username(client):
    
    db_engine = jqutils.get_db_engine()
    user_id = 2
    
    # get email and username for company-x user
    query = text("""
        SELECT username
        FROM user
        WHERE user_id = :user_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, user_id=user_id, meta_status='active').fetchone()
        assert result, "failed to get user_id and email"
        username = result["username"]
        email = None

    payload = {
        "username": username,
        "email": email,
    }
    response = do_initiate_forgot_password_request(client, payload)
    assert response.status_code == 200
    response_body = response.json
    assert response_body["status"] == "successful"
    assert response_body["action"] == "initiate_forgot_password_request"
    assert response_body["user_id"] == user_id
    assert response_body["contact_method"] == "email"

def test_initiate_forgot_password_request_using_non_existing_email(client):
    
    username = None
    email = "dummy@example.com"

    payload = {
        "username": username,
        "email": email,
    }
    response = do_initiate_forgot_password_request(client, payload)
    assert response.status_code == 200
    response_body = response.json
    assert response_body["status"] == "failed"
    assert response_body["action"] == "initiate_forgot_password_request"
    assert response_body["message"] == "User not found"

def test_get_forgot_password_request_successfully(client):

    db_engine = jqutils.get_db_engine()
    
    otp_status = 'sent'
    contact_method = 'email'
    user_id = 2
    intent = 'forgot_password'

    query = text("""
        SELECT otp
        FROM one_time_password
        WHERE otp_status = :otp_status
        AND contact_method = :contact_method
        AND user_id = :user_id
        AND intent = :intent
        AND meta_status = :meta_status
        ORDER BY otp_requested_timestamp DESC
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, otp_status=otp_status, contact_method=contact_method, user_id=user_id, intent=intent, meta_status='active').fetchone()
        assert result, "failed to get otp"
        otp = result["otp"]
    
    response = do_get_forgot_password_request(client, otp)
    assert response.status_code == 200
    response_body = response.json
    assert response_body["status"] == "successful"
    assert response_body["action"] == "get_forgot_password_request"
    assert response_body["otp_status"] == otp_status

def test_reset_password_using_otp_successful(client):

    db_engine = jqutils.get_db_engine()

    otp_status = 'sent'
    contact_method = 'email'
    user_id = 2
    intent = 'forgot_password'

    query = text("""
        SELECT otp
        FROM one_time_password
        WHERE otp_status = :otp_status
        AND contact_method = :contact_method
        AND user_id = :user_id
        AND intent = :intent
        AND meta_status = :meta_status
        ORDER BY otp_requested_timestamp DESC
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, otp_status=otp_status, contact_method=contact_method, user_id=user_id, intent=intent, meta_status='active').fetchone()
        assert result, "failed to get otp"
        otp = result["otp"]
    
    query = text("""
        SELECT password
        FROM user
        WHERE user_id = :user_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, user_id=user_id, meta_status='active').fetchone()
        assert result, "failed to get password"
        old_password = result["password"]
    
    payload = {
        "otp": otp,
        "password": "654321"
    }
    response = do_reset_user_password(client, payload)
    assert response.status_code == 200
    response_body = response.json
    assert response_body["status"] == "successful"
    assert response_body["action"] == "reset_user_password"
    assert response_body["user_id"] == user_id

    query = text("""
        SELECT password
        FROM user
        WHERE user_id = :user_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, user_id=user_id, meta_status='active').fetchone()
        assert result, "failed to get password"
        new_password = result["password"]
    
    assert old_password != new_password, "password should've been updated"

    password_manager = DataMigrationManager()
    decrypted_password = password_manager.decrypt_password(new_password.encode())

    assert decrypted_password.decode() == payload["password"], "password should've been updated to the new one"

def test_social_media_signup(client):
    
    data = {
        "social_media_name": "facebook",
        "email": "socialmediatest@example.com",
        "social_media_external_id": 1
    }
    
    response = do_social_media_login(client, data)
    assert response.status_code == 200, "failed to login with social media"

def test_mark_signup_completed(client, headers):
    response = do_mark_signup_completed(client, headers, 1, 1)
    assert response.status_code == 200, "failed to mark signup completed"

def test_contact_us_successfully(client):
    """
    Test successful contact us
    """

    payload = {
        "first_name_en": "john",
        "last_name_en": "doe",
        "phone_nr": "+96112345678",
        "email": "john_doe@xyz.com",
        "company_name": "John Doe Restaurant",
        "message": "I need this solution for my restaurant",
        "source_of_contact": "social",
    }

    response = do_contact_us(client, payload)
    assert response.status_code == 200
    assert response.json['status'] == 'successful'
    assert response.json['action'] == 'contact_us'

def test_contact_us_if_already_existing(client):
    """
    Test contact us with email that already exists
    """

    for idx in range(3):
        payload = {
            "first_name_en": "john",
            "last_name_en": "doe",
            "phone_nr": "+96112345678",
            "email": "john_doe@xyz.com",
            "company_name": "John Doe Restaurant",
            "message": "I need this solution for my restaurant",
            "source_of_contact": "social",
        }

        response = do_contact_us(client, payload)

    assert response.status_code == 200
    assert response.json['status'] == 'failed'
    assert response.json['action'] == 'contact_us'
    assert response.json['message'] == 'email already exists.'

def test_do_add_facility_to_user(client,headers):
    data = {
        "facility_id_list": [4,5,6,7]
    }
    user_id = headers["X-User-Id"]
    response = go_add_facility_to_user(client,headers,user_id,data)
    assert response.json['status'] == 'successful'

def test_do_delete_facility_user(client,headers):
    data = {
        "facility_id": 7,
        "user_id": 1
    }
    response = do_delete_user_facility(client,headers,data)
    assert response.json['status'] == 'successful'

# def test_do_update_user_password(client,headers):

#     data = {
#         "old_password": "123456",
#         "new_password": "12345678"
#     }
#     user_id = headers["X-User-Id"]
#     print(user_id)
#     print(headers)
#     response = do_update_user_password(client,headers,user_id,data)
#     print(response)
#     assert response.status_code == 200
#     assert response.json['status'] == 'successful'
#     assert response.json['action'] == 'update_user_password'
    
def test_do_get_user_organization(client,headers):
    user_id = headers["X-User-Id"]
    response = do_get_user_organizations(client,headers,user_id)
    assert response.status_code == 200
    assert response.json['status'] == 'successful'
    assert response.json['action'] == 'get_user_organizations'