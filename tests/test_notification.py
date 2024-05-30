import json

from notification_management import notification_ninja
from tests import test_user

base_api_url = "/api"

def do_login(client, username, password):
    """
    Login
    """
    request_url = f'{base_api_url}/login'
    payload = {
        "username": username,
        "password": password
    }
    response = client.post(request_url, json=payload)
    return response



def do_get_notifications(client, headers, page_number = None, page_size = None, read_p = None):
    """
    Get Notifications
    """
    url = f'{base_api_url}/notifications?'
    if page_number:
        url += f'page_number={page_number}'
    if page_size:
        url += f'&page_size={page_size}'
    if read_p is not None:
        url += f'&read_p={read_p}'
    
    response = client.get(url, headers=headers)
    return response

def do_update_notification_status(client, headers, payload):
    """
    Update Notification
    """
    response = client.put(f'{base_api_url}/notification/status', json=payload, headers=headers)
    return response


def test_e2e_notification_flow(client, headers, user_headers):
    
    response = do_login(client, "admin", "alburaaq424")
    assert response.status_code == 200
    response = do_login(client, "company-x", "123456")
    assert response.status_code == 200
    
    total_notifications = 5
    page_size = 2
    
    merchant_id = 1
    notification_type_name = "warning"
    title = "Test Warning"
    body = "This is a test warning"
    metadata = {"test": "test"}
    
    # Generate  Notification For All Users of merchant_id: 1, Total Notifications times
    for i in range(total_notifications):
        notification_ninja.generate_notification(title, body, notification_type_name, merchant_id, metadata=metadata)
        
    # Make Sure Admin User received all notifications
    response = do_get_notifications(client, headers, page_number=1, page_size=page_size)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data["status"] == "successful"
    assert response_data["action"] == "get_notifications"
    notification_list = response_data["data"]["notification_list"]
    assert response_data["data"]["total_count"] == total_notifications
    assert response_data["data"]["unread_count"] == total_notifications
    assert len(notification_list) == page_size
    
    # make sure 2nd page of notifications does not return total_count and unread_count 
    response = do_get_notifications(client, headers, page_number=2, page_size=page_size)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data["status"] == "successful"
    assert response_data["action"] == "get_notifications"
    notification_list = response_data["data"]["notification_list"]
    assert response_data["data"]["total_count"] == None
    assert response_data["data"]["unread_count"] == None
    assert len(notification_list) == page_size
    
    user_id = headers["X-User-Id"]
    access_token = headers["X-Access-Token"]
    
    
    # Make sure the unread_count shown in the current user is correct
    response = test_user.do_get_current_user(client, access_token, user_id)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data["status"] == "successful"
    assert response_data["action"] == "get_current_user"
    assert response_data["notification_unread_count"] == total_notifications
    
    # Mark all notifications on page 2 as read
    notification_id_list = [notification["notification_id"] for notification in notification_list]
    total_unread = total_notifications - len(notification_id_list)
    
    payload = {
        "notification_id_list": notification_id_list,
        "read_p": 1
    }
    
    response = do_update_notification_status(client, headers, payload)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data["status"] == "successful"
    assert response_data["action"] == "update_notification_status"
    assert response_data["data"]["unread_count"] == total_unread
    
    # Make sure total unread_count is updated for admin user
    response = do_get_notifications(client, headers, page_number=1, page_size=page_size)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data["status"] == "successful"
    assert response_data["action"] == "get_notifications"
    notification_list = response_data["data"]["notification_list"]
    assert response_data["data"]["total_count"] == total_notifications
    assert response_data["data"]["unread_count"] == total_unread
    assert len(notification_list) == page_size
    
    # get only read notifications for admin user
    response = do_get_notifications(client, headers, page_number=1, page_size=page_size, read_p=1)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data["status"] == "successful"
    assert response_data["action"] == "get_notifications"
    notification_list = response_data["data"]["notification_list"]
    assert response_data["data"]["total_count"] == total_notifications - total_unread
    assert response_data["data"]["unread_count"] == total_unread
    assert len(notification_list) == page_size
    
    # make sure unread_count is updated for admin user
    response = test_user.do_get_current_user(client, access_token, user_id)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data["status"] == "successful"
    assert response_data["action"] == "get_current_user"
    assert response_data["notification_unread_count"] == total_unread
    
    # make sure the merchant user has received all the notifications as well
    response = do_get_notifications(client, user_headers, page_number=1, page_size=page_size)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data["status"] == "successful"
    assert response_data["action"] == "get_notifications"
    notification_list = response_data["data"]["notification_list"]
    assert response_data["data"]["total_count"] == total_notifications
    assert response_data["data"]["unread_count"] == total_notifications
    assert len(notification_list) == page_size
    
    # make sure the merchant user unread_count is correct
    user_id = user_headers["X-User-Id"]
    access_token = user_headers["X-Access-Token"]
    
    response = test_user.do_get_current_user(client, access_token, user_id)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data["status"] == "successful"
    assert response_data["action"] == "get_current_user"
    assert response_data["notification_unread_count"] == total_notifications
    
    merchant_id = 1
    role_id = 2
    notification_type_name = "success"
    title = f"Test Notification only to role_id: {role_id}"
    body = "This is a test success"
    
    # Generate notification only intended for role_id: 2 i.e merchant
    notification_ninja.generate_notification(title, body, notification_type_name, merchant_id, role_id = role_id)
    
    # make sure the merchant user has received the new notification
    response = do_get_notifications(client, user_headers, page_number=1, page_size=page_size)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data["status"] == "successful"
    assert response_data["action"] == "get_notifications"
    notification_list = response_data["data"]["notification_list"]
    assert response_data["data"]["total_count"] == total_notifications + 1
    assert response_data["data"]["unread_count"] == total_notifications + 1
    assert len(notification_list) == page_size
    
    # make sure the merchant user unread_count is updated and correct
    response = test_user.do_get_current_user(client, access_token, user_id)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data["status"] == "successful"
    assert response_data["action"] == "get_current_user"
    assert response_data["notification_unread_count"] == total_notifications + 1
    
    # make sure the admin user has not received the new notification
    response = do_get_notifications(client, headers, page_number=1, page_size=page_size)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data["status"] == "successful"
    assert response_data["action"] == "get_notifications"
    notification_list = response_data["data"]["notification_list"]
    assert response_data["data"]["total_count"] == total_notifications
    assert response_data["data"]["unread_count"] == total_unread
    assert len(notification_list) == page_size
    
    merchant_id = 1
    user_id = 1
    notification_type_name = "success"
    title = f"Test Notification only to user_id:  {user_id}"
    body = "This is a test success"
    
    # generate notification only intended for user_id: 1 i.e admin
    notification_ninja.generate_notification(title, body, notification_type_name, merchant_id, user_id = user_id)
    
    # make sure the admin user has received the new notification and is unread
    response = do_get_notifications(client, headers, page_number=1, page_size=page_size, read_p=0)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data["status"] == "successful"
    assert response_data["action"] == "get_notifications"
    notification_list = response_data["data"]["notification_list"]
    assert response_data["data"]["total_count"] == total_unread + 1
    assert response_data["data"]["unread_count"] == total_unread + 1
    assert len(notification_list) == page_size
    
    user_id = headers["X-User-Id"]
    access_token = headers["X-Access-Token"]
    
    # make sure the admin user unread_count is updated and correct
    response = test_user.do_get_current_user(client, access_token, user_id)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data["status"] == "successful"
    assert response_data["action"] == "get_current_user"
    assert response_data["notification_unread_count"] == total_unread + 1
    
    # make sure the merchant user has not received the new notification
    response = do_get_notifications(client, user_headers, page_number=1, page_size=page_size)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data["status"] == "successful"
    assert response_data["action"] == "get_notifications"
    notification_list = response_data["data"]["notification_list"]
    assert response_data["data"]["total_count"] == total_notifications + 1
    assert response_data["data"]["unread_count"] == total_notifications + 1
    assert len(notification_list) == page_size
    