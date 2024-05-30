from utils import jqutils
from sqlalchemy.sql import text
import pytest
import json

base_api_url = "/api"

invitation_type = "join-merchant"
contact_method = "email"
recipient_email = "abc@gmail.com"
recipient_phone_nr = None

##########################
# TEST - INVITATION
########################## 
def do_get_invitations(client,user_headers):
    """
    Get Invitations
    """
    response = client.get(base_api_url + "/invitations", headers=user_headers)
    return response

def do_get_invitation(client,user_headers, invitation_id):
    """
    Get One Invitation
    """
    response = client.get(base_api_url + "/invitation/" +str(invitation_id), headers=user_headers)
    return response

def do_get_invitation_by_code(client, invitation_code):
    """
    Get One Invitation By Code
    """
    response = client.get(base_api_url + "/invitation/code/" +str(invitation_code))
    return response

def do_add_invitation(client,user_headers, payload):
    """
    Add Invitation
    """
    response = client.post(base_api_url + "/invitation", headers=user_headers, json=payload)
    return response

def do_resend_invitation(client,user_headers, invitation_id, contact_method=None):
    """
    Resend Invitation
    """
    url = base_api_url + "/resend-invitation/" + str(invitation_id)
    if contact_method:
        url += "?contact_method=" + contact_method
    response = client.get(url, headers=user_headers)
    return response

def do_cancel_invitation(client,user_headers, invitation_id):
    """
    Cancel Invitation
    """
    response = client.delete(base_api_url + "/invitation/" +str(invitation_id), headers=user_headers)
    return response


##########################
# TEST CASES
########################## 

def test_successful_add_invitation(client,user_headers):
    """
    Test add invitation
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
    response = do_add_invitation(client,user_headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'add_invitation'

    assert "invitation_id" in j
    assert jqutils.get_column_by_id(str(j["invitation_id"]), "invitation_type", "invitation") == "join-merchant", "Record not created in db, please check."

def test_failed_add_invitation_with_missing_params(client,user_headers):
    """
    Test add invitation
    """
    payload = {}
    with pytest.raises(Exception):
        do_add_invitation(client,user_headers, payload)

def test_failed_add_invitation_with_existing_data(client,user_headers):
    """
    Test add invitation again with same data
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
    response = do_add_invitation(client,user_headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'failed'
    assert j["action"] == 'add_invitation'

def test_get_invitations(client,user_headers):
    """
    Test get invitations
    """
    response = do_get_invitations(client,user_headers)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert len(j["data"]) > 0
    assert j["action"] == 'search_invitation_by_filter'

def test_resend_invitation(client,user_headers):
    """
    Test resend invitation
    """
    db_engine = jqutils.get_db_engine()
    query = text("""
            SELECT invitation_id
            FROM invitation
            WHERE invitation_type = :invitation_type
            AND contact_method = :contact_method
            AND recipient_email = :recipient_email
            AND meta_status = :meta_status
        """)
    with db_engine.connect() as conn:
        result = conn.execute(query, invitation_type=invitation_type, contact_method=contact_method, recipient_email=recipient_email, meta_status="active").fetchone()
        assert result, "Record not found in db, please check."
        invitation_id = result["invitation_id"]
    
    response = do_resend_invitation(client,user_headers, invitation_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'resend_invitation'

def test_get_invitation(client,user_headers):
    """
    Test get one invitation
    """
    db_engine = jqutils.get_db_engine()
    query = text("""
            SELECT invitation_id
            FROM invitation
            WHERE invitation_type = :invitation_type
            AND contact_method = :contact_method
            AND recipient_email = :recipient_email
            AND meta_status = :meta_status
        """)
    with db_engine.connect() as conn:
        result = conn.execute(query, invitation_type=invitation_type, contact_method=contact_method, recipient_email=recipient_email, meta_status="active").fetchone()
        assert result, "Record not found in db, please check."
        invitation_id = result["invitation_id"]
    
    response = do_get_invitation(client,user_headers, invitation_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_one_invitation'

    assert "invitation_id" in j["data"]

def test_get_invitation_by_code_successfully(client):
    """
    Test get one invitation
    """
    db_engine = jqutils.get_db_engine()
    query = text("""
            SELECT invitation_code
            FROM invitation
            WHERE invitation_type = :invitation_type
            AND contact_method = :contact_method
            AND recipient_email = :recipient_email
            AND meta_status = :meta_status
        """)
    with db_engine.connect() as conn:
        result = conn.execute(query, invitation_type=invitation_type, contact_method=contact_method, recipient_email=recipient_email, meta_status="active").fetchone()
        assert result, "Record not found in db, please check."
        invitation_code = result["invitation_code"]
    
    response = do_get_invitation_by_code(client, invitation_code)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_one_invitation_by_code'

    assert "invitation_id" in j["data"]

def test_get_invitation_by_code_invalid_code(client):
    """
    Test get one invitation
    """
    invitation_code = "dummy_code"
    
    response = do_get_invitation_by_code(client, invitation_code)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'failed'
    assert j["action"] == 'get_one_invitation_by_code'
    assert j["data"] == None

def test_cancel_invitation(client,user_headers):
    """
    Test cancel invitation
    """
    db_engine = jqutils.get_db_engine()
    query = text("""
            SELECT invitation_id
            FROM invitation
            WHERE invitation_type = :invitation_type
            AND contact_method = :contact_method
            AND recipient_email = :recipient_email
            AND meta_status = :meta_status
        """)
    with db_engine.connect() as conn:
        result = conn.execute(query, invitation_type=invitation_type, contact_method=contact_method, recipient_email=recipient_email, meta_status="active").fetchone()
        assert result, "Record not found in db, please check."
        invitation_id = result["invitation_id"]
    response = do_cancel_invitation(client,user_headers, invitation_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'cancel_invitation'

