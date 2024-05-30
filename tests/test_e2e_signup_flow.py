import json

from tests import test_user, test_invitation
from utils import jqutils
from sqlalchemy import text

base_api_url = "/api"

def do_soft_login(client, phone_nr):
    db_engine = jqutils.get_db_engine()

    """
    Login using phone number
    """
    intent = "soft_login"
    response = test_user.do_request_otp(client, phone_nr, None, intent)
    assert response.status_code == 200
    assert response.json['status'] == 'successful'
    assert response.json['action'] == 'request_otp'

    """
    Get merchant role from db
    """
    merchant_role_name = "merchant"
    query = text("""
        SELECT role_id
        FROM role
        WHERE role_name = :role_name
        AND meta_status = :status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, role_name=merchant_role_name, status='active').fetchone()
        assert result, "no merchant role found"
        merchant_role_id = result["role_id"]

    """
    Get OTP code from database
    Normally the user would receive OTP code on phone via SMS.
    """
    contact_method = "sms"
    query = text("""
        SELECT otp.otp
        FROM one_time_password otp
        JOIN user u ON otp.user_id = u.user_id
        WHERE u.phone_nr = :phone_nr
        AND otp.contact_method = :contact_method
        AND otp.intent = :intent
        AND u.meta_status = :status
        ORDER BY otp.otp_requested_timestamp DESC
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, phone_nr=phone_nr, contact_method=contact_method, intent=intent, status='active').fetchone()
        assert result, "failed to get otp_request"
        otp_code = result["otp"]

    """
    Verify OTP code for merchant_login
    """
    payload = {
        "phone_nr": phone_nr,
        "email": None,
        "otp": otp_code,
        "intent": "soft_login"
    }
    response = test_user.do_verify_otp(client, payload)
    assert response.status_code == 200
    assert response.json['status'] == 'successful'
    assert response.json['action'] == 'verify_otp'

    """
    Since the intent was for merchant_login, the user should be logged in as a merchant after verification
    """

    data = response.json['data']
    assert data["username"] == None
    assert data["role_id"] == 2
    assert data["role_name"] == "merchant"
    assert data["user_details"]["user_id"] > 0
    assert data["user_details"]["first_name"] == "john"
    assert data["user_details"]["last_name"] == "doe"
    assert data["user_details"]["phone_verified_p"] == True
    assert data["role_id"] == merchant_role_id
    assert data["role_name"] == merchant_role_name
    assert data["merchant"]["merchant_id"] == None
    assert data["merchant"]["merchant_type"]["merchant_type_id"] == None
    assert data["merchant"]["merchant_type"]["merchant_type_name"] == None
    assert data["merchant"]["merchant_website_url"] == None
    assert data["merchant"]["merchant_code"] == None
    assert data["merchant"]["merchant_name"] == None
    assert data["merchant"]["merchant_email"] == None
    assert data["merchant"]["merchant_logo_url"] == None
    assert data["merchant"]["merchant_description"] == None
    assert data["merchant"]["merchant_api_key"] == None
    assert data["merchant"]["payment_link_expiry_duration"] == None
    assert data["merchant"]["expiry_duration_measurement_id"] == None
    
    assert response.headers["X-Access-Token"] != None
    assert int(response.headers["X-User-Id"]) > 0

    user_id = int(response.headers["X-User-Id"])
    access_token = response.headers["X-Access-Token"]

    """
    Use current_user endpoint to get user details
    """
    response = test_user.do_get_current_user(client, access_token, user_id)
    assert response.status_code == 200
    j = response.json
    assert j["status"] == 'successful'


##############
# TEST-CASE
##############

phone_nr = "+92456123216"
invitation_type = "join-merchant"
contact_method = "email"
recipient_email = "abc12@gmail.com"
recipient_phone_nr = None

def test_e2e_signup_flow(client):

    user_id, access_token, otp_code = test_user.do_user_signup(client, phone_nr, "john doe")

    """
    Use current_user endpoint to get user details
    """
    response = test_user.do_get_current_user(client, access_token, user_id)
    assert response.status_code == 200
    j = response.json
    assert j["status"] == 'successful'

    """
    Verify OTP code for merchant_signup for the second time
    No new user should be created but rather existing user should be returned
    """
    payload = {
        "phone_nr": phone_nr,
        "email": None,
        "otp": otp_code,
        "intent": "merchant_signup"
    }
    response = test_user.do_verify_otp(client, payload)
    assert response.status_code == 200
    assert response.json['status'] == 'successful'
    assert response.json['action'] == 'verify_otp'
    assert int(response.headers['X-User-Id']) == user_id
    assert response.headers['X-Access-Token'] == access_token

def test_e2e_signup_flow_with_invitation_code(client, user_headers):
    
    """
    Create invitation request for a merchant employee
    """
    payload = {
        "invitation_type": invitation_type,
        "contact_method": contact_method,
        "recipient_email": recipient_email,
        "recipient_phone_nr": None,
        "recipient_role_id": 2,
        "invitation_expiry_timestamp": None,
        "user_id": user_headers.get("X-User-Id"),
        "merchant_id": user_headers.get("X-Merchant-Id"),
    }
    response = test_invitation.do_add_invitation(client,user_headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'add_invitation'

    invitation_link = j["invitation_link"]
    invitation_code = invitation_link.split("/")[-1]

    user_id, access_token, otp_code = test_user.do_user_signup(client, "+92456123212", "shiekh mansour", invitation_code)

    """
    Use current_user endpoint to get user details
    """
    response = test_user.do_get_current_user(client, access_token, user_id)
    assert response.status_code == 200
    j = response.json
    assert j["status"] == 'successful'

    """
    Verify OTP code for merchant_signup for the second time
    No new user should be created but rather existing user should be returned
    """
    payload = {
        "phone_nr": "+92456123212",
        "email": None,
        "otp": otp_code,
        "intent": "merchant_signup"
    }
    response = test_user.do_verify_otp(client, payload)
    assert response.status_code == 200
    assert response.json['status'] == 'successful'
    assert response.json['action'] == 'verify_otp'
    assert int(response.headers['X-User-Id']) == user_id
    assert response.headers['X-Access-Token'] == access_token

    """
    Test update user credentials
    """
    unverified_user_header = {
        "X-User-Id": user_id,
        "X-Access-Token": access_token
    }
    
    payload = {
        "user_id": user_id,
        "email": "unverified_user@integrations.com",
        "username": "unverified_user",
        "password": "123456"
    }
    
    response = test_user.do_update_user_credentials(client, unverified_user_header, payload)
    assert response.status_code == 200
    assert response.json['status'] == 'successful'
    assert response.json['action'] == 'update_user_credentials'
    assert response.json['user_id'] == user_id, "user_id should be the same as the one in the header"
    assert response.json['verification_status']['verification_status'] == 'under-review', "verification_status should be under-review"

def test_e2e_soft_login_flow(client):
    """
    Do soft login 5 times.
    Should register 5 new otp requests
    """

    for i in range(0, 5):
        do_soft_login(client, phone_nr)
