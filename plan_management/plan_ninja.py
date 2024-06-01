from sqlalchemy import text

from utils import jqutils
from menu_group_management import menu_group_ninja

def check_plan_availability(external_plan_id, plan_id=None):
    db_engine = jqutils.get_db_engine()

    plan_id_filter = ""
    if plan_id:
        plan_id_filter = "AND plan_id != :plan_id"
    query = text(f"""
        SELECT plan_id
        FROM plan
        WHERE external_plan_id = :external_plan_id
        {plan_id_filter}
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, external_plan_id=external_plan_id, plan_id=plan_id, meta_status="active").fetchone()

    return 0 if result else 1

def add_plans(brand_profile_id, plan_list, creation_user_id):
    dict_list = []
    plan_menu_group_map = {}
    for request_data in plan_list:
        external_plan_id = request_data["external_plan_id"]
        plan_name = request_data["plan_name"]
        menu_group_id_list = request_data.get("menu_group_id_list", [])
        plan_menu_group_map[external_plan_id] = menu_group_id_list

        availability_p = check_plan_availability(external_plan_id)
        if availability_p == 0:
            return False, f"External Plan ID {external_plan_id} already exists"

        dict_list.append({
            "external_plan_id": external_plan_id,
            "plan_name": plan_name,
            "brand_profile_id": brand_profile_id,
            "meta_status": "active",
            "creation_user_id": creation_user_id
        })

    plan_id_list = []
    db_engine = jqutils.get_db_engine()

    query = text("""
        INSERT INTO PLAN (external_plan_id, plan_name, brand_profile_id, meta_status, creation_user_id)
        VALUES (:external_plan_id, :plan_name, :brand_profile_id, :meta_status, :creation_user_id)
    """)

    with db_engine.connect() as conn:
        for row in dict_list:
            stmt = query.bindparams(**row)
            plan_id = conn.execute(stmt).lastrowid
            plan_id_list.append(plan_id)

    query = text("""
        SELECT plan_id, external_plan_id
        FROM plan
        WHERE plan_id IN :plan_id_list
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, plan_id_list=plan_id_list).fetchall()

    plan_menu_group_map = {row["external_plan_id"]: plan_menu_group_map[row["external_plan_id"]] for row in result}
    menu_group_ninja.add_menu_group_map(plan_menu_group_map, creation_user_id)

    return True, plan_id_list

def get_plan_list_by_brand_profile(brand_profile_id):
    db_engine = jqutils.get_db_engine()

    query = text("""
        SELECT plan_id, external_plan_id, brand_profile_id, plan_name
        FROM plan
        WHERE brand_profile_id = :brand_profile_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, brand_profile_id=brand_profile_id, meta_status="active").fetchall()

    plan_id_list = [row['plan_id'] for row in result]
    menu_group_list_map = menu_group_ninja.get_menu_group_list_map_by_plan_list(plan_id_list)

    plan_list = []
    for row in result:
        plan_dict = dict(row)
        plan_dict["menu_group_list"] = menu_group_list_map.get(plan_dict["plan_id"], [])
        plan_list.append(plan_dict)

    return plan_list

def delete_plans_by_brand_profile(brand_profile_id):
    db_engine = jqutils.get_db_engine()

    query = text("""
        SELECT plan_id
        FROM plan
        WHERE brand_profile_id = :brand_profile_id
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, brand_profile_id=brand_profile_id).fetchall()
        plan_id_list = [row["plan_id"] for row in result]

    query = text("""
        UPDATE plan
        SET meta_status = :meta_status
        WHERE plan_id IN :plan_id_list
    """)
    with db_engine.connect() as conn:
        conn.execute(query, meta_status="deleted", plan_id_list=plan_id_list)

    menu_group_ninja.delete_menu_group_map_by_plan_list(plan_id_list)