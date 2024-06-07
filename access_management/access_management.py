import json
import traceback
import logging

from flask import Blueprint, request, jsonify
from utils import keycloak_utils

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger.setLevel(logging.INFO)

access_management_blueprint = Blueprint('access_management', __name__)

@access_management_blueprint.route('/login', methods=['POST'])
def login():
    request_json = request.get_json()
    
    username = request_json["username"]
    password = request_json["password"]
    
    keycloak_client_openid = keycloak_utils.get_keycloak_client_openid()

    # Authenticate user with Keycloak
    try:
        token = keycloak_client_openid.token(username, password)
        
        try:
            permissions = keycloak_client_openid.uma_permissions(token["access_token"])
        except Exception as e:
            permissions = []
        
        return jsonify({
            'data': {
                'access_token': token['access_token'],
                'expires_in': token['expires_in'],
                'refresh_token': token['refresh_token'],
                'refresh_expires_in': token['refresh_expires_in'],
                'permissions': permissions,
            },
            'status': 'successful',
            'action': 'login',
        })
 
    except Exception as e:
        logger.error(traceback.format_exc(e))
        return jsonify({
            'message': 'Invalid username or password',
            'status': 'failed',
            'action': 'login'
        }, 401)
    
@access_management_blueprint.route('/refresh', methods=['POST'])
def refresh():
    request_json = request.get_json()
    
    refresh_token = request_json["refresh_token"]
    
    keycloak_client_openid = keycloak_utils.get_keycloak_client_openid()
    
    # Refresh token with Keycloak
    try:
        token = keycloak_client_openid.refresh_token(refresh_token)
        try:
            permissions = keycloak_client_openid.uma_permissions(token["access_token"])
        except Exception as e:
            permissions = []
        
        return jsonify({
            'data': {
                'access_token': token['access_token'],
                'expires_in': token['expires_in'],
                'refresh_token': token['refresh_token'],
                'refresh_expires_in': token['refresh_expires_in'],
                'permissions': permissions,
            },
            'action': 'refresh',
            'status': 'successful',
        })
        
    except Exception as e:
        logger.error(traceback.format_exc(e))
        return jsonify({
            'message': 'Invalid refresh token',
            'action': 'refresh',
            'status': 'failed'
        }, 401)
    
    
@access_management_blueprint.route('/logout', methods=['POST'])
def logout():
    request_json = request.get_json()
    
    refresh_token = request_json["refresh_token"]
    
    keycloak_client_openid = keycloak_utils.get_keycloak_client_openid()
    
    # Logout user with Keycloak
    try:
        keycloak_client_openid.logout(refresh_token)
        
        return jsonify({
            'data': {},
            'action': 'logout',
            'status': 'successful'
        })
        
    except Exception as e:
        logger.error(traceback.format_exc(e))
        return jsonify({
            'message': 'Invalid refresh token',
            'action': 'logout',
            'status': 'failed'
        }, 401)
    
    