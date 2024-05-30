from sqlalchemy import Column, DateTime, Integer, JSON, Numeric, SmallInteger, String
from sqlalchemy.schema import FetchedValue
from sqlalchemy.ext.declarative import declarative_base
import urllib.parse
import sqlalchemy
from sqlalchemy import create_engine, text
import random
import string
import os
import json
from utils import jqutils

from flask import Flask, request, g

def create_search_query(table_name, input_list, output_fields_list, ignore_deleted_records_p=True):
    select_str = """select """
    from_str = """ from """ + table_name
    where_str = """ where """
    limit_str = """ limit """
    pk_id = table_name.strip()+'_id'
    # order_by_str = """ order by modification_timestamp desc"""
    # limit_value = g.resource.pagination_max_limit
    pagination_action = 0
    limit_value = g.pagination_max_limit
    filter_list = []
    limit_action = 0
    where_action = 0
    after_timestamp_exists_p = 0
    after_id_exists_p = 0
    before_timestamp_exists_p = 0
    before_id_exists_p = 0
    del_status = ""

    limit_value = g.pagination_max_limit

    for k, v in input_list.items():
        if(k=='before_timestamp' ):
            if(v.strip()=="first"):
                pagination_action = 0
            else:
                pagination_action = 1
                before_timestamp_exists_p = 1           
                before_timestamp = v

        if(k=='before_id'):
            pagination_action = 1
            before_id_exists_p = 1
            before_id = v
        
            
        if(k=='limit'):
            limit_action = 1
            if(int(v) > g.pagination_max_limit):
                limit_value = g.pagination_max_limit
            else:
                limit_value = v   
# JQ adding some sauce here
        if(k=='after_timestamp'):
            after_timestamp_exists_p = 1
            after_timestamp = v

        if(k=='after_id'):
            after_id_exists_p = 1
            after_id = v

        if(k!='before_timestamp' and k!='limit' and k!='after_timestamp' and  k!='after_id' and  k!='before_id'):
            where_action = 1
            filter_list.append(f"{k} {v}")

    select_str = select_str + ", ".join(output_fields_list)

    where_str = where_str  + " and ".join(filter_list)
    ignore_delete_str = " meta_status != 'deleted' "


    if(where_action and ignore_deleted_records_p):
        query = select_str + from_str + where_str + " and " + ignore_delete_str
    elif(where_action and not ignore_deleted_records_p):
        query = select_str + from_str + where_str
    elif(ignore_deleted_records_p and not where_action):
        where_action = 1
        query = select_str + from_str + where_str + ignore_delete_str
    else:
        query = select_str + from_str


    if(pagination_action):
        d = {
        "before_timestamp" : before_timestamp_exists_p, 
        "before_id" : before_id_exists_p,
        "after_timestamp" : after_timestamp_exists_p, 
        "after_id" : after_id_exists_p
        }

        error_field_dict = {}
        error_p = 0
        for k, v in d.items():
            if(not v):
                error_field_dict[k] = v
                error_p = 1

        if(error_p):
            assert not error_field_dict, "Invalid Pagination Input Parameters"
        

    if(pagination_action and where_action):
        #query = query + " and (modification_timestamp > '" + after_timestamp + "' or modification_timestamp < '" + before_timestamp + "')"
        query = query +  f""" and (((modification_timestamp > '{after_timestamp}') or (modification_timestamp = '{after_timestamp}' and {pk_id} > '{after_id}') )
                               or ((modification_timestamp < '{before_timestamp}') or (modification_timestamp = '{before_timestamp}' and {pk_id} < '{before_id}'))) """
    elif(pagination_action):
        #query = query +  " where (modification_timestamp > '" + after_timestamp + "' or modification_timestamp < '" + before_timestamp + "')"
        query = query +   f""" where  ((modification_timestamp > '{after_timestamp}') or (modification_timestamp = '{after_timestamp}' and {pk_id} > '{after_id}'))
                               or ((modification_timestamp < '{before_timestamp}') or (modification_timestamp = '{before_timestamp}' and {pk_id} < '{before_id}')) """

    # Apply order by
    # query = query + f""" order by modification_timestamp desc, {pk_id} desc"""
    # Apply LIMIT
    query = query + """ limit """ + str(limit_value)
    return query 

