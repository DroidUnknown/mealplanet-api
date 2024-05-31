from sqlalchemy import text

from utils import jqutils

def check_plan_availability(external_plan_id):
    db_engine = jqutils.get_db_engine()

    query = text("""
        SELECT plan_id
        FROM plan
        WHERE external_plan_id = :external_plan_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, external_plan_id=external_plan_id, meta_status="active").fetchone()

    return 0 if result else 1