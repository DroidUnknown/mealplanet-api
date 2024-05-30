import os
from sqlalchemy import text
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openai import OpenAI

from utils import jqutils, jqimage_uploader
from orchestrator_management import rule_engine

def get_ai_model(model_type):
    db_engine = jqutils.get_db_engine()

    query = text("""
        SELECT service_name, model_name
        FROM ai_model
        WHERE model_type = :model_type
        AND meta_status = :meta_status
        ORDER BY priority ASC
        LIMIT 1
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, model_type=model_type, meta_status="active").fetchone()
        service_name = result['service_name']
        model_name = result['model_name']

    return service_name, model_name

def check_user_quota(model_type, user_id, role_id):
    db_engine = jqutils.get_db_engine()
    query = text("""
        SELECT limit_quota, duration, duration_measurement_id
        FROM ai_quota_config
        WHERE role_id = :role_id
        AND model_type = :model_type
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, role_id=role_id, model_type=model_type).fetchone()
        quota = result['limit_quota']
        duration = result['duration']
        duration_measurement_id = result['duration_measurement_id']
    
    # Calculate the start date based on the duration and duration_measurement_id
    day_result = jqutils.get_record_list_by_column("day", "measurement_name", "measurement")
    month_result = jqutils.get_record_list_by_column("month", "measurement_name", "measurement")

    day_measurement_id = day_result[0]["measurement_id"]
    month_measurement_id = month_result[0]["measurement_id"]

    if duration_measurement_id == day_measurement_id:  # day
        start_date = datetime.now().date() - timedelta(days=duration-1)
    elif duration_measurement_id == month_measurement_id:  # month
        start_date = (datetime.now().date().replace(day=1) - relativedelta(months=duration-1))

    query = text("""
        SELECT usage_count
        FROM ai_user_session
        WHERE user_id = :user_id
        AND model_type = :model_type
        AND usage_date >= :start_date
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, user_id=user_id, model_type=model_type, start_date=start_date).fetchone()
        usage_count = result if result else 0

    return usage_count < quota

def generate_text(user_prompt, system_prompt=None):
    service_name, model_name = get_ai_model("text")

    if service_name == "aws":
        params = {
            "user_prompt": user_prompt
        }
        if os.getenv("MOCK_AWS_AI") == "0":
            return aws_bedrock_invoke_model(model_name, params)
    elif service_name == "openai":
        params = {
            "user_prompt": user_prompt,
            "system_prompt": system_prompt
        }
        if os.getenv("MOCK_OPENAPI") == "0":
            return openai_invoke_model(model_name, params)
        return "This is a generated text"

def generate_image(before_id, after_id, fetch_new_count, fetch_old_count):
    db_engine = jqutils.get_db_engine()

    new_after_id = after_id
    
        # query = text("""
        #     SELECT private_key
        #     FROM kaykroo_secret
        #     WHERE description = :description
        #     AND meta_status = :meta_status
        # """)
        # with db_engine.connect() as conn:
        #     result = conn.execute(query, description="token-protector-key", meta_status="active").fetchone()
        #     private_key_string_db = result['private_key']
        #     private_key_string_db_bytes = private_key_string_db.encode()

        # # Hash the payload using your private key and send it hash with stock request
        # private_key = jqsecurity.rsa_private_key_bytes__to_key(private_key_string_db_bytes)

        # data_bytes = bytes(prompt_text, 'utf-8')
        # text_hash_str, text_hash_type = jqsecurity.generate_hash_from_bytes(data_bytes, private_key)

        # if prompt_type == "image":
        #     image_bytes = prompt_image[0].read()
        #     image_hash_str, image_hash_type = jqsecurity.generate_hash_from_bytes(image_bytes, private_key)
        
    query = text("""
        SELECT ai_prompt_id
        FROM ai_prompt
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query).fetchone()
        image_prompt_id = result['ai_prompt_id'] if result else None
    
    before_id_statement = f"AND ai_generated_image_id < {before_id}" if before_id else ""

    image_url_list = []

    if image_prompt_id:
        query = text(f"""
            SELECT ai_generated_image_id, ai_prompt_id, image_bucket_name, image_object_key
            FROM ai_generated_image
            WHERE ai_prompt_id = :prompt_id
            AND meta_status = :meta_status
            AND ai_generated_image_id > :after_id
            {before_id_statement}
            ORDER BY ai_generated_image_id ASC
            LIMIT :fetch_old_count
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, prompt_id=image_prompt_id, meta_status="active", after_id=after_id, fetch_old_count=fetch_old_count).fetchall()

        for row in result:
            new_after_id = row['ai_generated_image_id']
            if os.getenv("MOCK_S3_UPLOAD") == "0":
                image_url = jqimage_uploader.create_presigned_url(row['image_bucket_name'], row['image_object_key'])
            else:
                image_url = "https://dummyimage.com/600x400/000/fff"
            image_url_list.append(image_url)

    # new_image_count = fetch_new_count + (fetch_old_count - len(image_url_list))
    # for index in range(new_image_count):
    #     # generate image prompt
    #     pass
            
    return image_url_list, new_after_id, before_id


def aws_bedrock_invoke_model(model_name, params):
    if model_name == "stability.stable-diffusion-xl-v1":
        pass

def openai_invoke_model(model_name, params):
    if os.getenv("MOCK_OPENAPI") != "0":
        return "This is a generated text"
    
    client = OpenAI()

    completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": params["system_prompt"]},
            {"role": "user", "content": params["user_prompt"]}
        ]
    )
    return completion.choices[0].message.content

def hugging_face_invoke_model(model_name, params):
    if model_name == "gpt-3.5-turbo":
        pass


def get_applicable_ai_prompt(criteria, rule_type):
    db_engine = jqutils.get_db_engine()

    query = text("""
        SELECT apr.rule_expression, ap.ai_prompt_id, ap.prompt_type, ap.prompt_text
        FROM ai_prompt_rule apr
        JOIN ai_prompt ap ON apr.ai_prompt_id = ap.ai_prompt_id
        WHERE apr.rule_type = :rule_type
        AND apr.meta_status = :meta_status
        ORDER BY apr.rule_priority ASC
    """)
    with db_engine.connect() as conn:
        results = conn.execute(query, rule_type=rule_type, meta_status="active").fetchall()

    for result in results:
        rule_expression = result['rule_expression']
        ai_prompt_id = result['ai_prompt_id']
        prompt_type = result['prompt_type']
        prompt_text = result['prompt_text']

        applicable_p = rule_engine.apply_rule_expression(rule_expression, criteria)
        if applicable_p:
            return {
                "ai_prompt_id": ai_prompt_id,
                "prompt_type": prompt_type,
                "prompt_text": prompt_text
            }
    return None
