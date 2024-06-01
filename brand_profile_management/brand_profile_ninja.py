from sqlalchemy import text

from utils import jqutils

def check_brand_profile_availability(external_brand_profile_id, brand_profile_id=None):
    db_engine = jqutils.get_db_engine()

    brand_profile_id_filter = ""
    if brand_profile_id:
        brand_profile_id_filter = "AND brand_profile_id != :brand_profile_id"
    query = text(f"""
        SELECT brand_profile_id
        FROM brand_profile
        WHERE external_brand_profile_id = :external_brand_profile_id
        {brand_profile_id_filter}
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, external_brand_profile_id=external_brand_profile_id, brand_profile_id=brand_profile_id, meta_status="active").fetchone()

    return 0 if result else 1