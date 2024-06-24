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

def add_plan(brand_profile_id, plan_name, external_plan_id, menu_group_id_list, creation_user_id):
    db_engine = jqutils.get_db_engine()

    with db_engine.connect() as conn:
        query = text("""
            INSERT INTO plan (brand_profile_id, plan_name, external_plan_id, meta_status, creation_user_id)
            VALUES (:brand_profile_id, :plan_name, :external_plan_id, :meta_status, :creation_user_id)
        """)
        plan_id = conn.execute(query, brand_profile_id=brand_profile_id, plan_name=plan_name, external_plan_id=external_plan_id,
                meta_status="active", creation_user_id=creation_user_id).lastrowid
        assert plan_id, "unable to create plan"

        query_params = ""
        menu_group_id_list = list(set(menu_group_id_list))
        for menu_group_id in menu_group_id_list:
            query_params += f"({plan_id}, {menu_group_id}, 'active', {creation_user_id}),"
        
        if query_params:
            query_params = query_params[:-1]
            query = text(f"""
                INSERT INTO plan_menu_group_map (plan_id, menu_group_id, meta_status, creation_user_id)
                VALUES {query_params}
            """)
            result = conn.execute(query).rowcount
            assert result == len(menu_group_id_list), "unable to create plan_menu_group_map"
    
    return plan_id

def update_plan(plan_id, plan_name, external_plan_id, menu_group_id_list, creation_user_id):
    db_engine = jqutils.get_db_engine()
    
    with db_engine.connect() as conn:
        query = text("""
            SELECT plan_name, external_plan_id
            FROM plan
            WHERE plan_id = :plan_id
            AND meta_status = :meta_status
        """)
        result = conn.execute(query, plan_id=plan_id, meta_status="active").fetchone()
        assert result, f"plan_id: {plan_id} not found"
        
        if plan_name != result["plan_name"] or external_plan_id != result["external_plan_id"]:
            query = text("""
                UPDATE plan
                SET plan_name = :plan_name, external_plan_id = :external_plan_id, modification_user_id = :modification_user_id
                WHERE plan_id = :plan_id
            """)
            result = conn.execute(query, plan_name=plan_name, external_plan_id=external_plan_id,
                                    modification_user_id=creation_user_id, plan_id=plan_id).rowcount
            assert result, f"unable to update plan_id: {plan_id}"
    
        # get existing menu_group_id_list
        query = text("""
            SELECT menu_group_id
            FROM plan_menu_group_map
            WHERE plan_id = :plan_id
            AND meta_status = :meta_status
        """)
        result = conn.execute(query, plan_id=plan_id, meta_status="active").fetchall()
        existing_menu_group_id_list = [row["menu_group_id"] for row in result]
    
        # get menu_group_id_list to be added
        menu_group_id_list_to_add = list(set(menu_group_id_list) - set(existing_menu_group_id_list))
        if len(menu_group_id_list_to_add) > 0:
            query_params = ""
            for menu_group_id in menu_group_id_list_to_add:
                query_params += f"({plan_id}, {menu_group_id}, 'active', {creation_user_id}),"
            
            if query_params:
                query_params = query_params[:-1]
                query = text(f"""
                    INSERT INTO plan_menu_group_map (plan_id, menu_group_id, meta_status, creation_user_id)
                    VALUES {query_params}
                """)
                result = conn.execute(query).rowcount
                assert result == len(menu_group_id_list_to_add), "unable to create plan_menu_group_map"
        
        # get menu_group_id_list to be deleted
        menu_group_id_list_to_delete = list(set(existing_menu_group_id_list) - set(menu_group_id_list))
        if len(menu_group_id_list_to_delete) > 0:
            query = text(f"""
                UPDATE plan_menu_group_map
                SET meta_status = :meta_status, deletion_user_id = :deletion_user_id, deletion_timestamp = :deletion_timestamp
                WHERE plan_id = :plan_id
                AND menu_group_id IN :menu_group_id_list_to_delete
            """)
            result = conn.execute(query, meta_status='deleted', plan_id=plan_id, menu_group_id_list_to_delete=menu_group_id_list_to_delete,
                                    deletion_user_id=creation_user_id, deletion_timestamp=jqutils.get_utc_datetime()).rowcount
            assert result == len(menu_group_id_list_to_delete), "unable to delete menu_groups"