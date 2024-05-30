from utils import jqutils, jqaccess_control_engine, jqsecurity, aws_utils, whatsapp_utils
from sqlalchemy import text
import random
import datetime
import os

def get_merchant_details_for_user(user_id):
    """
    Get the merchant details for a user
    """
    
    db_engine = jqutils.get_db_engine()

    query = text("""
        SELECT
            m.merchant_id, m.merchant_type_id, mt.merchant_type_name, m.merchant_name, m.merchant_code, m.merchant_email,
            m.merchant_website_url, m.merchant_description, m.merchant_api_key, m.payment_link_expiry_duration,
            m.expiry_duration_measurement_id, mi.merchant_image_bucket_name, mi.merchant_image_object_key
        FROM
            user u
        LEFT JOIN
            user_merchant_map umm on umm.user_id = u.user_id
        LEFT JOIN
            merchant m on m.merchant_id = umm.merchant_id
        LEFT JOIN
            merchant_type mt on mt.merchant_type_id = m.merchant_type_id
        LEFT JOIN
            merchant_image mi on m.merchant_id = mi.merchant_id
        WHERE
            u.user_id = :user_id
        AND
            u.meta_status = :status
    """)
    with db_engine.connect() as conn:
        user_merchant_result = conn.execute(query, user_id=user_id, status='active').fetchone()

    # get presigned url for merchant logo
    merchant_logo_url = None
    if user_merchant_result["merchant_image_bucket_name"] and user_merchant_result["merchant_image_object_key"]:
        merchant_logo_url = jqutils.create_presigned_get_url(user_merchant_result["merchant_image_bucket_name"], user_merchant_result["merchant_image_object_key"], expiration=3600)

    # decrypt merchant api key if exists
    merchant_api_key = user_merchant_result['merchant_api_key']
    if merchant_api_key:
        merchant_api_key = jqaccess_control_engine.decrypt_password(user_merchant_result['merchant_api_key']).decode()
    
    merchant_details = {
        'merchant_id' : user_merchant_result['merchant_id'],
        'merchant_type': {
            'merchant_type_id': user_merchant_result['merchant_type_id'],
            "merchant_type_name": user_merchant_result['merchant_type_name']
        },
        'merchant_website_url' : user_merchant_result['merchant_website_url'],
        'merchant_code' : user_merchant_result['merchant_code'],
        'merchant_name' : user_merchant_result['merchant_name'],
        'merchant_email' : user_merchant_result['merchant_email'],
        'merchant_logo_url': merchant_logo_url,
        'merchant_description' : user_merchant_result['merchant_description'],
        'merchant_api_key' :  merchant_api_key,
        'payment_link_expiry_duration': user_merchant_result["payment_link_expiry_duration"],
        'expiry_duration_measurement_id': user_merchant_result["expiry_duration_measurement_id"],
    }

    return merchant_details

def get_user_access_token(user_id):
    """
    Generates a new access token for a user if it does not exist or if the existing token has expired
    """
    
    db_engine = jqutils.get_db_engine()

    query = text("""
        select access_token 
        from user 
        where user_id = :user_id
        and access_token is not null
        and token_expiry_timestamp > now()
        and meta_status = 'active'
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, user_id=user_id).fetchone()
    
    if result:
        access_token = result['access_token']
    else:
        access_token = jqsecurity.generate_secret(16)
        
        query = text("""
            update user
            set access_token = :access_token,
            token_expiry_timestamp = now() + INTERVAL 180 DAY
            where user_id = :user_id
        """)

        with db_engine.connect() as conn:
            result = conn.execute(query, access_token=access_token, user_id=user_id).rowcount
            assert result, "failed to update access token"
    
    return access_token

def generate_otp(contact_method, intent, one_time_password_id=None, signup_request_id=None, user_id=None, email=None, phone_nr=None, email_intent='otp', merchant_name=None):
    
    # generate random numeric 6 digit otp
    otp = random.randint(100000, 999999)
    otp_request_count=1
    otp_requested_timestamp = datetime.datetime.now()
    otp_status='pending'

    assert signup_request_id is not None or user_id is not None, "requires at least one dependency"
    assert contact_method in ['sms', 'email'], "unknown contact method"
    
    if contact_method in ['sms', 'whatsapp']:
        assert phone_nr is not None, "phone_nr is required for sms otp"
    elif contact_method == 'email':
        assert email is not None, "email is required for email otp"

    db_engine = jqutils.get_db_engine()

    if one_time_password_id:
        # get existing otp request details
        query = text("""
            SELECT otp_request_count, otp
            FROM one_time_password
            WHERE one_time_password_id = :one_time_password_id
            AND meta_status = :meta_status
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, one_time_password_id=one_time_password_id, meta_status='active').fetchone()
            assert result, f"unable to find existing one_time_password with id: {one_time_password_id}"
            otp = result["otp"]
            otp_request_count = result["otp_request_count"] + 1
    
    else:
        # insert otp request
        query = text("""
            INSERT INTO one_time_password (signup_request_id, user_id, otp, intent, contact_method, otp_request_count, otp_requested_timestamp, otp_status, meta_status)
            VALUES(:signup_request_id, :user_id, :otp, :intent, :contact_method, :otp_request_count, :otp_requested_timestamp, :otp_status, :meta_status)
        """)
        with db_engine.connect() as conn:
            one_time_password_id = conn.execute(query, signup_request_id=signup_request_id, user_id=user_id, otp=otp, intent=intent, contact_method=contact_method, otp_request_count=otp_request_count,
                                    otp_requested_timestamp=otp_requested_timestamp, otp_status=otp_status, meta_status='active').lastrowid
            assert one_time_password_id, "otp request insert error"
    
    # send otp
    if os.getenv("MOCK_AWS_NOTIFICATIONS") != "1" and os.getenv("MOCK_WHATSAPP") != "1":
        if contact_method == 'sms':
            if intent == "customer_signup":
                body = f"Here's your OTP: {otp} for {merchant_name} registration. Please do not share this OTP with anyone."
            else:
                body = f"Dear customer, your OTP for registration is {otp}. Please do not share this OTP with anyone."
            aws_utils.publish_text_message(phone_nr=phone_nr, message=body)
        elif contact_method == 'email':
            if email_intent == 'otp':
                aws_utils.publish_email(
                    source="noreply@iblinknext.com",
                    destination={
                        "ToAddresses": [email],
                    },
                subject=f"Welcome to iBlinkPay",
                    text=f"Dear customer,\n\nYour OTP for registration is {otp}. Please do not share this OTP with anyone.",
                    html=f"Dear customer,<br><br>Your OTP for registration is {otp}. Please do not share this OTP with anyone."
                )
            else:
                frontend_base_url = "https://portal.iblinkx.com"
                confirmation_link = f"{frontend_base_url}/confirm-email/{otp}?email={email}"
                
                aws_utils.publish_email(
                    source="noreply@iblinknext.com",
                    destination={
                        "ToAddresses": [email],
                    },
                subject=f"Welcome to iBlinkX",
                    text=f"Dear customer,\n\nThank you for signing up. Please click on this link to setup your account:\n\n{confirmation_link}.",
                    html=f"Dear customer,<br><br>Thank you for signing up. Please click on this link to setup your account:<br><br><a href=\"{confirmation_link}\">{confirmation_link}</a>."
                )
        elif contact_method == 'whatsapp':
            whatsapp_utils.send_message(to_phone_nr=phone_nr, otp=otp)

    # update otp status
    otp_status = 'sent'
    otp_requested_timestamp = datetime.datetime.now()
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
    
    return one_time_password_id, otp_request_count