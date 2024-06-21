import logging
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class SnsWrapper:
    """Encapsulates Amazon SNS topic and subscription functions."""

    def __init__(self, sns_resource):
        """
        :param sns_resource: A Boto3 Amazon SNS resource.
        """
        self.sns_resource = sns_resource

    def get_topic(self, topic):
        """
        Lists topics for the current account.
        :return: An iterator that yields the topics.
        """
        try:
            topics_iter = self.sns_resource.topics.all()
            logger.info("Got topics.")
        except ClientError:
            logger.exception("Couldn't get topics.")
            raise
        else:
            for one_topic in topics_iter:
                if one_topic.arn == topic:
                    return one_topic
            return None

    def subscribe(self, topic, protocol, endpoint):
        """
        Subscribes an endpoint to the topic. Some endpoint types, such as email,
        must be confirmed before their subscriptions are active. When a subscription
        is not confirmed, its Amazon Resource Number (ARN) is set to
        'PendingConfirmation'.
        :param topic: The topic to subscribe to.
        :param protocol: The protocol of the endpoint, such as 'sms' or 'email'.
        :param endpoint: The endpoint that receives messages, such as a phone number
                         (in E.164 format) for SMS messages, or an email address for
                         email messages.
        :return: The newly added subscription.
        """
        topic = self.get_topic(topic)
        try:
            subscription = topic.subscribe(
                Protocol=protocol, Endpoint=endpoint, ReturnSubscriptionArn=True)
            logger.info("Subscribed %s %s to topic %s.",
                        protocol, endpoint, topic.arn)
        except ClientError:
            logger.exception(
                "Couldn't subscribe %s %s to topic %s.", protocol, endpoint, topic.arn)
            raise
        else:
            return subscription

    def publish_message(self, topic, message, attributes):
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
        topic = self.get_topic(topic)
        try:
            att_dict = {}
            for key, value in attributes.items():
                if isinstance(value, str):
                    att_dict[key] = {
                        'DataType': 'String', 'StringValue': value}
                elif isinstance(value, bytes):
                    att_dict[key] = {
                        'DataType': 'Binary', 'BinaryValue': value}
            response = topic.publish(
                Message=message, MessageAttributes=att_dict)
            message_id = response['MessageId']
            logger.info(
                "Published message with attributes %s to topic %s.", attributes,
                topic.arn)
        except ClientError:
            logger.exception(
                "Couldn't publish message to topic %s.", topic.arn)
            raise
        else:
            return message_id

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


class SesWrapper:
    """Encapsulates functions to send emails with Amazon SES."""
    def __init__(self, ses_client):
        """
        :param ses_client: A Boto3 Amazon SES client.
        """
        self.ses_client = ses_client

    def send_email(self, source, destination, subject, text, html, reply_tos=None):
        """
        Sends an email.

        Note: If your account is in the Amazon SES  sandbox, the source and
        destination email accounts must both be verified.

        :param source: The source email account.
        :param destination: The destination email account.
        :param subject: The subject of the email.
        :param text: The plain text version of the body of the email.
        :param html: The HTML version of the body of the email.
        :param reply_tos: Email accounts that will receive a reply if the recipient
                          replies to the message.
        :return: The ID of the message, assigned by Amazon SES.
        """
        send_args = {
            'Source': source,
            'Destination': destination,
            'Message': {
                'Subject': {
                    'Data': subject,
                },
                'Body': {
                    'Text': {
                        'Data': text,
                    },
                    'Html': {
                        'Data': html,
                    }
                }
            }
        }
        if reply_tos is not None:
            send_args['ReplyToAddresses'] = reply_tos
        try:
            response = self.ses_client.send_email(**send_args)
            message_id = response['MessageId']
            logger.info(
                "Sent mail %s from %s to %s.", message_id, source, destination['ToAddresses'])
        except ClientError:
            logger.exception(
                "Couldn't send mail from %s to %s.", source, destination['ToAddresses'])
            raise
        else:
            return message_id

    def send_email_with_attachments(self, source, recipients, subject, text, attachments=None):
        """
        Sends an email with attachments.

        Note: If your account is in the Amazon SES  sandbox, the source and
        recipients email accounts must both be verified.

        :param source: The source email account.
        :param recipients: The list of recipient email accounts.
        :param subject: The subject of the email.
        :param text: The plain text version of the body of the email.
        :param attachments: A list of attachments.
        :return: The ID of the message, assigned by Amazon SES.
        """
        content = MIMEMultipart()
        content["Subject"] = subject
        body = MIMEText(text, "plain")
        content.attach(body)
        if attachments:
            for file_name in attachments:
                with open(file_name, "rb") as attachment:
                    part = MIMEApplication(attachment.read())
                    base_file_name = os.path.basename(file_name)
                    part.add_header("Content-Disposition", "attachment", filename=base_file_name)
                content.attach(part)
        
        send_args = {
            'Source': source,
            'Destinations': recipients,
            'RawMessage': {
                "Data": content.as_string()
            }
        }
        try:
            response = self.ses_client.send_raw_email(**send_args)
            message_id = response['MessageId']
            logger.info(
                "Sent mail %s from %s to %s.", message_id, source, destination['ToAddresses'])
        except ClientError:
            logger.exception(
                "Couldn't send mail from %s to %s.", source, destination['ToAddresses'])
            raise
        else:
            return message_id


def get_aws_publisher(publisher_type):
    if publisher_type == "email":
        return SesWrapper(boto3.client('ses'))
    else:
        return SnsWrapper(boto3.resource('sns'))


def subscribe_new_endpoint(endpoint, topic, protocol):
    sns_publisher = get_aws_publisher("sms")

    sns_publisher.subscribe(
        topic=topic,
        protocol=protocol,
        endpoint=endpoint
    )


def publish_text_message(phone_nr, message):
    sns_publisher = get_aws_publisher("sms")
    sns_publisher.publish_text_message(phone_nr, message)

def publish_email(source, destination, subject, text, html):
    if os.getenv("MOCK_AWS_NOTIFICATIONS") != "1":
        ses_publisher = get_aws_publisher("email")
        ses_publisher.send_email(source, destination, subject, text, html)

def extract_text_from_image(image_file):
    # EXTRACT using aws textract
    if os.getenv("MOCK_AWS_TEXTRACT") == "0":
        textract_client = boto3.client('textract')
        api_response = textract_client.detect_document_text(
            Document={"Bytes": image_file.read()}
        )

        # read the response and get the related info
        extracted_data = ""
        for item in api_response["Blocks"]:
            if item["BlockType"] == "LINE":
                extracted_data += item["Text"] + "\n"
    else:
        extracted_data = "Mock extracted data"
    
    return extracted_data

def get_file_data_from_s3(bucket_name, object_key):
    s3_client = boto3.client('s3')
    try:
        file_data = s3_client.get_object(Bucket=bucket_name, Key=object_key)['Body'].read()
        file_data = file_data.decode()
    except ClientError as error:
        logging.error(error)
        file_data = None
    return file_data