import json
import logging
import boto3
from botocore.exceptions import ClientError

from sqlalchemy.sql import text
from utils import jqutils

import os

logger = logging.getLogger(__name__)

def __init__():
    sns_resource = boto3.resource('sns')
    self.sns_resource = sns_resource

def create_topic(name):
    sns_resource = boto3.resource('sns')

    try:
        topic = sns_resource.create_topic(Name=name)
        logger.info("Created topic %s with ARN %s.", name, topic.arn)
    except ClientError:
        logger.exception("Couldn't create topic %s.", name)
        raise
    else:
        return topic


def create_fifo_topic(name):
    sns_resource = boto3.resource('sns')
    try:
        topic = sns_resource.create_topic(Name=name, Attributes={'FifoTopic': 'true'})
        logger.info("Created topic %s with ARN %s.", name, topic.arn)
    except ClientError:
        logger.exception("Couldn't create topic %s.", name)
        raise
    else:
        return topic

def list_topics():
    sns_resource = boto3.resource('sns')
    try:
        topics_iter = sns_resource.topics.all()
        logger.info("Got topics.")
    except ClientError:
        logger.exception("Couldn't get topics.")
        raise
    else:
        return topics_iter

def delete_topic(topic):
    """
    Deletes a topic. All subscriptions to the topic are also deleted.
    """
    try:
        topic.delete()
        logger.info("Deleted topic %s.", topic.arn)
    except ClientError:
        logger.exception("Couldn't delete topic %s.", topic.arn)
        raise

def subscribe(topic, protocol, endpoint):
    try:
        subscription = topic.subscribe(
            Protocol=protocol, Endpoint=endpoint, ReturnSubscriptionArn=True)
        logger.info("Subscribed %s %s to topic %s.", protocol, endpoint, topic.arn)
    except ClientError:
        logger.exception(
            "Couldn't subscribe %s %s to topic %s.", protocol, endpoint, topic.arn)
        raise
    else:
        return subscription

# @staticmethod
def list_subscriptions(topic=None):
    sns_resource = boto3.resource('sns')
    try:
        subs_iter = topic.subscriptions.all()
        if topic is None:
            subs_iter = sns_resource.subscriptions.all()
        else:
            subs_iter = topic.subscriptions.all()
        logger.info("Got subscriptions.")
    except ClientError:
        logger.exception("Couldn't get subscriptions.")
        raise
    else:
        return subs_iter


def add_subscription_filter(subscription, attributes):
    """
    Adds a filter policy to a subscription. A filter policy is a key and a
    list of values that are allowed. When a message is published, it must have an
    attribute that passes the filter or it will not be sent to the subscription.

    :param subscription: The subscription the filter policy is attached to.
    :param attributes: A dictionary of key-value pairs that define the filter.
    """
    try:
        att_policy = {key: [value] for key, value in attributes.items()}
        subscription.set_attributes(
            AttributeName='FilterPolicy', AttributeValue=json.dumps(att_policy))
        logger.info("Added filter to subscription %s.", subscription.arn)
    except ClientError:
        logger.exception(
            "Couldn't add filter to subscription %s.", subscription.arn)
        raise


def delete_subscription(subscription):
    try:
        subscription.delete()
        logger.info("Deleted subscription %s.", subscription.arn)
    except ClientError:
        logger.exception("Couldn't delete subscription %s.", subscription.arn)
        raise

def publish_text_message(self, phone_number, message):
    """
    Publishes a text message directly to a phone number without need for a
    subscription.

    :param phone_number: The phone number that receives the message. This must be
                            in E.164 format. For example, a United States phone
                            number might be +12065550101.
    :param message: The message to send.
    :return: The ID of the message.
    """
    try:
        response = self.sns_resource.meta.client.publish(
            PhoneNumber=phone_number, Message=message)
        message_id = response['MessageId']
        logger.info("Published message to %s.", phone_number)
    except ClientError:
        logger.exception("Couldn't publish message to %s.", phone_number)
        raise
    else:
        return message_id

