import os
import json
import logging

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from flask_mysqldb import MySQL
from flask import Flask, request
from flask_restful import Api
from dotenv import load_dotenv

from utils import jqaccess_control_engine

# ===============================================================================
# import API Blueprints
# ===============================================================================
from access_management.access_management import access_management_blueprint
from user_management.user_management import user_management_blueprint
from role_management.role_management import role_management_blueprint

# import Environment variables
load_dotenv(override=True)

# ===============================================================================
#  Flask App Configuration
# ===============================================================================
app = Flask(__name__, static_url_path='', static_folder='public')  # pylint: disable=invalid-name
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
app.register_blueprint(access_management_blueprint, url_prefix=base_api_url)
app.register_blueprint(user_management_blueprint, url_prefix=base_api_url)
app.register_blueprint(role_management_blueprint, url_prefix=base_api_url)

# ===============================================================================
# Gunicorn settings
# ===============================================================================
gunicorn_logger = logging.getLogger('gunicorn.error')  # pylint: disable=invalid-name
app.debug = os.environ.get('DEBUG')
app.logger.setLevel(logging.DEBUG)

# ===============================================================================
# Sentry settings
# ===============================================================================
if os.getenv("MYSQL_HOST") != "127.0.0.1" and os.environ.get('SENTRY_DSN'):
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        integrations=[FlaskIntegration()],
        traces_sample_rate=os.getenv("SENTRY_TRACES_SAMPLE", 1.0),
        sample_rate=os.getenv("SENTRY_TRACES_SAMPLE", 1.0),
        environment=os.getenv('ENV')
    )

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

    # Check Tag Exists
    if 'uuid' in request.headers.keys():
        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("uuid", request.headers['uuid'])

    if request.method == 'OPTIONS':
        return

    app.logger.debug('-' * 100)
    app.logger.debug('REQUEST Url: %s', f'{request.method}: {request.url}')
    app.logger.debug('REQUEST Headers: %s', json.dumps(request.headers, default=str))
    app.logger.debug('REQUEST Body: %s', request.data)

    if request.path.startswith('/api/') and request.url_rule:
        return

# ====================================================================================
# after_request(): function which runs after every request is returned from blueprint
# ====================================================================================
@app.after_request
def after_request(response):
    if request.path.startswith('/api/'):
        if app.debug and not request.path.startswith('/api/payment-api/hello'):
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
