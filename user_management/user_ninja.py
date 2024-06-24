import os
import re
import uuid

from datetime import datetime, timedelta
from utils import jqutils, aws_utils
from sqlalchemy import text

def check_username_availability(username, user_id=None):
    user_id_filter = ""
    if user_id:
        user_id_filter = "AND user_id != :user_id"
    
    db_engine = jqutils.get_db_engine()
    
    query = text(f"""
        SELECT user_id
        FROM user
        WHERE username = :username
        {user_id_filter}
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, username=username, user_id=user_id, meta_status="active").fetchone()

    return False if result else True

def check_username_validity(username):
    username_regex = r'^[a-zA-Z0-9_.-]+$'
    validity = re.fullmatch(username_regex, username)
     
    return True if validity else False

def send_user_signup_email(userdata, creation_user_id):

    user_id = userdata["user_id"]

    # create OTP request
    otp = str(uuid.uuid4())
    otp_requested_timestamp_str = jqutils.get_utc_datetime()
    otp_requested_timestamp = datetime.strptime(otp_requested_timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
    otp_expiry_timestamp = otp_requested_timestamp + timedelta(days=7)
    
    intent = "user_signup"
    contact_method = "email"

    db_engine = jqutils.get_db_engine()

    query = text("""
        INSERT INTO one_time_password (
            user_id, intent, contact_method, otp, otp_request_count, otp_requested_timestamp,
            otp_expiry_timestamp, otp_status, meta_status, creation_user_id
        )
        VALUES (
            :user_id, :intent, :contact_method, :otp, :otp_request_count, :otp_requested_timestamp,
            :otp_expiry_timestamp, :otp_status, :meta_status, :creation_user_id
        )
    """)
    with db_engine.connect() as conn:
        one_time_password_id = conn.execute(query, user_id=user_id, intent=intent, contact_method=contact_method, otp=otp,
                                otp_request_count=0, otp_requested_timestamp=otp_requested_timestamp, otp_expiry_timestamp=otp_expiry_timestamp,
                                otp_status="pending", meta_status="active", creation_user_id=creation_user_id).lastrowid
        assert one_time_password_id, "failed to create OTP request"

    # generate verification link
    fe_base_url = os.getenv("FE_PORTAL_WEB_URL")
    verification_link = f"{fe_base_url}/user-signup/{user_id}?otp={otp}"
    
    name = userdata["first_names_en"]
    if userdata["last_name_en"]:
        name += " " + userdata["last_name_en"]

    # send OTP to user email
    if os.getenv("MOCK_AWS_NOTIFICATIONS") != "1":
        email_templates = jqutils.get_email_templates("user_signup")

        html_template = email_templates['html']['body']
        text_template = email_templates['txt']['body']

        html_template = html_template.replace("[NAME]", name.title())
        html_template = html_template.replace("[LINK]", verification_link)

        text_template = text_template.replace("[NAME]", name.title())
        text_template = text_template.replace("[LINK]", verification_link)

        if contact_method == 'email':
            aws_utils.publish_email(
                source="haseeb.ahmed@globalvertices.com",
                destination={
                    "ToAddresses": [userdata["email"]],
                },
                subject=email_templates['html']['subject'],
                text=text_template,
                html=html_template
            )

    # update OTP status to sent
    query = text("""
        UPDATE one_time_password
        SET otp_status = :otp_status,
        modification_user_id = :modification_user_id
        WHERE one_time_password_id = :one_time_password_id
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, otp_status="sent", one_time_password_id=one_time_password_id, modification_user_id=creation_user_id).rowcount
        assert result, "failed to update OTP status"