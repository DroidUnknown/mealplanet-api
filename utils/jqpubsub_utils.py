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
import secrets

from utils import jqutils, notification_manager

from math import ceil



from flask import Flask, request, g


# publishing_queue_id = Column(Integer, primary_key=True)
#     customer_order_id = Column(Integer)
#     message = Column(String(128))
#     message_id = Column(String(128))
#     message_attributes = Column(String(128))
#     order_event = Column(String(32))
#     message_deduplication_id_str = Column(String(128))
#     meta_status = Column(String(32))

# def publish_line_item_level_event_v2(line_item_event_dict, message_attributes_dict, message_deduplication_id_str):
#     order_line_item_event = message_attributes_dict["event_name"]
#     order_line_item_id = line_item_event_dict["order_line_item_id"]
#     message_str = str(line_item_event_dict)
#     message_attributes_str = str(message_attributes_dict)


def publish_order_level_event(order_event_dict, message_attributes_dict, message_deduplication_id_str):
    if (os.environ["ORDER_LEVEL_PUBLISHER_ENABLED_P"] == 'false'):
        return
    
    order_event = message_attributes_dict["event_name"]
    customer_order_id = order_event_dict["customer_order_id"]
    message_str = str(order_event_dict)
    message_attributes_str = str(message_attributes_dict)

    # order_event = "order_created"
    pub_query = text(
                    """
                    insert into publishing_queue_order (customer_order_id, message, message_attributes, order_event, 
                    message_deduplication_id_str, meta_status)
                    values(:customer_order_id, :message, :message_attributes, :order_event, 
                    :message_deduplication_id_str, :meta_status)
                    """
                )
    db_engine = jqutils.get_db_engine()  
    with db_engine.connect() as conn:
        publishing_queue_id = conn.execute(pub_query, customer_order_id=customer_order_id, message=message_str, message_attributes=message_attributes_str, 
        order_event=order_event, message_deduplication_id_str=message_deduplication_id_str, meta_status="pending").lastrowid
        assert publishing_queue_id,  "could not insert into publishing_queue"

    order_events_topic_name = os.environ.get('ORDER_EVENTS_TOPIC_NAME')
    # publish_order_creation_event(customer_order_id, message_attributes, order_events_topic_name)
    
    # order_orchestrator.route_order(customer_order_id)
    # return customer_order_id

# def publish_order_creation_event(customer_order_id, message_attributes, order_events_topic_name):
    # one_message = {
    #     "order_id" : customer_order_id
    #     }   
    
    # order_events_topic_name = os.environ.get('ORDER_EVENTS_TOPIC_NAME')
    
    # order_events_topic_name = f'order-events.fifo'
    
    publish_result = notification_manager.publish_message_on_sns_topic(order_events_topic_name, order_event_dict,  message_attributes_dict, 
    message_deduplication_id_str)

    if len(publish_result) > 0:
        pub_update_query = text(
                    """
                    update publishing_queue_order
                    set
                    message_id = :message_id,
                    meta_status = :meta_status
                    where publishing_queue_order_id = :publishing_queue_order_id
                    
                    """
                )
        db_engine = jqutils.get_db_engine()  
        with db_engine.connect() as conn:
            update_publishing_queue_id = conn.execute(pub_update_query, message_id=publish_result, meta_status="published",
            publishing_queue_order_id=publishing_queue_id).rowcount

            assert publishing_queue_id,  "could not insert into publishing_queue_line_item"
    return

###############################################################

def publish_line_item_level_event_v2(line_item_event_dict, message_attributes_dict, message_deduplication_id_str):
    if (os.environ["LINE_ITEM_LEVEL_PUBLISHER_ENABLED_P"] == "false"):
        return
    order_line_item_event = message_attributes_dict["event_name"]
    order_line_item_id = line_item_event_dict["order_line_item_id"]
    message_str = str(line_item_event_dict)
    message_attributes_str = str(message_attributes_dict)

    order_line_item_events_topic_name = os.environ.get('ORDER_LINE_ITEM_EVENTS_TOPIC_NAME')


    pub_query = text(
                    """
                    insert into publishing_queue_line_item (order_line_item_id, message, message_attributes, order_line_item_event, 
                    message_deduplication_id_str, meta_status)
                    values(:order_line_item_id, :message, :message_attributes, :order_line_item_event, :message_deduplication_id_str, :meta_status)
                    """
                )
    db_engine = jqutils.get_db_engine()  
    with db_engine.connect() as conn:
        publishing_queue_id = conn.execute(pub_query, order_line_item_id=order_line_item_id, message=message_str,
        message_attributes=message_attributes_str, order_line_item_event=order_line_item_event, 
        message_deduplication_id_str=message_deduplication_id_str, meta_status="pending").lastrowid

        assert publishing_queue_id,  "could not insert into publishing_queue_line_item"

    publish_result = notification_manager.publish_message_on_sns_topic(order_line_item_events_topic_name, line_item_event_dict,  
    message_attributes_dict, message_deduplication_id_str)

    if len(publish_result) > 0:
        pub_update_query = text(
                    """
                    update publishing_queue_line_item
                    set
                    message_id = :message_id,
                    meta_status = :meta_status
                    where publishing_queue_line_item_id = :publishing_queue_line_item_id
                    
                    """
                )
        db_engine = jqutils.get_db_engine()  
        with db_engine.connect() as conn:
            update_publishing_queue_id = conn.execute(pub_update_query, message_id=publish_result, meta_status="published",
            publishing_queue_line_item_id=publishing_queue_id).rowcount

            assert publishing_queue_id,  "could not insert into publishing_queue_line_item"

    
    return