# Joined Query Search
def create_joining_search_query(
        table_name, joining_condition, input_list, output_fields_list, ignore_deleted_records_p=True, meta_status="meta_status"):
    select_str = """select """
    where_str = f""" where  {joining_condition} """
    limit_str = """ limit """
    pk_id = table_name.split(',')[0] + "." + table_name.split(',')[0] + '_id'
    joining = table_name
    from_str = """ from """ + joining

    # limit_value = g.resource.pagination_max_limit
    pagination_action = 0
    limit_value = g.pagination_max_limit
    filter_list = []
    limit_action = 0
    after_timestamp_exists_p = 0
    after_id_exists_p = 0
    before_timestamp_exists_p = 0
    before_id_exists_p = 0
    del_status = ""

    for k, v in input_list.items():
        if(k == 'before_timestamp'):
            # print(f"the VALUE OF BEFORE_TIMESTAMP is: ", v)
            if(v.strip() == "first"):
                pagination_action = 0
            else:
                pagination_action = 1
                before_timestamp_exists_p = 1
                before_timestamp = v

        if(k == 'before_id'):
            # print(f"the VALUE OF BEFORE_ID is: ", v)
            pagination_action = 1
            before_id_exists_p = 1
            before_id = v

        if(k == 'limit'):
            limit_action = 1
            if(int(v) > g.pagination_max_limit):
                limit_value = g.pagination_max_limit
            else:
                limit_value = v
            # JQ adding some sauce here
        if(k == 'after_timestamp'):
            after_timestamp_exists_p = 1
            after_timestamp = v

        if(k == 'after_id'):
            after_id_exists_p = 1
            after_id = v

        if(k != 'before_timestamp' and k != 'limit' and k != 'after_timestamp' and k != 'after_id' and k != 'before_id'):
            #where_action = 1
            filter_list.append(f"{k} {v}")
            # print(f"{k} {v}")

    # = null is not recommended so is null applied
    filter_list = [filter.replace('=null', 'is null') for filter in filter_list]

    select_str = select_str + ", ".join(output_fields_list)
    # print("where_str", where_str)
    ignore_delete_str = f" {table_name.split(',')[0]}.{meta_status} <> 'deleted' "

    if(filter_list and ignore_deleted_records_p):
        query = select_str + from_str + where_str + " and " + ignore_delete_str + " and " + " and ".join(filter_list)
    elif(filter_list and not ignore_deleted_records_p):
        query = select_str + from_str + where_str + " and " + " and ".join(filter_list)
    elif(not filter_list and ignore_deleted_records_p):
        query = select_str + from_str + where_str + " and " + ignore_delete_str
    else:
        query = select_str + from_str + where_str

    if(pagination_action):
        d = {
            "before_timestamp": before_timestamp_exists_p,
            "before_id": before_id_exists_p,
            "after_timestamp": after_timestamp_exists_p,
            "after_id": after_id_exists_p
        }

        error_field_dict = {}
        error_p = 0
        for k, v in d.items():
            if(not v):
                # print(k + "does not exist")
                error_field_dict[k] = v
                error_p = 1

        if(error_p):
            assert not error_field_dict, "Invalid Pagination Input Parameters"

    # There is always where condition involved so no need to check
    if(pagination_action):
        query = query + \
            f""" and ((({table_name.split(',')[0]}.modification_timestamp > '{after_timestamp}') or ({table_name.split(',')[0]}.modification_timestamp = '{after_timestamp}' and {pk_id} > '{after_id}') )
                                or (({table_name.split(',')[0]}.modification_timestamp < '{before_timestamp}') or ({table_name.split(',')[0]}.modification_timestamp = '{before_timestamp}' and {pk_id} < '{before_id}'))) """

    # Apply order by
    # query = query + f""" order by {table_name.split(',')[0]}.modification_timestamp desc, {pk_id} desc"""
    # Apply LIMIT
    query = query + """ limit """ + str(limit_value)

    # print(query)
    return query

