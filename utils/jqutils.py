import hashlib
import random
import string
import decimal
import os
import re
import logging
import secrets
import boto3
import urllib

from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from flask import g

from utils import aws_utils

ENGINES = {}
ENGINE_KWARGS = {'pool_pre_ping': True, 'pool_size': 250, 'pool_recycle': 600, 'isolation_level': 'READ COMMITTED'}

def get_db_engine(db_schema=None, connection_name=None):
    load_dotenv(dotenv_path='./.env')

    if connection_name:
        assert connection_name in ['DEV'], 'connection name is not correct'
        connection_prefix = "mysql+pymysql://"
        database_user = os.environ.get(f'{connection_name}_MYSQL_USER')
        database_password = os.environ.get(f'{connection_name}_MYSQL_PASSWORD')
        host = os.environ.get(f'{connection_name}_MYSQL_IP_ADDRESS')
        port = os.environ.get(f'{connection_name}_MYSQL_PORT')
        db_schema = db_schema if db_schema else os.environ.get(f'{connection_name}_MYSQL_SCHEMA_NAME')
        connect_args = {}

        engine_name = 'ENGINE' + db_schema

    else:
        connection_prefix = "mysql+pymysql://"
        database_user = os.environ.get('MYSQL_USER')
        database_password = os.environ.get('MYSQL_PASSWORD')
        host = os.environ.get('MYSQL_IP_ADDRESS')
        port = "3306"
        db_schema = db_schema if db_schema else os.environ.get('MYSQL_SCHEMA_NAME')
        connect_args = {}

        engine_name = 'ENGINE' + db_schema

    
    if engine_name not in ENGINES:
        ENGINES[engine_name] = create_engine(connection_prefix + database_user + ":" + database_password + "@" + host + ':' + port + '/' + db_schema, connect_args=connect_args, **ENGINE_KWARGS)
    return ENGINES[engine_name]

def jq_prepare_insert_statement(table_name, one_row_dict):
    query = """
    INSERT INTO {0} ({1}) VALUES ({2});
    """
    one_dict = dict(one_row_dict)
    columns = ','.join(one_dict.keys())
    placeholders = ','.join(['%s'] * len(one_dict))
    values_list = list(one_dict.values())
    return (query.format(table_name, columns, placeholders), values_list)

def jq_prepare_insert_statement_v2(table_name, one_row_dict, g):
    one_row_dict["meta_status"] = "active"
    one_row_dict["tenant_id"] = g.tenant_id
    one_row_dict["creation_user_id"] = g.user_id
    query = """
    INSERT INTO {0} ({1}) VALUES ({2});
    """
    one_dict = dict(one_row_dict)
    columns = ','.join(one_dict.keys())
    placeholders = ','.join(['%s'] * len(one_dict))
    values_list = list(one_dict.values())
    return (query.format(table_name, columns, placeholders), values_list)

def jq_prepare_insert_statement_multi_rows(table_name, dict_list):
    query = """
    INSERT INTO {0} ({1}) VALUES ({2});
    """
    row_list = []
    for one_dict in dict_list:
        one_dict = dict(one_dict)
        columns = ','.join(one_dict.keys())
        placeholders = ','.join(['%s'] * len(one_dict))
        values_list = list(one_dict.values())
        row_list.append(values_list)
    
    # one_dict = dict(one_row_dict)
    # columns = ','.join(one_dict.keys())
    
    # placeholders = ','.join(['%s'] * len(one_dict))
    # values_list = list(one_dict.values())
    return (query.format(table_name, columns, placeholders), row_list)

def jq_prepare_insert_statement_multi_rows_v2(table_name, dict_list,g):
    query = """
    INSERT INTO {0} ({1}) VALUES ({2});
    """
    row_list = []
    for one_dict in dict_list:
        one_dict["meta_status"] = "active"
        one_dict["tenant_id"] = g.tenant_id
        one_dict["creation_user_id"] = g.user_id
        one_dict = dict(one_dict)
        columns = ','.join(one_dict.keys())
        placeholders = ','.join(['%s'] * len(one_dict))
        values_list = list(one_dict.values())
        row_list.append(values_list)
    
    # one_dict = dict(one_row_dict)
    # columns = ','.join(one_dict.keys())
    
    # placeholders = ','.join(['%s'] * len(one_dict))
    # values_list = list(one_dict.values())
    return (query.format(table_name, columns, placeholders), row_list)

