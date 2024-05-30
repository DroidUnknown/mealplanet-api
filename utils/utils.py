import datetime
import decimal
import hashlib
from utils import jqutils
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.sql import text
from flask import Flask, request, g
import random
import string
from decimal import Decimal
ALLOWED_IMG_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif', 'jfif'])
#Json DataType handler
# List to be appended here
dataTypeList = (datetime.datetime, decimal.Decimal, datetime.date, datetime.timedelta)
def json_value_caster(list_dict):
    for i in list_dict:
        for key in i:
            if isinstance(i[key], dataTypeList):
                i[key] = str(i[key])
            # elif isinstance(i[key], Decimal):
            #     i[key] = float(i[key])
    return list_dict

#Search Extracted Record Count
def total_record_count(list_dict):
    record_count = 0
    for i in list_dict:
        record_count+=1
    return record_count

#Search Base Record Count
def base_record_count(entity):
    query = f""" select count(1) from {entity} where meta_status = \"active\" """
    db_engine = jqutils.get_db_engine()
    with db_engine.connect() as conn:
        count = conn.execute(query).fetchone()[0]
    return count

#Count on Provided Criteria
def create_search_count_query(table_name, input_list):
    select_str = """select count(1)"""
    from_str = """ from """ + table_name
    where_str = """ where """

    filter_list = []
    where_action = 0

    for k, v in input_list.items(): 
        if(k!='paginate_last_timestamp' and k!='limit'):
            where_action = 1
            filter_list.append(f"{k}{v}")
           
    where_str = where_str  + " and ".join(filter_list)

    if(where_action):
        query = select_str + from_str + where_str
    else:
        query = select_str + from_str

    return query

# Joined Query Search
def create_joining_search_query(table_name, joining_condition, input_list, output_fields_list, ignore_deleted_records_p=True, meta_status="meta_status"):
    select_str = """select """
    where_str = f""" where  {joining_condition} """
    limit_str = """ limit """
    pk_id = table_name.split(',')[0]+"."+table_name.split(',')[0] + '_id'
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
            #where_action = 1
            filter_list.append(f"{k} {v}")
    
    # = null is not recommended so is null applied
    filter_list = [filter.replace('=null','is null') for filter in filter_list]

    select_str = select_str + ", ".join(output_fields_list)
    ignore_delete_str = f" {table_name.split(',')[0]}.{meta_status} != 'deleted' "

    if(filter_list and ignore_deleted_records_p):
        query = select_str + from_str  +  where_str +" and "+ ignore_delete_str +" and "+" and ".join(filter_list)
    elif(filter_list and not ignore_deleted_records_p):
        query = select_str + from_str  +  where_str +" and "+" and ".join(filter_list)
    elif(not filter_list and ignore_deleted_records_p):
        query = select_str + from_str  +  where_str + " and " + ignore_delete_str
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

    return query


#Random Alphanumeric Code Generator
def generate_random_alphanumeric(name, namelength, codelength):
    characters = name[0:namelength]
    letters = string.ascii_lowercase + string.digits
    return characters+"_"+''.join(random.choice(letters) for i in range(codelength))


# Query builder
def query_builder(table, columns, values, **parent):
    if(parent == {}): #REPLACE TO UPSERT
        sql = "REPLACE INTO {0} ({1}) VALUES ({2})"
        endQuery = sql.format( table, columns, values)
    else:          
        newColumns = columns+ "," +",".join(v for v in parent.keys()) 
        newVals = values+ ",'"  +"','".join(str(v) for v in parent.values()) + "'"
        
        sql = "INSERT INTO {0} ({1}) VALUES ({2})"
        endQuery = sql.format( table, newColumns, newVals)
    return endQuery.replace("\\\\'" , "\\'")


# def dictionary_process(custom_dictionary):
# 	cols = ""
# 	vals = ""
# 	for key, value in custom_dictionary.items():
# 		cols+=key + ""","""
# 		vals+= """'""" + str(value) + """', """ 
# 	columns = cols[:-1]
# 	values = vals[:-2]

# 	return columns , values

def dictionary_process(custom_dictionary):
    columns = ""
    values = ""
    columns = columns +",".join(v for v in custom_dictionary.keys())
    values = values+ "'"  +"','".join(str(v) for v in custom_dictionary.values()) + """'"""
    return columns , values



def string_json_convert(object):
    if(object != None):
        res = list(eval(object))
    else:
        res = []
    return res



def prepare_update_statement(table_name, one_row_dict, where_clause):
	query = """
    update {0} set {1} where {2};
    """
	one_dict = dict(one_row_dict)
	column = ' = %s, '.join(one_row_dict.keys()) + ''.join([' = %s'])
	where = ' = %s and '.join(where_clause.keys()) + " =" + ''.join([' %s '] )
    #where = ''.join(where_clause.keys()) + " = " + ''.join(['%s'] * len(where_clause))
	values_list = list(one_dict.values()) + list(where_clause.values())

	return (query.format(table_name,column, where), values_list)



def check_image_extension(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMG_EXTENSIONS

def create_unique_external_code_by_branch(table_name, column_name, branch_id, input_string, length=10):
 
    db_engine = jqutils.get_db_engine()

    while True:
        # Encode the string before hashing
        encoded_string = input_string.encode('utf-8')
        
        # Create a SHA-256 hash object
        sha256_hash = hashlib.sha256()
        
        # Update the hash object with the encoded string
        sha256_hash.update(encoded_string)
        
        # Get the hexadecimal representation of the hash
        hashed_value = sha256_hash.hexdigest()

        # Truncate the hash to the desired length
        truncated_hash = hashed_value[:length]

        # Check if the hash already exists in the database for the branch
        query = text(f"""
            SELECT {table_name}_id
            FROM {table_name}
            WHERE branch_id = :branch_id
            AND {column_name} = :external_code
            AND meta_status = :meta_status
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, branch_id=branch_id, external_code=truncated_hash, meta_status="active").fetchone()

        if not result:
            # If it doesn't exist, return the hash
            return truncated_hash
        
        # If it exists, regenerate the hash with a random salt
        input_string = input_string + str(random.randint(1, 1000))