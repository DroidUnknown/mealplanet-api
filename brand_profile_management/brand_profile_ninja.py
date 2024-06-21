from utils import jqutils
from sqlalchemy import text

def check_brand_profile_name_availability(brand_profile_name, brand_profile_id=None):
    brand_profile_id_filter = ""
    if brand_profile_id:
        brand_profile_id_filter = "AND brand_profile_id != :brand_profile_id"
    
    db_engine = jqutils.get_db_engine()
    
    query = text(f"""
        SELECT brand_profile_id
        FROM brand_profile
        WHERE brand_profile_name = :brand_profile_name
        {brand_profile_id_filter}
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, brand_profile_name=brand_profile_name, brand_profile_id=brand_profile_id, meta_status="active").fetchone()

    return False if result else True

def get_brand_profile_plan_list(brand_profile_id, menu_group_info_p=False):    
    db_engine = jqutils.get_db_engine()
    
    # get plans associated with brand_profile
    query = text("""
        SELECT plan_id, plan_name, external_plan_id
        FROM plan
        WHERE brand_profile_id = :brand_profile_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        results = conn.execute(query, brand_profile_id=brand_profile_id, meta_status="active").fetchall()
        plan_list = [dict(row) for row in results]
        
        if len(plan_list) and menu_group_info_p:
            plan_id_list = [one_plan["plan_id"] for one_plan in plan_list]
            
            # get menu groups associated with plans
            query = text("""
                SELECT pmgm.plan_id, mg.menu_group_id, mg.menu_group_name, mg.external_menu_group_id
                FROM (
                    SELECT plan_id, menu_group_id
                    FROM plan_menu_group_map
                    WHERE plan_id IN :plan_id_list
                    AND meta_status = :meta_status
                ) pmgm
                JOIN menu_group mg ON pmgm.menu_group_id = mg.menu_group_id
                WHERE mg.meta_status = :meta_status
            """)
            results = conn.execute(query, plan_id_list=plan_id_list, meta_status="active").fetchall()
            
            plan_id_menu_group_map = {}
            for one_result in results:
                plan_id = one_result["plan_id"]
                
                if plan_id not in plan_id_menu_group_map:
                    plan_id_menu_group_map[plan_id] = []
                
                plan_id_menu_group_map[plan_id].append({
                    "menu_group_id": one_result["menu_group_id"],
                    "menu_group_name": one_result["menu_group_name"],
                    "external_menu_group_id": one_result["external_menu_group_id"]
                })
            
            for one_plan in plan_list:
                one_plan["menu_group_list"] = plan_id_menu_group_map.get(one_plan["plan_id"], [])

    return plan_list