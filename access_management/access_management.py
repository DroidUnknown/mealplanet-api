import json
import requests
import os
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

    if token:
        access_token = token['access_token']
        
        token_info = keycloak_openid.decode_token(access_token)
        with open('token_info.json', 'w') as f:
            json.dump(token_info, f)
        user_roles = token_info['realm_access']['roles']
        user_id = token_info['sub']
        
        rpt = keycloak_openid.token(grant_type='urn:ietf:params:oauth:grant-type:uma-ticket',audience='Istio')
        rpt_token = rpt['access_token']
        rpt_token_info = keycloak_openid.decode_token(rpt_token)
        
        
        if not rpt_token_info:
            response_body = {
                'message': 'Login failed no user roles found',
                'acton': 'login',
                'status': 'failed'
            }
        else:
            response_body = {
                'data': {
                    'access_token': access_token,
                    'rpt_token': rpt_token,
                    'user_id': user_id,
                    'rpt_token_info': rpt_token_info,
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