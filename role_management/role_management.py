import json

from flask import Response, Blueprint, g
from sqlalchemy.sql import text

from utils import jqutils

role_management_blueprint = Blueprint('role_management_blueprint', __name__)

# GET ASSIGNABLE ROLES
@role_management_blueprint.route('/assignable-roles', methods=['GET'])
def get_assignable_roles():
    db_engine = jqutils.get_db_engine()

    role_id = g.role_id

    query = text("""
        SELECT ar.role_id, ar.role_name, ar.role_description
        FROM role_assignable_role_permission_map rarpm
        JOIN role ar on ar.role_id = rarpm.assignable_role_id
        WHERE rarpm.role_id = :role_id
        AND rarpm.permission = :permission
        AND rarpm.meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        results = conn.execute(query, role_id=role_id, permission=1, meta_status='active').fetchall()
        role_list = [dict(row) for row in results]
    
    response = Response(content_type='application/json')
    response_body = {
        "role_list": role_list,
        "action": "get_assignable_roles",
        "status": "successful",
    }
    response.data = json.dumps(response_body)
    return response