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

        token_info = keycloak_openid.decode_token(access_token, validate=False)
            
        user_roles = token_info['realm_access']['roles']
        
        if not user_roles:
            response_body = {
                'message': 'Login failed no user roles found',
                'acton': 'login',
                'status': 'failed'
            }
        else:
            response_body = {
                'data': {
                    'access_token': access_token,
                    'user_roles': user_roles
                },
                'status': 'successful',
                'action': 'login',
                'message': 'Login successful'
            }
    else:
        response_body = {
            'message': 'Login failed',
            'action': 'login',
            'status': 'failed'
        }
    
    return jsonify(response_body)