def jq_prepare_update_statement(table_name, one_row_dict, condition, user_id):
    one_row_dict["modification_user_id"] = user_id
    one_row_dict["modification_timestamp"] = datetime.now()
    query = """
    UPDATE {0} SET {1} WHERE {2};
    """
    one_dict = dict(one_row_dict)
    columns = ""
    for i in one_dict.keys():
        columns = columns + i + " = " + '%s, '
    where = ''.join(condition.keys()) + " = " + ''.join(['%s'] * len(condition))
    values_list = list(one_dict.values())
    values_list.append(''.join(condition.values()))

    return (query.format(table_name, columns[:-2], where), values_list)

def jq_prepare_update_statement_v2(table_name, one_row_dict, condition, g):
    one_row_dict["tenant_id"] = g.tenant_id
    one_row_dict["modification_user_id"] = g.user_id
    one_row_dict["modification_timestamp"] = datetime.now()

    query = """
    UPDATE {0} SET {1} WHERE {2};
    """
    one_dict = dict(one_row_dict)
    columns = ""
    for i in one_dict.keys():
        columns = columns + i + " = " + '%s, '
    where_conditions = []
    for key, value in condition.items():
        where_conditions.append(f"{key} = %s")
    where = ' AND '.join(where_conditions)
    values_list = list(one_dict.values())
    values_list.extend(list(condition.values()))

    return (query.format(table_name, columns[:-2], where), values_list)

# Random Alphanumeric Generator
def get_random_alphanumeric(length):
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for i in range(length))

# def get_utc_datetime():
#     import time
#     from datetime import datetime
#     TIME_FORMAT='%Y-%m-%d %H:%M:%S'
#     ts = int(time.time()) # UTC timestamp
#     timestamp = datetime.utcfromtimestamp(ts).strftime(TIME_FORMAT)
#     utc_timestamp_str = str(datetime.strptime(timestamp + "+0000", TIME_FORMAT + '%z'))
#     return utc_timestamp_str

def get_utc_datetime():
    import time
    from datetime import datetime
    TIME_FORMAT = '%Y-%m-%d %H:%M:%S.%f'
    ts = time.time()  # UTC timestamp
    timestamp = datetime.utcfromtimestamp(ts).strftime(TIME_FORMAT)
    # utc_timestamp_str = str(datetime.strptime(timestamp + "+0000", TIME_FORMAT + '%z'))
    utc_timestamp_str = str(datetime.strptime(timestamp, TIME_FORMAT))
    # ts1 = utc_timestamp_str.timestamp()
    return utc_timestamp_str

def get_utc_date():
    from datetime import datetime
    DATE_FORMAT = '%Y-%m-%d'
    utc_date = datetime.utcnow().strftime(DATE_FORMAT)
    return utc_date

def get_local_date(timezone_offset_hours):
    from datetime import datetime, timedelta
    DATE_FORMAT = '%Y-%m-%d'
    local_date = (datetime.utcnow() + timedelta(hours=timezone_offset_hours)).strftime(DATE_FORMAT)
    return local_date


def upload_csv_map(target_table_name, source_filename, table_list):
    count = 0
    db_engine = get_db_engine()
    with open(source_filename) as fp:
        header = fp.readline().strip()
        header_list = header.split(',')
        for line in fp:
            count += 1
            one_row = line.strip()
            one_row_list = one_row.split(',')
            res1 = [i + "." + j for i, j in zip(table_list, header_list)]
            res = [i + "='" + j + "'" for i, j in zip(res1, one_row_list)]
            where_line = """ where """ + ' and '.join(res) + ')'
            key_ids = [table + '.' + table + '_id' for table in table_list]
            field_list = [table + '_id' for table in table_list]
            insert_line = """ insert into """ + target_table_name + """ (""" + ','.join(field_list) + ') '
            select_line = """(select """ + ','.join(key_ids)
            from_line = """ from """ + ','.join(table_list)
            query = insert_line + select_line + from_line + where_line
            with db_engine.connect() as conn:
                conn.execute(query)

def jq_prepare_insert_statement_from_csv(table_name, header, one_row):
    query = """
    INSERT INTO {0} ({1}) VALUES ({2});
    """
    param_list = one_row.split('|')
    for i,one_param in enumerate(param_list):
        if one_param == 'None':
            param_list[i] = None
            
    placeholders = ','.join(['%s'] * len(param_list))

    return (query.format(table_name, header, placeholders), param_list)


