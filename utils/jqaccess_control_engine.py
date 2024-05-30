import secrets
import hashlib
import hmac
import os

from sqlalchemy.sql import text
from flask import request, g

from utils import jqutils, jqsecurity
from data_migration_management.data_migration_manager import DataMigrationManager

TOKEN_VALIDATION_MECHANISM = "db" # db or jwt

def validate_token():
    access_token = request.headers['X-Access-Token']
    user_id = request.headers['X-User-ID']
    assert user_id , "X-User-ID not found"
    g.user_id = user_id
    
    # BELOW: validating an access token from database and NOT JWT for now.
    if(TOKEN_VALIDATION_MECHANISM=="db"):
        db_engine = jqutils.get_db_engine()
        with db_engine.connect() as conn:
            query = text(""" 
                select us.user_id, us.username, urm.role_id, us.tenant_id, us.user_code, umm.merchant_id, ucm.customer_id
                from user us
                left join user_role_map urm on us.user_id = urm.user_id
                left join user_merchant_map umm on us.user_id = umm.user_id
                left join user_customer_map ucm on us.user_id = ucm.user_id
                where us.user_id = :user_id and
                us.access_token = :access_token and
                us.token_expiry_timestamp > now() and
                us.meta_status = 'active'
                """)
            result = conn.execute(query, user_id=user_id, access_token=access_token).fetchone()
            if(result):
                g.user_id = result['user_id']
                g.user_code = result["user_code"]
                g.username = result['username']
                g.role_id = result['role_id']
                g.merchant_id = result["merchant_id"]
                g.customer_id = result["customer_id"]
                g.tenant_id = result["tenant_id"]
        assert result, " invalid token error"


def validate_path_permissions(base_api_url=""):
    db_engine = jqutils.get_db_engine()
    request_type = "api"

    if(request_type=="api"):
        request_path = request.path.replace(base_api_url, "").lower()
        request_method = request.method.lower()

    #  select config_statement->'$."""+ request.method.lower() + """' as permission
        with db_engine.connect() as conn:
            query = text(""" 
                    SELECT r.resource_id, r.pagination_max_limit
                        FROM resource r
                        join role_resource_permission_map rrpm on r.resource_id = rrpm.resource_id
                        where :request_path regexp r.path_regex and
                        r.method = :request_method and
                        rrpm.role_id = :role_id;
                """)   
            result = conn.execute(query, request_path=request_path, request_method=request_method, role_id=g.role_id).fetchone()
            g.resource_id = result['resource_id']
            g.pagination_max_limit = result['pagination_max_limit']

        assert result, "permission denied"


def fetch_resource_details(base_api_url=""):
    db_engine = jqutils.get_db_engine()
    request_type = "api"

    if(request_type=="api"):
        request_path = request.path.replace(base_api_url, "").lower()
        request_method = request.method.lower()

        query = text(""" 
            SELECT r.resource_id, r.pagination_max_limit
            FROM resource r
            WHERE :request_path regexp r.path_regex
            AND r.method = :request_method                      
        """)   
        with db_engine.connect() as conn:
            result = conn.execute(query, request_path=request_path, request_method=request_method).fetchone()
            assert result, "resource not defined"
        
        g.resource_id = result['resource_id']
        g.pagination_max_limit = result['pagination_max_limit']


def decrypt_password(password):
    password = password.encode()

    db_engine = jqutils.get_db_engine()

    with db_engine.connect() as conn:
        query = text(""" 
            SELECT
                symmetric_key 
            FROM
                payment_api_secret 
            WHERE
                description = 'password-protector-key'
            AND
                meta_status = 'active'
            """)
        result = conn.execute(query).fetchone()
        assert result, "Failed to get password protector key"
        
        key_string_db = result['symmetric_key']
        key_string_db_bytes = key_string_db.encode()
        
        password = jqsecurity.decrypt_bytes_symmetric_to_bytes(password, key_string_db_bytes)
    return password


def validate_merchant_api_key():
    api_key = request.headers['X-Api-Key']
    user_id = request.headers['X-User-Id']

    db_engine = jqutils.get_db_engine()

    query = text("""
        SELECT m.merchant_id, m.merchant_code, m.merchant_api_key, m.tenant_id, m.merchant_type_id, ucm.customer_id
        FROM user_merchant_map umm
        JOIN merchant m ON umm.merchant_id = m.merchant_id
        LEFT JOIN user_customer_map ucm ON umm.user_id = ucm.user_id
        WHERE umm.user_id = :user_id
        AND umm.meta_status = :meta_status
        AND m.meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, user_id=user_id, meta_status='active').fetchone()
        assert result, "user not mapped to any merchant"
    
    if api_key.encode() != decrypt_password(result['merchant_api_key']):
        assert False, f"permission denied for merchant key ({api_key})"

    g.tenant_id = result['tenant_id']
    g.merchant_id = result['merchant_id']
    g.merchant_code = result['merchant_code']
    g.merchant_type_id = result["merchant_type_id"]
    g.customer_id = result["customer_id"]

    query = text("""
        SELECT role_id
        FROM user_role_map
        WHERE user_id = :user_id
        AND meta_status = :meta_status
    """)

    with db_engine.connect() as conn:
        result = conn.execute(query, user_id=user_id, meta_status='active').fetchone()
        assert result, "Role not found for user"

    g.role_id = result['role_id']
    g.user_id = user_id


def validate_sumsub_webhook_hash():
    sumsub_webhook_secret = os.getenv('SUMSUB_WEBHOOK_SECRET').encode('utf-8')
    x_payload_digest = request.headers['x-payload-digest']

    request_payload = request.data

    signature_computed =hmac.new(sumsub_webhook_secret, request_payload, hashlib.sha1).hexdigest()
    assert secrets.compare_digest(x_payload_digest, signature_computed), "invalid hash"


def validate_b2binpay_webhook_hash():
    db_engine = jqutils.get_db_engine()
    query = text("""
                SELECT service_provider_username, service_provider_password
                FROM service_provider m 
                WHERE service_provider_name = :service_provider_name
                AND meta_status = :meta_status
            """)
    with db_engine.connect() as conn:
        result = conn.execute(query, service_provider_name='b2binpay', meta_status='active').fetchone()
        assert result, "Invalid service_provider_name: b2binpay"

    password_manager = DataMigrationManager()

    username = result["service_provider_username"]
    password = password_manager.decrypt_password(result["service_provider_password"].encode()).decode()

    callback_payload = request.json
    callback_sign = callback_payload['meta']['sign']
    callback_time = callback_payload['meta']['time']

    included_transfer = list(filter(lambda item: item['type'] == 'transfer', callback_payload['included']))

    included_transfer = included_transfer.pop()['attributes']
    deposit = callback_payload['data']['attributes']

    status = included_transfer['status']
    amount = included_transfer['amount']
    tracking_id = deposit['tracking_id']

    # prepare data for hash check
    message = status + amount + tracking_id + callback_time
    hash_secret = hashlib.sha256((username + password).encode()).digest()
    hash_hmac_result = hmac.new(hash_secret, message.encode(), hashlib.sha256).digest()

    assert secrets.compare_digest(hash_hmac_result, callback_sign), "invalid hash"
