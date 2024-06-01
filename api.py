import os
import json
import logging

from flask_mysqldb import MySQL
from flask import Flask, request, g
from flask_restful import Api
from dotenv import load_dotenv

from utils import json_encoder

# ===============================================================================
# import API Blueprints
# ===============================================================================
from brand_profile_management.brand_profile_management import brand_profile_management_blueprint
from plan_management.plan_management import plan_management_blueprint
from delivery_provider_profile_management.delivery_provider_profile_management import delivery_provider_profile_management_blueprint
from kitchen_profile_management.kitchen_profile_management import kitchen_profile_management_blueprint

# import Environment variables
load_dotenv(override=True)

# ===============================================================================
#  Flask App Configuration
# ===============================================================================
app = Flask(__name__, static_url_path='', static_folder='public')  # pylint: disable=invalid-name
app.json_encoder = json_encoder.JQJSONEncoder
base_api_url = "/api"

# ===============================================================================
# Environment-specific configurations can be done here
# ===============================================================================
if os.environ.get('ENV') == 'development':
    print("Starting application in Development mode...")
    # any config ...
elif os.environ.get('ENV') == 'production':
    print("Starting application in Production mode...")
    # any config ...

# ===============================================================================
# API blueprints registration
# ===============================================================================
app.register_blueprint(brand_profile_management_blueprint, url_prefix=base_api_url)
app.register_blueprint(plan_management_blueprint, url_prefix=base_api_url)
app.register_blueprint(delivery_provider_profile_management_blueprint, url_prefix=base_api_url)
app.register_blueprint(kitchen_profile_management_blueprint, url_prefix=base_api_url)

# ===============================================================================
# Gunicorn settings
# ===============================================================================
gunicorn_logger = logging.getLogger('gunicorn.error')  # pylint: disable=invalid-name
app.debug = os.environ.get('DEBUG')
app.logger.setLevel(logging.DEBUG)

# ===============================================================================
# Redis settings
# ===============================================================================
try:
    # app.redis_con = StrictRedis(
    # host=os.getenv('REDIS_HOST'),
    # port=os.getenv('REDIS_PORT')
    app.redis_con.ping()
except Exception:  # pylint: disable=broad-except
    app.redis_con = None

# ===============================================================================
# MySQL settings
# ===============================================================================
app.sql = MySQL(app)

# ===============================================================================
# before_request(): function which runs before every request is routed to blueprint
# ===============================================================================
@app.before_request
def before_request():
    if request.method == 'OPTIONS':
        return

    app.logger.debug('-' * 100)
    app.logger.debug('REQUEST Url: %s', f'{request.method}: {request.url}')
    app.logger.debug('REQUEST Headers: %s', json.dumps(request.headers, default=str))
    app.logger.debug('REQUEST Body: %s', request.data)


    if request.path.startswith('/api/') and request.url_rule:
        g.user_id = 1
        g.tenant_id = 1
        return

# ====================================================================================
# after_request(): function which runs after every request is returned from blueprint
# ====================================================================================
@app.after_request
def after_request(response):
    if request.path.startswith('/api/'):
        if app.debug and not request.path.startswith('/api/healthcheck'):
            # print("PRINT => IN-DEBUG")
            # print("response.data => ",response.data)
            # response.headers.add('Content-Type', 'application/json')
            #response.headers.add('Access-Control-Allow-Origin', '*')
            #response.headers.add('Access-Control-Allow-Headers', 'Content-Type, X-Access-Token, X-User-ID')
            #response.headers.add('Access-Control-Expose-Headers', 'Content-Type, Content-Length, X-Access-Token, X-User-ID')
            # app.logger.debug('RESPONSE Headers: %s', response.headers)
            # app.logger.debug('RESPONSE Body: %s', response.data)
            app.logger.debug('RESPONSE Status: %s %s', response.status_code, response.status)
            app.logger.debug('-' * 100)

    return response

# ===============================================================================
# Override default error handler
# ===============================================================================
class ExtendApi(Api):
    """
    This class overrides 'handle_error' method of 'Api' class ,
    to extend global exception handing functionality of 'flask-restful'.
    """

    def handle_error(self, e):
        # reraise the error so that it is handled in the app level error handlers
        # Add custom handlers below if required
        if getattr(e, "code"):
            if e.code == 404:
                return {"message": "Not Found"}, 404
        raise e

# ===============================================================================
# Flask register app and start
# ===============================================================================
api = ExtendApi(app, catch_all_404s=True)  # pylint: disable=invalid-name

if __name__ == '__main__':
    app.run(debug=app.debug, port=8000, host='0.0.0.0')