def upload_csv(target_table_name, source_filename):
    # table_name = 'brand'
    count = 0
    db_engine = get_db_engine()

    with open(source_filename, encoding="utf8") as fp:
        header = fp.readline()
        header += "|creation_user_id"
        header = header.replace('|', ',')

        for line in fp:
            count += 1
            one_row = line.strip()
            one_row += "|1"

            query, param_list = jq_prepare_insert_statement_from_csv(target_table_name, header, one_row)
            with db_engine.connect() as conn:
                conn.execute(query, param_list).lastrowid


def result_proxy_to_dict_list(result_proxy):
    x = {}
    y = []
    for one_row_proxy in result_proxy:
        # rowproxy.items() returns an array like [(key0, value0), (key1, value1)]
        for column, value in one_row_proxy.items():
            # build up the dictionary
            # d = {**d, **{column: value}}
            x = {**x, column: value}
        # a.append(d)
        y.append(x)
    return y

def upload_one_row_from_csv_append_column(csv_path, column_value, column_name, table_name):
    with open(csv_path) as fp:
        header = fp.readline()
        header = header.replace('|', ',')
        header = header.strip() + "," + column_name
        for line in fp:
            # count += 1
            one_row = line.strip()
            one_row = one_row + "|" + str(column_value)
            param_list = one_row.split("|")
            placeholders = ','.join(['%s'] * len(param_list))
            query = """
            INSERT INTO {0} ({1}) VALUES ({2})
            """
            query = query.format(table_name, header, placeholders)
            db_engine = get_db_engine()
            with db_engine.connect() as conn:
                row_id = conn.execute(query, param_list).lastrowid
    return row_id


def upload_multiple_rows_from_csv_append_column(csv_path, column_value, column_name, table_name):
    with open(csv_path) as fp:
        header = fp.readline()
        header = header.replace('|', ',')
        header = header.strip() + "," + column_name

        id_list = []
        for line in fp:
            # count += 1
            one_row = line.strip()
            one_row = one_row + "|" + str(column_value)
            param_list = one_row.split("|")
            # param_list.append(country_id)
            placeholders = ','.join(['%s'] * len(param_list))
            # query, param_list = jq_prepare_insert_statement_from_csv("city", header, one_row)
            query = """
            INSERT INTO {0} ({1}) VALUES ({2})
            """
            # placeholders = ','.join(['%s'] * len(param_list))
            # placeholders = placeholders + " , " + str(country_id)

            query = query.format(table_name, header, placeholders)

            db_engine = get_db_engine()
            with db_engine.connect() as conn:
                row_id = conn.execute(query, param_list).lastrowid
                id_list.append(row_id)

    return id_list

def insert_one_row_from_csv(file_path, table_name):
    with open(file_path) as fp:
        header = fp.readline()
        header = header.strip()
        header = header.replace('|', ',')
        data = fp.readline()
        param_list = data.split("|")
        value_placeholders = ','.join(['%s'] * len(param_list))

        query = """
        INSERT INTO {0} ({1}) VALUES ({2})
        """
        query = query.format(table_name, header, value_placeholders)
        db_engine = get_db_engine()
        with db_engine.connect() as conn:
            last_row_id = conn.execute(query, param_list).lastrowid
    return last_row_id


def get_id_by_name(input_value, column_name, table_name):
    primary_id = table_name + "_id"
    query = text(
        """ SELECT """ + primary_id +
        """ FROM """ + table_name +
        """ WHERE """ + column_name + """ = '""" + input_value.strip() + """' """+
        """AND meta_status = 'active' """+
        """ORDER BY insertion_timestamp DESC """+
        """LIMIT 1"""
    )
    db_engine = get_db_engine()
    with db_engine.connect() as conn:
        last_row_id = conn.execute(query).fetchone()[0]
        assert last_row_id, "no data"
    return last_row_id


def get_id_of_map_by_names(input_value_1, column_name_1, table_name_1, input_value_2, column_name_2, table_name_2, map_table_name):
    primary_id = map_table_name + "_id"
    query = text(
        """ SELECT """ + primary_id + " from " + map_table_name + " mtn inner join " + table_name_1 +
        " t1 on t1." + table_name_1 + "_id  = " + "mtn." + table_name_1 + "_id inner join " +
        table_name_2 + " t2 on t2." + table_name_2 + "_id = " + "mtn." + table_name_2 + "_id " +
        " WHERE t1." + column_name_1 + " = '" + input_value_1 + "' and t2." + column_name_2 + " = '" + input_value_2 + "'"
    )
    db_engine = get_db_engine()
    with db_engine.connect() as conn:
        result = conn.execute(query).fetchone()
        assert result, "no data"
        last_row_id = result[0]
    return last_row_id

