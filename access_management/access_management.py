import json
from flask import Blueprint, request, jsonify, g
from sqlalchemy import text

from utils import jqutils, keycloak_utils

access_management_blueprint = Blueprint('access_management', __name__)


@access_management_blueprint.route('/login', methods=['POST'])
def login():
    request_data = request.get_json()
    
    keycloak_openid = keycloak_utils.get_keycloak_client_openid()
    
    username = request_data["username"]
    password = request_data["password"]

    # Authenticate user with Keycloak
    try:
        token = keycloak_openid.token(username, password)
    except Exception as e:
        return jsonify({'error': str(e)}), 401

    # If authentication is successful, authorize user
    if token:
        # get user role from keycloak
        access_token = token['access_token']

        userinfo = keycloak_openid.userinfo(access_token)
        print(json.dumps(userinfo, indent=4))
        user_id = userinfo['sub']
        
        user_roles = keycloak_utils.get_user_roles(user_id)
        if not user_roles:
            response_body = {
                'message': 'Login failed'
            }
        else:
            response_body = {
                'message': 'Login successful',
                'access_token': token['access_token'],
                'user_roles': user_roles
            }
    else:
        response_body = {
            'message': 'Login failed'
        }
    
    return jsonify(response_body)