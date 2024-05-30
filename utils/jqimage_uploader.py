import os
import boto3
import botocore
import logging

from botocore.exceptions import ClientError

def upload_fileobj(file, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    if os.getenv("MOCK_S3_UPLOAD") != "0":
        return True
    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_fileobj(file, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

def put_object(file, bucket, object_name=None):
    if os.getenv("MOCK_S3_UPLOAD") != "0":
        return True
    # Upload the file
    s3_client = boto3.client('s3')
    try:
        s3_client.put_object(Body=file, Bucket=bucket, Key=object_name)
    except ClientError as error:
        logging.error(error)
        return False
    return True

def create_bucket(bucket_name, aws_region='ap-southeast-1'):
    s3_client = boto3.client('s3')
    s3_client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={'LocationConstraint': aws_region})


def check_bucket_exists(bucket_name):
    s3_client = boto3.resource('s3')
    bucket = s3_client.Bucket(bucket_name)
    exists = True
    try:
        s3_client.meta.client.head_bucket(Bucket=bucket_name)
    except botocore.exceptions.ClientError as e:
        # If a client error is thrown, then check that it was a 404 error.
        # If it was a 404 error, then the bucket does not exist.
        error_code = e.response['Error']['Code']
        if error_code == '404':
            exists = False
    
    return exists


def delete_bucket(bucket_name):
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)

    for key in bucket.objects.all():
        key.delete()
    bucket.delete()

def get_keys(bucket_name):
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)
    return bucket.objects.all()


def delete_object_from_bucket(bucket_name, object_key):
    s3 = boto3.resource('s3')
    s3.Object(bucket_name, object_key).delete()


def create_presigned_url(bucket_name, object_name, expiration=3600):
    """Generate a presigned URL to share an S3 object

    :param bucket_name: string
    :param object_name: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """

    # Generate a presigned URL for the S3 object
    s3_client = boto3.client('s3')
    try:
        response = s3_client.generate_presigned_url('get_object', Params={
                        'Bucket': bucket_name,
                        'Key': object_name
                    }, ExpiresIn=expiration)
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return response

def read_file_content(bucket_name, object_key):
    s3 = boto3.resource('s3')
    obj = s3.Object(bucket_name, object_key)
    return obj.get()['Body'].read()