def get_column_by_id(input_value, column_name, table_name):
    primary_id = table_name + "_id"
    query = text(
        """ SELECT """ + column_name +
        """ FROM """ + table_name +
        """ WHERE """ + primary_id + """ = """ + str(input_value)
    )
    db_engine = get_db_engine()
    with db_engine.connect() as conn:
        result = conn.execute(query).fetchone()
        assert result, "no data"
        last_row_id = result[0]
    return last_row_id

def get_record_by_id(input_value, table_name, undeleted=True):
    primary_id = table_name + "_id"
    query = f"""
        SELECT * FROM {table_name} 
        WHERE {primary_id} = {str(input_value)}
    """
    if undeleted:
        query += " AND meta_status <> 'deleted'"
    db_engine = get_db_engine()
    with db_engine.connect() as conn:
        record = conn.execute(text(query)).fetchone()
    return record

def get_record_list_by_column(input_value, column_name, table_name, undeleted=True):
    query = f"""
        SELECT * FROM {table_name} 
        WHERE {column_name} = :input_value
    """
    if undeleted:
        query += " AND meta_status <> 'deleted'"
    db_engine = get_db_engine()
    with db_engine.connect() as conn:
        records = conn.execute(text(query), input_value=input_value).fetchall()
    return [dict(_) for _ in records]

def get_by_id(input_value, table_name, condition={}):
    query = """
        SELECT * FROM {1} WHERE {2};
    """
    table_id = input_value
    where = ''.join(condition.keys()) + " = " + ''.join(['%s'] * len(condition))
    values_list = list(one_dict.values())
    values_list.append(''.join(condition.values()))

    return (query.format(table_name, columns[:-2], where), values_list)

def check_record_by_id(input_value, table_name):
    primary_id = f"{table_name}_id"
    query = text(f"""
        SELECT {primary_id} FROM {table_name}
        WHERE {primary_id} = {str(input_value)}
    """)
    db_engine = get_db_engine()
    with db_engine.connect() as conn:
        return conn.execute(query).rowcount

def delete_record_by_id(input_value, table_name, user_id):
    primary_id = f"{table_name}_id"
    change = {"meta_status": "deleted"}
    condition = {primary_id: str(input_value)}
    query, params = jq_prepare_update_statement(table_name, change, condition, user_id)

    db_engine = get_db_engine()
    with db_engine.connect() as conn:
        result = conn.execute(query, params).rowcount

    return result

def delete_record_by_id_v2(input_value, table_name,g):
    primary_id = f"{table_name}_id"
    change = {
        "meta_status": "deleted",
        "modification_user_id":g.user_id,
        "tenant_id":g.tenant_id,
        "modification_timestamp":datetime.now()
        }
    condition = {primary_id: str(input_value)}
    query, params = jq_prepare_update_statement_v2(table_name, change, condition,g)

    db_engine = get_db_engine()
    with db_engine.connect() as conn:
        result = conn.execute(query, params).rowcount

    return result

def create_code_from_title(name, random_count):
    # remove all special characters
    name = re.sub(r"[^a-zA-Z0-9\s]", "", name)
    # replace all spaces with single space
    name = re.sub(r"[\s]+", " ", name)
    name_list = name.strip().lower().split(" ")
    # q = ''.join()
    q = ''.join(_[0] for _ in name_list)
    random_code = q + "_" + ''.join([str(secrets.choice(string.digits)) for _ in range(random_count)])
    return random_code

