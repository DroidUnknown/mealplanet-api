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

from flask import Flask, request, g

import boto3

from botocore.exceptions import ClientError
import logging

import time

def create_fifo_queue(queue_name):
    # Get the service resource
    sqs = boto3.resource('sqs')
    # Create the queue. This returns an SQS.Queue instance
    # queue = sqs.create_queue(QueueName=queue_name, Attributes={'DelaySeconds': '5'})
    queue = sqs.create_queue(QueueName= queue_name, Attributes={'FifoQueue': 'true'})
    # You can now access identifiers and attributes
    return queue

def create_queue(queue_name):
    # Get the service resource
    sqs = boto3.resource('sqs')
    queue = sqs.create_queue(QueueName=queue_name)
    # You can now access identifiers and attributes
    return queue


def get_queue(queue_name):
    sqs = boto3.resource('sqs')
    queue = sqs.get_queue_by_name(QueueName=queue_name)
    return


def list_queues():
    sqs = boto3.resource('sqs')
    return sqs.queues.all()

def send_message(queue_name, message_body, message_deduplication_id):
        # Get the service resource
    sqs = boto3.resource('sqs')
    # Get the queue
    queue = sqs.get_queue_by_name(QueueName=queue_name)

    # Create a new message
    response = queue.send_message(MessageBody=message_body, MessageGroupId='1001', MessageDeduplicationId=message_deduplication_id)

    # The response is NOT a resource, but gives you a message ID and MD5
    return response

def get_messages(queue_name):
    # Get the service resource
    sqs = boto3.resource('sqs')

    # Get the queue
    queue = sqs.get_queue_by_name(QueueName=queue_name)

    for message in queue.receive_messages():
        # Get the custom author message attribute if it was set
        author_text = ''
        # Print out the body and author (if set)

        # Let the queue know that the message is processed
        message.delete()

def set_attributes(queue_url, attribute_key, attribute_value):
    client = boto3.client('sqs')
    
    response = client.set_queue_attributes(
    QueueUrl=queue_url,
    Attributes={
        attribute_key: attribute_value
    }
)

def delete_queue(queue_url):
    try:
        client = boto3.client('sqs')
        response = client.delete_queue(QueueUrl=queue_url)
    except:
        return

def delete_queues_by_list(queue_list):
    # queue_list = list_queues()
    # time.sleep(10)
    for one_queue in queue_list:
        delete_queue(one_queue.url)
        
        # delete_queue_v2(one_queue.url)

        
    
    