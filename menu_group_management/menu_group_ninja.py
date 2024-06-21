from utils import jqutils
from sqlalchemy import text

def check_menu_group_name_availability(menu_group_name, menu_group_id=None):
    menu_group_id_filter = ""
    if menu_group_id:
        menu_group_id_filter = "AND menu_group_id != :menu_group_id"

    db_engine = jqutils.get_db_engine()
    
    query = text(f"""
        SELECT menu_group_id
        FROM menu_group
        WHERE menu_group_name = :menu_group_name
        {menu_group_id_filter}
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, menu_group_name=menu_group_name, menu_group_id=menu_group_id, meta_status="active").fetchone()

    return 0 if result else 1