def create_unique_code_from_title(name, random_count, table_name, column_name, retries=50, append_hard_coded_string=None):
    db_engine = get_db_engine()
    
    unique_p = False
    try_count = 0

    while not unique_p and try_count < retries:
        candidate_code = create_code_from_title(name, random_count)

        if append_hard_coded_string:
            candidate_code = candidate_code + "_" + append_hard_coded_string

        query = text(f"""
            SELECT {column_name}
            FROM {table_name}
            WHERE {column_name} = :candidate_code
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, candidate_code=candidate_code).rowcount
            try_count += 1
            if not result:
                unique_p = True
    
    assert unique_p, "Unable to generate unique code"

    return candidate_code

def cleanse_for_db(value):
    """
    Cleanses the value for database insertion
    lowercases the value
    pipes are never allowed
    """
    if value is None:
        return None
    value = value.lower()
    value = value.replace("|", "")
    return value


# def get_utc_datetime():
#    import time
#    from datetime import datetime
#    TIME_FORMAT='%Y-%m-%d %H:%M:%S'
#    ts = int(time.time()) # UTC timestamp
#    timestamp = datetime.utcfromtimestamp(ts).strftime(TIME_FORMAT)
#    utc_timestamp_str = str(datetime.strptime(timestamp + "+0000", TIME_FORMAT + '%z'))
#    # ts1 = utc_timestamp_str.timestamp()
#    return utc_timestamp_str


# def create_presigned_post(bucket_name, object_name, file_type, expiration=3600):
#     # Generate a presigned S3 POST URL
#     s3_client = boto3.client('s3')
#     try:
#         response = s3_client.generate_presigned_post(bucket_name,
#                                                      object_name,
#                                                      Fields = {"acl": "public-read", "Content-Type": file_type},
#                                                      Conditions = [
#                                                         {"acl": "public-read"},
#                                                         {"Content-Type": file_type}
#                                                         ],
#                                                      ExpiresIn=expiration)
#     except ClientError as e:
#         logging.error(e)
#         return None
#     # The response contains the presigned URL and required fields
#     return response

# def create_presigned_post(bucket_name, object_name, file_type, expiration=3600):
#     # Generate a presigned S3 POST URL
#     s3_client = boto3.client('s3', aws_access_key_id="xxxxxxxxxx", aws_secret_access_key="xxxxxxxxxxxxxx" )
#     try:
#         response = s3_client.generate_presigned_post(
#                     Bucket = bucket_name,
#                     Key = object_name,
#                     Fields = {"acl": "public-read", "Content-Type": file_type},
#                     Conditions = [
#                     {"acl": "public-read"},
#                     {"Content-Type": file_type}
#                     ],
#                     ExpiresIn = expiration
#                 )

#         response.pop("url")
#         response= {
#             'data': response,
#             'url': 'https://%s.s3.amazonaws.com/%s' % (bucket_name, object_name)
#         }

#     except ClientError as e:
#         logging.error(e)
#         return None
#     # The response contains the presigned URL and required fields
#     return response

def create_s3_public_url(bucket_name, object_key, region_name=None):
    if not region_name:
        region_name = os.getenv('AWS_DEFAULT_REGION')
    
    object_url = None
    if region_name and bucket_name and object_key:
        object_url = "https://{0}.s3.{1}.amazonaws.com/{2}".format(urllib.parse.quote_plus(bucket_name, safe="/"), region_name, urllib.parse.quote_plus(object_key, safe="/"))
    
    return object_url

def create_presigned_put_url(bucket_name, object_name, expiration=3600):
    # Generate a presigned S3 PUT URL
    s3_client = boto3.client('s3')
    try:
        response = response = s3_client.generate_presigned_url(
            ClientMethod='put_object',
            HttpMethod='PUT',
            ExpiresIn=expiration,
            Params={
                'Bucket': bucket_name,
                'Key': object_name
            }
        )

    except ClientError as e:
        logging.error(e)
        return None
    # The response contains the presigned URL and required fields
    return response


def create_presigned_get_url(bucket_name, object_name, expiration=3600):
    # Generate a presigned S3 PUT URL
    s3_client = boto3.client('s3')
    try:
        response = response = s3_client.generate_presigned_url(
            ClientMethod='get_object',
            HttpMethod='GET',
            ExpiresIn=expiration,
            Params={
                'Bucket': bucket_name,
                'Key': object_name
            }
        )

    except ClientError as e:
        logging.error(e)
        return None
    # The response contains the presigned URL and required fields
    return response


# def test_jq_lab(client):
#     BUCKET_NAME = "jq-bucket-play"
#     # Generate a presigned S3 POST URL
#     filename = './data_migration_management/menu_item_and_instruction_images/fern el balad/spicy akkawi/menu-item-display-images/spicy akkawi.jpg'
#     object_name = "presigned_post_object_1"
#     response = create_presigned_post(BUCKET_NAME, object_name, expiration=3600)
#     # Demonstrate how another Python program can use the presigned URL to upload a file
#     with open(filename, 'rb') as f:
#         files = {'file': (object_name, f)}
#         http_response = requests.post(response['url'], data=response['fields'], files=files)
#     # If successful, returns HTTP status code 204
#     return


def check_value_exists_in_candidate_list(reference_value, candidate_key, cand_search_list):
    value_exists = False
    for one_element in cand_search_list:
        candidate_element = one_element[candidate_key]
        if candidate_element == reference_value:
            value_exists = True
            break
    return value_exists

def cleanse_string_values_in_json(input_obj):
    if isinstance(input_obj, dict):
        for key, value in input_obj.items():
            # Check if value is of dict type
            if isinstance(value, dict):
                # If value is dict then iterate over all its values
                cleanse_string_values_in_json(value)
            elif isinstance(value, list):
                for v in value:
                    cleanse_string_values_in_json(v)
            elif isinstance(value, str):
                    input_obj[key] = cleanse_string(value)
    return input_obj

def cleanse_string(input_string):
    # remove |
    input_string = input_string.replace("|", "")
    input_string = input_string.strip().lower()
    
    return re.sub(r"[\s]+", " ", input_string)

def generate_unique_code(table_name, column_name, keyword, length=10, method="basic"):
    
    db_engine = get_db_engine()
    unique_p = False
    retries = 0
    max_retry_count = 50

    while not unique_p and retries < max_retry_count:
        
        if method == "sha256":
            # generate random seed to encode
            seed = ''.join([str(secrets.choice(string.digits)) for _ in range(length)])
            candidate_code = cleanse_string(hashlib.sha256(seed.encode()).hexdigest()[:length])
        else:
            candidate_code = cleanse_string(create_code_from_title(keyword, length))

        # check if merchant_transaction_code is unique
        query = text(f"""
            SELECT {column_name}
            FROM {table_name}
            WHERE {column_name} = :candidate_code
            AND meta_status = :meta_status
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, candidate_code=candidate_code, meta_status="active").rowcount
            retries += 1
            if not result:
                unique_p = True
    
    assert retries < max_retry_count, f"unable to create unique {column_name}, retries: {retries}."

    return candidate_code

