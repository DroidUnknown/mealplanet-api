import json
import os
import pytest

from sqlalchemy import text
from datetime import datetime, timedelta

from tests.test_merchant import do_add_merchant_and_user
from utils import jqutils, generative_ai_util

def do_get_ai_model(model_type):
    return generative_ai_util.get_ai_model(model_type)

def do_check_user_quota(model_type, user_id, role_id):
    return generative_ai_util.check_user_quota(model_type, user_id, role_id)

def do_generate_text(user_prompt, system_prompt):
    return generative_ai_util.generate_text(user_prompt, system_prompt)

def do_generate_image(service_name, model_name, prompt_text, reference_image):
    return generative_ai_util.generate_image(service_name, model_name, prompt_text, reference_image)

# def do_aws_bedrock_invoke_model():
#     return generative_ai_util.aws_bedrock_invoke_model

# def do_openai_invoke_model():
#     return generative_ai_util.openai_invoke_model

# def do_hugging_face_invoke_model():
#     return generative_ai_util.hugging_face_invoke_model

##########################
# TEST CASES
##########################

model_name = ""
service_name = ""

def test_get_ai_model():
    model_type = "text"
    expected_model_name = "gpt-3.5-turbo-0301"
    expected_service_name = "openai"

    global model_name
    global service_name
    service_name, model_name = do_get_ai_model(model_type)    
    assert model_name == expected_model_name, f"model_name is {model_name}, expected {expected_model_name}"
    assert service_name == expected_service_name, f"service_name is {service_name}, expected {expected_service_name}"

def test_check_user_quota():
    user_id = 1
    model_type = "text"
    role_id = 1
    eligible_p = do_check_user_quota(model_type, user_id, role_id)
    assert eligible_p, "User should be eligible to use the model."

def test_generate_text():
    user_prompt = "help me write a brief promo message for 50%% off on chocolate cake"
    system_prompt = ""
    generated_text = do_generate_text(user_prompt, system_prompt)
    assert generated_text, "generated_text is empty"

def test_generate_image():
    prompt_text = """help me write a banner on top of the image saying 50%% off" """
    reference_image = open("tests/testdata/test_images/menu-chocolate-cake.jpg", "rb")

    image_bytes = do_generate_image(service_name, model_name, prompt_text, reference_image)
    assert image_bytes, "image_bytes is empty"

