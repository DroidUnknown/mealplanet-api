from botocore.exceptions import ClientError
from datetime import datetime, timedelta
from sqlalchemy import text
from customer_order_management import customer_order_ninja
from utils import jqutils, aws_utils
from flask import g
import requests
import logging
import boto3
import json
import os


def create_status_entry(entity_id,status,reference_table,capture_tenant = True):
    db_engine = jqutils.get_db_engine()
    with db_engine.connect() as conn:
        dynamic_data = {
            reference_table+"_id":entity_id,
            "action_timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": status,
        }
        if capture_tenant:
            new_query, new_params = jqutils.jq_prepare_insert_statement_v2(reference_table+"_status_log",dynamic_data,g)
        else:
            dynamic_data["meta_status"] = "active"
            new_query, new_params = jqutils.jq_prepare_insert_statement(reference_table+"_status_log",dynamic_data)
        conn.execute(new_query, new_params)


def create_new_single_db_entry(one_dict, table_name, capture_tenant = True):
    if capture_tenant:
        query,params = jqutils.jq_prepare_insert_statement_v2(table_name,one_dict,g)
    else:
        one_dict["meta_status"] = 'active'
        query,params = jqutils.jq_prepare_insert_statement(table_name,one_dict)
    db_engine = jqutils.get_db_engine()
    with db_engine.connect() as conn:
        result = conn.execute(query,params)
    if result:
        last_entry_id = result.lastrowid
        return last_entry_id
    return False


def update_single_db_entry(one_dict, table_name, condition, capture_tenant = True):
    if capture_tenant:
        query,params = jqutils.jq_prepare_update_statement_v2(table_name,one_dict,condition,g)
    else:
        query,params = jqutils.jq_prepare_update_statement(table_name, one_dict, condition, None) 
    db_engine = jqutils.get_db_engine()
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
    db_engine = jqutils.get_db_engine()
    with db_engine.connect() as conn:
        result_tuple = conn.execute(query).fetchall()
        return [dict(row) for row in result_tuple]


def get_specific_columns_by_table(table,column_name_str):
    query = text(f"""
        SELECT 
            {column_name_str}
        FROM 
            {table}
        WHERE 
            meta_status = 'active'
        AND 
            tenant_id = {g.tenant_id}
    """)
    db_engine = jqutils.get_db_engine()
    with db_engine.connect() as conn:
        result_tuple = conn.execute(query).fetchall()
        return [dict(row) for row in result_tuple]


def upload_json_to_s3(json_data, file_name):
    s3_bucket = os.getenv("S3_BUCKET_NAME")
    s3_object_key = os.getenv("S3_TRANSACTION_OBJECT")+file_name
    if file_name != None:
        if os.getenv("MOCK_S3_UPLOAD") == "1":
            s3_bucket = "test_"+s3_bucket
            s3_object_key = "test_"+s3_object_key
        else:
            s3_client = boto3.client('s3')
            try:
                s3_client.put_object(
                    Body=json.dumps(json_data,default=str),
                    Key=s3_object_key,
                    Bucket=s3_bucket
                    )
            except ClientError as e:
                logging.error(e)
                s3_object_key = None
    return s3_bucket,s3_object_key


def get_file_data_from_s3(bucket_name, object_key):
    s3_client = boto3.client('s3')
    try:
        file_data = s3_client.get_object(Bucket=bucket_name, Key=object_key)['Body'].read()
        file_data = file_data.decode()
    except ClientError as error:
        logging.error(error)
        file_data = None
    return file_data


def create_archive_record(table_name, record_id):
    one_row_data = get_specific_columns_by_id(str(record_id), table_name, "*")
    if len(one_row_data) <=0:
        return False

    status = create_new_single_db_entry(one_row_data[0],"archive_"+table_name,True)
    return status


def publish_tech_support_message(message, event, user_id=None, signup_request_id=None, demo_signup_request_id=None):
    if os.getenv("MOCK_AWS_NOTIFICATIONS") != "1":
        topic_name = os.getenv("TECH_SUPPORT_ALERTS_TOPIC_NAME")
        db_engine = jqutils.get_db_engine()
        query = text("""
            SELECT topic_arn
            FROM sns_topic
            WHERE topic_name = :topic_name
            AND meta_status = :meta_status
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, topic_name=topic_name, meta_status="active").fetchone()
            assert result, "select topic_arn failure"

        topic = result['topic_arn']
        publisher = aws_utils.get_aws_publisher("sms")
        attributes = {}
        message_id = publisher.publish_message(topic, message, attributes)

        query = text("""
            INSERT INTO publishing_queue_tech_support(user_id, signup_request_id, demo_signup_request_id, message, message_id, message_attributes, order_event, meta_status)
            VALUES (:user_id, :signup_request_id, :demo_signup_request_id, :message, :message_id, :message_attributes, :order_event, :meta_status)
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, user_id=user_id, signup_request_id=signup_request_id, demo_signup_request_id=demo_signup_request_id, message=message,
                        message_id=message_id, message_attributes=str(attributes), order_event=event, meta_status="active").lastrowid
            assert result, "Failed to insert into publishing queue"


def check_order_exists(external_order_reference_nr):
    db_engine = jqutils.get_db_engine()

    date_yesterday = datetime.utcnow() - timedelta(days=7)

    query = text("""
        SELECT customer_order_id, order_status
        FROM customer_order
        WHERE external_order_reference_nr = :external_order_reference_nr
        AND DATE(order_creation_timestamp) > :date_yesterday
        ORDER BY customer_order_id DESC
        LIMIT 1
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, external_order_reference_nr=external_order_reference_nr, date_yesterday=date_yesterday).fetchone()

    if result:
        return result['customer_order_id'], result['order_status']
    return None, None


def punch_integrated_order(one_branch, one_payload):
    
    request_headers = {
        'X-Access-Token': os.getenv('IBLINK_API_ACCESS_TOKEN'),
        'X-User-ID':os.getenv('IBLINK_API_USER_ID'),
    }
    request_url = f"{os.getenv('IBLINK_API_BASE_URL')}/customer-order"
    response = requests.post(request_url, json=one_payload, headers=request_headers)
    if response.status_code != 200:
        status = "failed"
        message = response.text

        logging.info("Failed to punch order with status: %s %s", status, message)
    else:
        response_body = response.json()
        customer_order_id = response_body['customer_order_id']
        logging.info(f"Successfully punched order with id: {customer_order_id}")

        if one_branch['auto_accept_p']:
            order_status = "accepted"
            action_timestamp = datetime.now()
            payment_method_id = None
            payment_method_type = None
            
            # Auto accept order
            accept_integrated_order(customer_order_id)

            success, message = customer_order_ninja.update_order_status(customer_order_id, order_status, action_timestamp, payment_method_id, payment_method_type)
            assert success, "unable to mark order as accepted"

def accept_integrated_order(customer_order_id):
    request_url = f"{os.getenv('IBLINK_API_BASE_URL')}/customer-order"
    request_headers = {
        'X-Access-Token': os.getenv('IBLINK_API_ACCESS_TOKEN'),
        'X-User-ID':os.getenv('IBLINK_API_USER_ID'),
    }
    request_body = {
        "customer_order_id": customer_order_id,
        "order_status": "accepted",
        "action_timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }
    response = requests.put(request_url, json=request_body, headers=request_headers)
    logging.info("Order acceptance attempted with status: %s", response.status_code)
