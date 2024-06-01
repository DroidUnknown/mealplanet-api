
from sqlalchemy import text

from utils import jqutils

def get_menu_group_list_map_by_plan_list(plan_id_list):
    db_engine = jqutils.get_db_engine()

    query = text("""
        SELECT pmgm.plan_id, pmgm.menu_group_id, mg.menu_group_name
        FROM plan_menu_group_map pmgm
        JOIN menu_group mg ON pmgm.menu_group_id = mg.menu_group_id
        WHERE plan_id IN :plan_id_list
        AND pmgm.meta_status = :meta_status
        AND mg.meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, plan_id_list=plan_id_list, meta_status="active").fetchall()

    menu_group_list_map = {}
    for row in result:
        if row["plan_id"] not in menu_group_list_map:
            menu_group_list_map[row["plan_id"]] = []
        menu_group_list_map[row["plan_id"]].append(dict(row))

    return menu_group_list_map

def delete_menu_group_map_by_plan_list(plan_id_list):
    db_engine = jqutils.get_db_engine()

    query = text("""
        UPDATE plan_menu_group_map
        SET meta_status = :meta_status
        WHERE plan_id IN :plan_id_list
    """)
    with db_engine.connect() as conn:
        conn.execute(query, plan_id_list=plan_id_list, meta_status="deleted")

def add_menu_group_map(plan_menu_group_map, creation_user_id):
    db_engine = jqutils.get_db_engine()

    query = text("""
        INSERT INTO plan_menu_group_map (plan_id, menu_group_id, creation_user_id, meta_status)
        VALUES (:plan_id, :menu_group_id, :creation_user_id, :meta_status)
    """)
    with db_engine.connect() as conn:
        for plan_id, menu_group_id_list in plan_menu_group_map.items():
            for menu_group_id in menu_group_id_list:
                stmt = query.bindparams(plan_id=plan_id, menu_group_id=menu_group_id, creation_user_id=creation_user_id, meta_status="active")
                conn.execute(stmt)