def round_half_up(number, decimal_places=2):
    decimal_precision = '0.' + '0' * (decimal_places-1) + '1'
    rounded = decimal.Decimal(str(number)).quantize(decimal.Decimal(decimal_precision), rounding=decimal.ROUND_HALF_UP)
    return float(rounded)

# local time 08:00:00, default_timezone_offset_hour = 3
# utc time 05:00:00
def get_utc_time_from_local_time(time_local, default_timezone_offset_hour):
    time_local = f"2021-01-01 {time_local}"
    time_local = datetime.strptime(time_local, "%Y-%m-%d %H:%M:%S")
    time_utc = time_local - timedelta(hours=default_timezone_offset_hour)
    time_utc = time_utc.strftime("%H:%M:%S")
    return time_utc

def get_random_alphanumeric_string(length):
    result_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for i in range(length))
    return result_str

def create_new_single_db_entry(one_dict, table_name, capture_tenant = True):
    if capture_tenant:
        query,params = jq_prepare_insert_statement_v2(table_name,one_dict,g)
    else:
        one_dict["meta_status"] = 'active'
        query,params = jq_prepare_insert_statement(table_name,one_dict)
    db_engine = get_db_engine()
    with db_engine.connect() as conn:
        result = conn.execute(query,params)
    if result:
        last_entry_id = result.lastrowid
        return last_entry_id
    return False

def update_single_db_entry(one_dict, table_name, condition, capture_tenant = True):
    if capture_tenant:
        query,params = jq_prepare_update_statement_v2(table_name,one_dict,condition,g)
    else:
        query,params = jq_prepare_update_statement(table_name, one_dict, condition, None) 
    db_engine = get_db_engine()
    with db_engine.connect() as conn:
        result = conn.execute(query,params)
    if result:
        update_status = result.rowcount
        return update_status
    return False

def get_specific_columns_by_id(entity_id_list,table,column_name_str, capture_tenant = True):
    sub_query = ""
    if capture_tenant:
        sub_query = f" AND tenant_id = {g.tenant_id}"
    query = text(f"""
        SELECT
            {column_name_str}
        FROM
            {table}
        WHERE
            {table}_id IN ({entity_id_list})
        AND
            meta_status = 'active'
        {sub_query}
    """)
    db_engine = get_db_engine()
    with db_engine.connect() as conn:
        result_tuple = conn.execute(query).fetchall()
        return [dict(row) for row in result_tuple]

def create_archive_record(table_name, record_id):
    one_row_data = get_specific_columns_by_id(str(record_id), table_name, "*")
    if len(one_row_data) <=0:
        return False

    status = create_new_single_db_entry(one_row_data[0],"archive_"+table_name,True)
    return status