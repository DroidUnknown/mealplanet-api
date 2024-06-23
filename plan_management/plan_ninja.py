from utils import jqutils
from sqlalchemy import text

def check_plan_name_availability(plan_name, brand_profile_id, plan_id=None):
    plan_id_filter = ""
    if plan_id:
        plan_id_filter = "AND plan_id != :plan_id"

    db_engine = jqutils.get_db_engine()
    
    query = text(f"""
        SELECT plan_id
        FROM plan
        WHERE plan_name = :plan_name
        AND brand_profile_id = :brand_profile_id
        {plan_id_filter}
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, plan_name=plan_name, brand_profile_id=brand_profile_id, plan_id=plan_id, meta_status="active").fetchone()

    return 0 if result else 1