def publish_line_item_level_step_event(line_item_event_dict, message_attributes_dict, message_deduplication_id_str):
    if (os.environ["LINE_ITEM_STEP_LEVEL_PUBLISHER_ENABLED_P"] == "false"):
        return
    order_line_item_event = message_attributes_dict["event_name"]
    order_line_item_id = line_item_event_dict["order_line_item_id"]
    message_str = str(line_item_event_dict)
    message_attributes_str = str(message_attributes_dict)

    order_line_item_events_topic_name = os.environ.get('ORDER_LINE_ITEM_EVENTS_TOPIC_NAME')


    pub_query = text(
                    """
                    insert into publishing_queue_line_item (order_line_item_id, message, message_attributes, order_line_item_event, 
                    message_deduplication_id_str, meta_status)
                    values(:order_line_item_id, :message, :message_attributes, :order_line_item_event, :message_deduplication_id_str, :meta_status)
                    """
                )
    db_engine = jqutils.get_db_engine()  
    with db_engine.connect() as conn:
        publishing_queue_id = conn.execute(pub_query, order_line_item_id=order_line_item_id, message=message_str,
        message_attributes=message_attributes_str, order_line_item_event=order_line_item_event, 
        message_deduplication_id_str=message_deduplication_id_str, meta_status="pending").lastrowid

        assert publishing_queue_id,  "could not insert into publishing_queue_line_item"

    publish_result = notification_manager.publish_message_on_sns_topic(order_line_item_events_topic_name, line_item_event_dict,  
    message_attributes_dict, message_deduplication_id_str)

    if len(publish_result) > 0:
        pub_update_query = text(
                    """
                    update publishing_queue_line_item
                    set
                    message_id = :message_id,
                    meta_status = :meta_status
                    where publishing_queue_line_item_id = :publishing_queue_line_item_id
                    
                    """
                )
        db_engine = jqutils.get_db_engine()  
        with db_engine.connect() as conn:
            update_publishing_queue_id = conn.execute(pub_update_query, message_id=publish_result, meta_status="published",
            publishing_queue_line_item_id=publishing_queue_id).rowcount

            assert publishing_queue_id,  "could not insert into publishing_queue_line_item"

    
    return


def publish_config_event(config_event_dict, message_attributes_dict, message_deduplication_id_str):
    if (os.environ["CONFIG_LEVEL_PUBLISHER_ENABLED_P"] == "False"):
        return
    config_event = message_attributes_dict["event_name"]
    station_id = config_event_dict["station_id"]
    message_str = str(config_event_dict)
    message_attributes_str = str(message_attributes_dict)

    config_events_topic_name = os.environ.get('CONFIG_EVENTS_TOPIC_NAME')


    pub_query = text(
                    """
                    insert into publishing_queue_config (station_id, message, message_attributes, config_event, 
                    message_deduplication_id_str, meta_status)
                    values(:station_id, :message, :message_attributes, :config_event, :message_deduplication_id_str, :meta_status)
                    """
                )
    db_engine = jqutils.get_db_engine()  
    with db_engine.connect() as conn:
        publishing_queue_id = conn.execute(pub_query, station_id=station_id, message=message_str,
        message_attributes=message_attributes_str, config_event=config_event, 
        message_deduplication_id_str=message_deduplication_id_str, meta_status="pending").lastrowid

        assert publishing_queue_id,  "could not insert into publishing_queue_config"

    publish_result = notification_manager.publish_message_on_sns_topic(config_events_topic_name, config_event_dict,  
    message_attributes_dict, message_deduplication_id_str)

    if len(publish_result) > 0:
        pub_update_query = text(
                    """
                    update publishing_queue_config
                    set
                    message_id = :message_id,
                    meta_status = :meta_status
                    where publishing_queue_config_id = :publishing_queue_config_id
                    
                    """
                )
        db_engine = jqutils.get_db_engine()  
        with db_engine.connect() as conn:
            update_publishing_queue_id = conn.execute(pub_update_query, message_id=publish_result, meta_status="published",
            publishing_queue_config_id=publishing_queue_id).rowcount

            assert publishing_queue_id,  "could not insert into publishing_queue_config"

    
    return