def create_joining_search_query_v2(table_name, joining_condition, input_list, output_fields_list, ignore_deleted_records_p=True, meta_status="meta_status"):
    select_str = """select """
    where_str = f""" {joining_condition} where"""
    # limit_str = """ limit """
    pk_id = table_name.split(',')[0]+"."+table_name.split(',')[0] + '_id'
    first_table_name = table_name.split(',')[0]
    # table_name_without_underscore = first_table_name.split('_')
    # first_letter_of_each_element = [x[0] for x in table_name_without_underscore]
    # key_of_table = """ """.join(first_letter_of_each_element)
    from_str = f""" from {first_table_name}""" 
    
    # limit_value = g.resource.pagination_max_limit
    pagination_action = 0
    limit_value = g.pagination_max_limit
    filter_list = []
    limit_action = 0
    after_timestamp_exists_p = 0
    after_id_exists_p = 0
    before_timestamp_exists_p = 0
    before_id_exists_p = 0
    del_status = ""

    for k, v in input_list.items():
        if(k=='before_timestamp' ):
            print(f"the VALUE OF BEFORE_TIMESTAMP is: ", v)
            if(v.strip()=="first"):
                pagination_action = 0
            else:
                pagination_action = 1
                before_timestamp_exists_p = 1           
                before_timestamp = v

        if(k=='before_id'):
            print(f"the VALUE OF BEFORE_ID is: ", v)
            pagination_action = 1
            before_id_exists_p = 1
            before_id = v
        
            
        if(k=='limit'):
            limit_action = 1
            if(int(v) > g.pagination_max_limit):
                limit_value = g.pagination_max_limit
            else:
                limit_value = v   
            # JQ adding some sauce here
        if(k=='after_timestamp'):
            after_timestamp_exists_p = 1
            after_timestamp = v

        if(k=='after_id'):
            after_id_exists_p = 1
            after_id = v

        if(k!='before_timestamp' and k!='limit' and k!='after_timestamp' and  k!='after_id' and  k!='before_id'):
            #where_action = 1
            filter_list.append(f"{k} {v}")
            # print(f"{k} {v}")
    
    # = null is not recommended so is null applied
    filter_list = [filter.replace('=null','is null') for filter in filter_list]

    select_str = select_str + ", ".join(output_fields_list)
    # print("where_str", where_str)
    ignore_delete_str = f" {table_name.split(',')[0]}.{meta_status} != 'deleted' "

    if(filter_list and ignore_deleted_records_p):
        query = select_str + from_str  +  where_str + ignore_delete_str +" and "+" and ".join(filter_list)
    elif(filter_list and not ignore_deleted_records_p):
        query = select_str + from_str  +  where_str +" and ".join(filter_list)
    elif(not filter_list and ignore_deleted_records_p):
        query = select_str + from_str  +  where_str + ignore_delete_str
    else:
        query = select_str + from_str + where_str
    

    if(pagination_action):
        d = {
        "before_timestamp" : before_timestamp_exists_p, 
        "before_id" : before_id_exists_p,
        "after_timestamp" : after_timestamp_exists_p, 
        "after_id" : after_id_exists_p
        }

        error_field_dict = {}
        error_p = 0
        for k, v in d.items():
            if(not v):
                print(k + "does not exist")
                error_field_dict[k] = v
                error_p = 1

        if(error_p):
            assert not error_field_dict, "Invalid Pagination Input Parameters"
    
    # There is always where condition involved so no need to check
    if(pagination_action):
        query = query + f""" and ((({table_name.split(',')[0]}.modification_timestamp > '{after_timestamp}') or ({table_name.split(',')[0]}.modification_timestamp = '{after_timestamp}' and {pk_id} > '{after_id}') )
                            or (({table_name.split(',')[0]}.modification_timestamp < '{before_timestamp}') or ({table_name.split(',')[0]}.modification_timestamp = '{before_timestamp}' and {pk_id} < '{before_id}'))) """
    
    
    # Apply order by
    # query = query + f""" order by {table_name.split(',')[0]}.modification_timestamp desc, {pk_id} desc"""
    # Apply LIMIT
    query = query + """ limit """ + str(limit_value)

    # print(query)
    return query