############################################################################
def publish_message_by_arn(topic_arn, message, attributes, message_deduplication_id):
    # message_deduplication_id = '123543'
    try:
        att_dict = {}
        for key, value in attributes.items():
            if isinstance(value, str):
                att_dict[key] = {'DataType': 'String', 'StringValue': value}
            elif isinstance(value, bytes):
                att_dict[key] = {'DataType': 'Binary', 'BinaryValue': value}

        # sns = boto3.client('sns', region_name='eu-west-1')
        sns = boto3.client('sns')

        response = sns.publish(TopicArn=topic_arn, Message=message, MessageGroupId='1001', MessageDeduplicationId=message_deduplication_id,
                               MessageAttributes=att_dict)

        message_id = response['MessageId']
        logger.info(
            "Published message with attributes %s to topic %s.", attributes,
            topic_arn)
    except ClientError:
        logger.exception("Couldn't publish message to topic %s.", topic_arn)
        raise
    else:
        return message_id

############################################################################
def publish_message(topic, message, attributes, message_deduplication_id):
    """
    Publishes a message, with attributes, to a topic. Subscriptions can be filtered
    based on message attributes so that a subscription receives messages only
    when specified attributes are present.

    :param topic: The topic to publish to.
    :param message: The message to publish.
    :param attributes: The key-value attributes to attach to the message. Values
                        must be either `str` or `bytes`.
    :return: The ID of the message.
    """
    # message_deduplication_id = '123543'
    try:
        att_dict = {}
        for key, value in attributes.items():
            if isinstance(value, str):
                att_dict[key] = {'DataType': 'String', 'StringValue': value}
            elif isinstance(value, bytes):
                att_dict[key] = {'DataType': 'Binary', 'BinaryValue': value}

        response = topic.publish(Message=message, MessageGroupId='1001', MessageDeduplicationId=message_deduplication_id,
                                 MessageAttributes=att_dict)

        message_id = response['MessageId']
        logger.info(
            "Published message with attributes %s to topic %s.", attributes,
            topic.arn)
    except ClientError:
        logger.exception("Couldn't publish message to topic %s.", topic.arn)
        raise
    else:
        return message_id


def publish_multi_message(
        topic, subject, default_message, sms_message, email_message):
    """
    Publishes a multi-format message to a topic. A multi-format message takes
    different forms based on the protocol of the subscriber. For example,
    an SMS subscriber might receive a short, text-only version of the message
    while an email subscriber could receive an HTML version of the message.

    :param topic: The topic to publish to.
    :param subject: The subject of the message.
    :param default_message: The default version of the message. This version is
                            sent to subscribers that have protocols that are not
                            otherwise specified in the structured message.
    :param sms_message: The version of the message sent to SMS subscribers.
    :param email_message: The version of the message sent to email subscribers.
    :return: The ID of the message.
    """
    try:
        message = {
            'default': default_message,
            'sms': sms_message,
            'email': email_message
        }
        response = topic.publish(
            Message=json.dumps(message), Subject=subject, MessageStructure='json')
        message_id = response['MessageId']
        logger.info("Published multi-format message to topic %s.", topic.arn)
    except ClientError:
        logger.exception("Couldn't publish message to topic %s.", topic.arn)
        raise
    else:
        return message_id


def delete_topics_and_subscriptions(topics_list):
    for one_topic in topics_list:
        topic_subs = list_subscriptions(one_topic)
        for sub in topic_subs:
            for sub in topic_subs:
                if sub.arn != 'PendingConfirmation':
                    delete_subscription(sub)
        delete_topic(one_topic)


def publish_message_on_sns_topic(topic_name, message_json, message_attributes, message_deduplication_id):


    query = text(
        """
            select topic_arn
            from sns_topic iscr
            where topic_name =:topic_name and
            meta_status = :meta_status
            """
    )
    db_engine = jqutils.get_db_engine()
    with db_engine.connect() as conn:
        result = conn.execute(query, topic_name=topic_name, meta_status="active").fetchone()
        assert result, "select topic_arn failure."

        ref_topic_arn = result["topic_arn"].strip()


        one_message_str = json.dumps(message_json)


        # message_deduplication_id = f"1001{i}"

        x = publish_message_by_arn(
            ref_topic_arn,
            one_message_str,
            message_attributes,
            message_deduplication_id
        )
        return x
