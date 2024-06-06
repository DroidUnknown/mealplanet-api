import json
import requests
import os
import traceback
import logging

from flask import Blueprint, request, jsonify, g
from sqlalchemy import text

from utils import jqutils, keycloak_utils

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger.setLevel(logging.INFO)

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
        access_token = token['access_token']
        refresh_token = token['refresh_token']
        rpt_token = keycloak_utils.get_rpt_token(keycloak_openid)
        assert rpt_token, 'Unable to get RPT token'
        
        return jsonify({
            'data': {
                'access_token': access_token,
                'rpt_token': rpt_token,
                'refresh_token': refresh_token,
            },
            'status': 'successful',
            'action': 'login',
        })
 
    except Exception as e:
        logger.error(traceback.format_exc())
        return jsonify({
            'message': 'Invalid username or password',
            'action': 'login',
            'status': 'failed'
        })
    
    