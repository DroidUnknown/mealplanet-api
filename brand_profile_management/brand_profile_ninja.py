from utils import jqutils
from sqlalchemy import text

def check_brand_profile_availability(brand_profile_name, brand_profile_id=None):
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
    plan_list = []
    
    db_engine = jqutils.get_db_engine()
    
    # get plans associated with brand_profile
    query = text("""
        SELECT bppm.brand_profile_plan_map_id, p.plan_id, p.plan_name, p.external_plan_id
        FROM (
            SELECT brand_profile_plan_map_id, plan_id
            FROM brand_profile_plan_map
            WHERE brand_profile_id = :brand_profile_id
            AND meta_status = :meta_status
        ) bppm
        JOIN plan p ON bppm.plan_id = p.plan_id
    """)
    with db_engine.connect() as conn:
        results = conn.execute(query, brand_profile_id=brand_profile_id, meta_status="active").fetchall()
    
        brand_profile_plan_map_id_index_map = {}
        for idx, one_result in enumerate(results):
            brand_profile_plan_map_id = one_result["brand_profile_plan_map_id"]
            
            one_plan_map_dict = {
                "brand_profile_plan_map_id": brand_profile_plan_map_id,
                "plan": {
                    "plan_id": one_result["plan_id"],
                    "plan_name": one_result["plan_name"],
                    "external_plan_id": one_result["external_plan_id"],
                }
            }
            if menu_group_info_p:
                one_plan_map_dict["menu_group_list"] = []
            
            plan_list.append(one_plan_map_dict)
            brand_profile_plan_map_id_index_map[brand_profile_plan_map_id] = idx
        
        if len(brand_profile_plan_map_id_index_map) and menu_group_info_p:
            # get menu groups associated with plans
            query = text("""
                SELECT bppmgm.brand_profile_plan_menu_group_map_id, bppmgm.brand_profile_plan_map_id, bppmgm.menu_group_id, mg.menu_group_name
                FROM (
                    SELECT brand_profile_plan_menu_group_map_id, brand_profile_plan_map_id, menu_group_id
                    FROM brand_profile_plan_menu_group_map
                    WHERE brand_profile_plan_map_id IN :brand_profile_plan_map_id_list
                    AND meta_status = :meta_status
                ) bppmgm
                JOIN menu_group mg ON bppmgm.menu_group_id = mg.menu_group_id
            """)
            results = conn.execute(query, brand_profile_plan_map_id_list=list(brand_profile_plan_map_id_index_map.keys()), meta_status="active").fetchall()
            
            for one_result in results:
                idx = brand_profile_plan_map_id_index_map[one_result["brand_profile_plan_map_id"]]
                plan_list[idx]["menu_group_list"].append({
                    "brand_profile_plan_menu_group_map_id": one_result["brand_profile_plan_menu_group_map_id"],
                    "menu_group": {
                        "menu_group_id": one_result["menu_group_id"],
                        "menu_group_name": one_result["menu_group_name"]
                    }
                })

    return plan_list