def create_joining_search_query_v3(table_name, joining_condition, input_list, output_fields_list, ignore_deleted_records_p=True, meta_status="meta_status"):
    select_str = """select """
    where_str = f""" {joining_condition} where"""
    # limit_str = """ limit """
    pk_id = table_name.split(',')[0]+"."+table_name.split(',')[0] + '_id'
    first_table_name = table_name.split(',')[0]
    # table_name_without_underscore = first_table_name.split('_')
    # first_letter_of_each_element = [x[0] for x in table_name_without_underscore]
    # key_of_table = """ """.join(first_letter_of_each_element)
    from_str = f""" from {first_table_name}""" 
    
    # limit_value = g.resource.pagination_max_limit
    pagination_action = 0
    limit_value = g.pagination_max_limit
    filter_list = []
    limit_action = 0
    after_timestamp_exists_p = 0
    after_id_exists_p = 0
    before_timestamp_exists_p = 0
    before_id_exists_p = 0
    del_status = ""

    for k, v in input_list.items():
        if(k=='before_timestamp' ):
            print(f"the VALUE OF BEFORE_TIMESTAMP is: ", v)
            if(v.strip()=="first"):
                pagination_action = 0
            else:
                pagination_action = 1
                before_timestamp_exists_p = 1           
                before_timestamp = v

        if(k=='before_id'):
            print(f"the VALUE OF BEFORE_ID is: ", v)
            pagination_action = 1
            before_id_exists_p = 1
            before_id = v
        
            
        if(k=='limit'):
            limit_action = 1
            if(int(v) > g.pagination_max_limit):
                limit_value = g.pagination_max_limit
            else:
                limit_value = v   
            # JQ adding some sauce here
        if(k=='after_timestamp'):
            after_timestamp_exists_p = 1
            after_timestamp = v

        if(k=='after_id'):
            after_id_exists_p = 1
            after_id = v

        if(k!='before_timestamp' and k!='limit' and k!='after_timestamp' and  k!='after_id' and  k!='before_id'):
            #where_action = 1
            filter_list.append(f"{k} {v}")
            # print(f"{k} {v}")
    
    # = null is not recommended so is null applied
    filter_list = [filter.replace('=null','is null') for filter in filter_list]

    select_str = select_str + ", ".join(output_fields_list)
    # print("where_str", where_str)
    ignore_delete_str = f" {table_name.split(',')[0]}.{meta_status} = 'active' "

    if(filter_list and ignore_deleted_records_p):
        query = select_str + from_str  +  where_str + ignore_delete_str +" and "+" and ".join(filter_list)
    elif(filter_list and not ignore_deleted_records_p):
        query = select_str + from_str  +  where_str +" and ".join(filter_list)
    elif(not filter_list and ignore_deleted_records_p):
        query = select_str + from_str  +  where_str + ignore_delete_str
    else:
        query = select_str + from_str + where_str
    

    if(pagination_action):
        d = {
        "before_timestamp" : before_timestamp_exists_p, 
        "before_id" : before_id_exists_p,
        "after_timestamp" : after_timestamp_exists_p, 
        "after_id" : after_id_exists_p
        }

        error_field_dict = {}
        error_p = 0
        for k, v in d.items():
            if(not v):
                print(k + "does not exist")
                error_field_dict[k] = v
                error_p = 1

        if(error_p):
            assert not error_field_dict, "Invalid Pagination Input Parameters"
    
    # There is always where condition involved so no need to check
    if(pagination_action):
        query = query + f""" and ((({table_name.split(',')[0]}.modification_timestamp > '{after_timestamp}') or ({table_name.split(',')[0]}.modification_timestamp = '{after_timestamp}' and {pk_id} > '{after_id}') )
                            or (({table_name.split(',')[0]}.modification_timestamp < '{before_timestamp}') or ({table_name.split(',')[0]}.modification_timestamp = '{before_timestamp}' and {pk_id} < '{before_id}'))) """
    
    return query


def validate_query_string(resource_id):
    db_engine = jqutils.get_db_engine()
    # input_fields =  ["user_id", "username", "address", "description"]
    
    with db_engine.connect() as conn:
        query = text(""" 
                SELECT r.input_fields
                    FROM resource r
                    where resource_id = :resource_id and
                    meta_status = :meta_status                      
            """) 
        result = conn.execute(query, resource_id=resource_id, meta_status='active').fetchone()
        input_fields = result["input_fields"]
        input_fields_list = json.loads(input_fields)

    for k, v in request.args.items():
        if(k=='before_timestamp' or k=='after_timestamp'or k=='limit' or k=='after_id' or k=='before_id'):
            continue
        assert k in input_fields_list, "invalid input parameter"

    return { "status": "successful" }
            
  
def get_output_fields(resource_id):
    db_engine = jqutils.get_db_engine()
    # input_fields =  ["user_id", "username", "address", "description"]
    
    with db_engine.connect() as conn:
        query = text(""" 
                SELECT r.output_fields
                    FROM resource r
                    where resource_id = :resource_id and
                    meta_status = :meta_status                      
            """) 
        result = conn.execute(query, resource_id=resource_id, meta_status='active').fetchone()
        output_fields = result["output_fields"]

        output_fields_list = json.loads(output_fields)

    return output_fields_list
            
  
