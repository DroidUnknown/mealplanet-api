from utils import jqutils
from sqlalchemy import text
import pytest
import json

base_api_url = "/api"

##########################
# TEST - Merchant Tip
########################## 
def do_get_merchant_tip_choices(client,headers):
    """
    Get Merchant Tips
    """
    response = client.get(base_api_url + "/merchant-tip-choices", headers=headers)
    return response

def do_get_merchant_tip_choice(client,headers, merchant_tip_choice_id):
    """
    Get One Merchant Tip
    """
    response = client.get(base_api_url + "/merchant-tip-choice/" +str(merchant_tip_choice_id), headers=headers)
    return response

def do_add_merchant_tip_choice(client,headers, payload):
    """
    Add One Merchant Tip
    """
    response = client.post(base_api_url + "/merchant-tip-choice", headers=headers, json=payload)
    return response

def do_update_merchant_tip_choice(client,headers, payload):
    """
    Update One Merchant Tip
    """
    response = client.put(base_api_url + "/merchant-tip-choice", headers=headers, json=payload)
    return response

def do_delete_merchant_tip_choice(client,headers, merchant_tip_choice_id):
    """
    Delete One Merchant Tip
    """
    response = client.delete(base_api_url + "/merchant-tip-choice/" +str(merchant_tip_choice_id), headers=headers)
    return response


##########################
# TEST CASES
########################## 

def test_successful_add_merchant_tip(client,headers):
    """
    Test add merchant_tip_choice
    """
    payload = {
        "merchant_id" : 1,
        "tip_amount": 0.5,
        "percentage_p": 1,
        "tip_currency_id": 1,
        "default_p": 1,
    }
    response = do_add_merchant_tip_choice(client,headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'add_merchant_tip_choice'

    assert "merchant_tip_choice_id" in j
    assert jqutils.get_column_by_id(str(j["merchant_tip_choice_id"]), "merchant_id", "merchant_tip_choice") == 1, "Record not created in db, please check."

def test_failed_add_merchant_tip_with_missing_params(client,headers):
    """
    Test add merchant_tip_choice
    """
    payload = {}
    with pytest.raises(Exception):
        do_add_merchant_tip_choice(client,headers, payload)

def test_update_merchant_tip(client,headers):
    """
    Test update merchant_tip_choice
    """
    db_engine = jqutils.get_db_engine()

    query = text("""
        SELECT merchant_tip_choice_id
        FROM merchant_tip_choice
        WHERE merchant_id = :merchant_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, merchant_id=1, meta_status='active').fetchone()
        assert result, "No active merchant_tip_choice found for merchant_id 1"
        merchant_tip_choice_id = result["merchant_tip_choice_id"]
    
    payload = {
        "merchant_tip_choice_id" : merchant_tip_choice_id,
        "merchant_id" : 1,
        "tip_amount": 10,
        "percentage_p": 0,
        "tip_currency_id": 1,
        "default_p": 1,
    }
    response = do_update_merchant_tip_choice(client,headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'update_merchant_tip_choice'

    assert "merchant_tip_choice_id" in j
    assert jqutils.get_column_by_id(str(j["merchant_tip_choice_id"]), "merchant_id", "merchant_tip_choice") == 1, "Record not updated in db, please check."

def test_get_merchant_tip(client,headers):
    """
    Test get one merchant_tip_choice
    """
    db_engine = jqutils.get_db_engine()

    query = text("""
        SELECT merchant_tip_choice_id
        FROM merchant_tip_choice
        WHERE merchant_id = :merchant_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, merchant_id=1, meta_status='active').fetchone()
        assert result, "No active merchant_tip_choice found for merchant_id 1"
        merchant_tip_choice_id = result["merchant_tip_choice_id"]
    
    response = do_get_merchant_tip_choice(client,headers, merchant_tip_choice_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_one_merchant_tip_choice'

    assert "merchant_tip_choice_id" in j["data"]
    assert jqutils.get_column_by_id(str(j["data"]["merchant_tip_choice_id"]), "merchant_id", "merchant_tip_choice") == 1, "Wrong record fetched from db, please check."

def test_get_merchant_tips(client,headers):
    """
    Test get merchant_tip_choices
    """
    response = do_get_merchant_tip_choices(client,headers)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert len(j["data"]) > 0
    assert j["action"] == 'search_merchant_tip_choice_by_filter'

def test_delete_merchant_tip(client,headers):
    """
    Test delete merchant_tip_choice
    """
    db_engine = jqutils.get_db_engine()

    query = text("""
        SELECT merchant_tip_choice_id
        FROM merchant_tip_choice
        WHERE merchant_id = :merchant_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, merchant_id=1, meta_status='active').fetchone()
        assert result, "No active merchant_tip_choice found for merchant_id 1"
        merchant_tip_choice_id = result["merchant_tip_choice_id"]
    
    response = do_delete_merchant_tip_choice(client,headers, merchant_tip_choice_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'delete_merchant_tip_choice'

    updated_meta_status = jqutils.get_column_by_id(str(merchant_tip_choice_id), "meta_status", "merchant_tip_choice")
    assert updated_meta_status == "deleted"
    with pytest.raises(Exception):
        do_get_merchant_tip_choice(client,headers, merchant_tip_choice_id)