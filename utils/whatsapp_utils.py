import requests
import os
from utils import jqutils
from sqlalchemy import text

def get_whatsapp_account_details(merchant_id, version="19.0"):
    db_engine = jqutils.get_db_engine()
    
    query = text("""
        SELECT wa.whatsapp_account_id, wa.whatsapp_account_phone_nr, wa.external_account_id, wa.whatsapp_token
        FROM whatsapp_account wa
        JOIN merchant m ON m.merchant_group_id = wa.merchant_group_id
        WHERE m.merchant_id = :merchant_id
        AND wa.meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, merchant_id=merchant_id, meta_status='active').fetchone()
        assert result, f"No active whatsapp account found for merchant id: {merchant_id}"
    
    whatsapp_details = {
        "whatsapp_account_id": result['whatsapp_account_id'],
        "whatsapp_account_phone_nr": result['whatsapp_account_phone_nr'],
    }
    
    external_account_id = result['external_account_id'] 
    whatsapp_token = result['whatsapp_token']
    
    whatsapp_url = f'https://graph.facebook.com/v{version}/{external_account_id}/messages'
    
    return whatsapp_url, whatsapp_token, whatsapp_details

def send_message(template_name, to_phone_nr, message_list, image_url):
    whatsapp_url = os.environ.get('WHATSAPP_API_URL')
    whatsapp_access_token = os.environ.get('WHATSAPP_TOKEN')

    headers = {
        'Authorization': f'Bearer {whatsapp_access_token}',
        'Content-Type': 'application/json',
    }

    components = []

    if image_url:
        components.append({
            "type": "header",
            "parameters": [
                {
                    "type": "image",
                    "image": {
                        "link": image_url
                    }
                }
            ]
        })

    body_param_list = []
    for one_message in message_list:
        body_param_list.append({
            "type": "text",
            "text": one_message
        })

    components.append({
        "type": "body",
        "parameters": body_param_list
    })

    data = {
        "messaging_product": "whatsapp",
        "to": to_phone_nr,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {
                "code": "en_GB"
            },
            "components": components
        }
    }

    response = requests.post(whatsapp_url, headers=headers, json=data)
    print(response.text)
    assert response.status_code == 200, "Failed to send message"

def send_text_message(message_text, to_phone_nr, merchant_id, preview_url=False):
    whatsapp_url, whatsapp_token, whatsapp_details = get_whatsapp_account_details(merchant_id)

    db_engine = jqutils.get_db_engine()

    query = text("""
        INSERT INTO publishing_whatsapp_message(merchant_id, whatsapp_account_id, message, from_phone_nr, to_phone_nr, message_status, meta_status)
        VALUES(:merchant_id, :whatsapp_account_id, :message, :from_phone_nr, :to_phone_nr, :message_status, :meta_status)
    """)
    with db_engine.connect() as conn:
        whatsapp_message_log = {
            "merchant_id": merchant_id,
            "whatsapp_account_id": whatsapp_details['whatsapp_account_id'],
            "message": message_text,
            "from_phone_nr": whatsapp_details['whatsapp_account_phone_nr'],
            "to_phone_nr": to_phone_nr,
            "message_status": "pending",
            "meta_status": "active"
        }
        publishing_whatsapp_message_id = conn.execute(query, whatsapp_message_log).lastrowid
        assert publishing_whatsapp_message_id, "Failed to create whatsapp message log"

    headers = {
        'Authorization': f'Bearer {whatsapp_token}',
        'Content-Type': 'application/json',
    }
    
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_phone_nr,
        "type": "text",
        "text": {
            "preview_url": preview_url,
            "body": message_text
        }
    }

    if os.getenv('MOCK_WHATSAPP') == "0":
        response = requests.post(whatsapp_url, headers=headers, json=data)
        if response.status_code != 200:
            query = text("""
                UPDATE publishing_whatsapp_message
                SET message_status = :message_status
                WHERE publishing_whatsapp_message_id = :publishing_whatsapp_message_id
            """)
            with db_engine.connect() as conn:
                result = conn.execute(query, message_status="failed", publishing_whatsapp_message_id=publishing_whatsapp_message_id).rowcount
                assert result, "Failed to update whatsapp message log"
            
            assert response.status_code == 200, "Failed to send whatsapp message"
    
    query = text("""
        UPDATE publishing_whatsapp_message
        SET message_status = :message_status
        WHERE publishing_whatsapp_message_id = :publishing_whatsapp_message_id
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, message_status="sent", publishing_whatsapp_message_id=publishing_whatsapp_message_id).rowcount
        assert result, "Failed to update whatsapp message log"

def send_message_with_button(template_name, to_phone_nr, message_list, image_url, discount_code):
    whatsapp_url = os.environ.get('WHATSAPP_API_URL')
    whatsapp_access_token = os.environ.get('WHATSAPP_TOKEN')

    headers = {
        'Authorization': f'Bearer {whatsapp_access_token}',
        'Content-Type': 'application/json',
    }

    components = []

    if image_url:
        components.append({
            "type": "header",
            "parameters": [
                {
                    "type": "image",
                    "image": {
                        "link": image_url
                    }
                }
            ]
        })

    body_param_list = []
    for one_message in message_list:
        body_param_list.append({
            "type": "text",
            "text": one_message
        })

    components.append({
        "type": "body",
        "parameters": body_param_list
    })

    if discount_code:
        components.append({
            "type": "button",
            "sub_type" : "url",
            "index": "0", 
            "parameters": [
                {
                    "type": "text",
                    "text": discount_code
                }
            ]
        })

        components.append({
            "type": "button",
            "sub_type": "quick_reply",
            "index": "1",
            "parameters": [
            {
                "type": "payload",
                "payload": "no"
            }
            ]
      })
    
    data = {
        "messaging_product": "whatsapp",
        "to": to_phone_nr,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {
                "code": "en_GB"
            },
            "components": components
        }
    }

    response = requests.post(whatsapp_url, headers=headers, json=data)
    assert response.status_code == 200, "Failed to send message"