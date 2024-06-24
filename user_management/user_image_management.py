import os

from sqlalchemy import text
from flask import Blueprint, request, jsonify, g
from utils import jqutils, jqimage_uploader

user_image_management_blueprint = Blueprint('user_image_management', __name__)

allowed_filename_extension_list = ['jpg', 'jpeg', 'png']

@user_image_management_blueprint.route('/user-image', methods=['POST'])
def add_user_image():
    request_dict = request.form.to_dict()
    
    user_id = request_dict["user_id"]
    image_type = request_dict["image_type"]
    user_image = request.files['user_image']

    if not user_image:
        response_body = {
            "data": {},
            "action": "add_user_image",
            "status": "failed",
            "message": "No image file found"
        }
        return jsonify(response_body)

    filename = user_image.filename
    filename_parts = filename.rsplit('.', 1)
    
    filename = filename_parts[0].lower()
    file_extension = filename_parts[1].lower()
    action_timestamp = jqutils.get_utc_datetime()
    
    assert file_extension in allowed_filename_extension_list, "invalid file extension"
    
    image_bucket_name = os.getenv("S3_BUCKET_NAME")
    image_object_key = f"user-images/{user_id}/{filename}_{action_timestamp}.{file_extension}"

    # Upload image to S3 if not mocking
    if os.getenv("MOCK_S3_UPLOAD") != '1':    
        is_uploaded = jqimage_uploader.upload_fileobj(user_image, image_bucket_name, image_object_key)
        assert is_uploaded, "failed to upload item image to S3"
        user_image_url = jqimage_uploader.create_presigned_url(image_bucket_name, image_object_key)
    else:
        user_image_url = f"https://s3.amazonaws.com/{image_bucket_name}/{image_object_key}"

    db_engine = jqutils.get_db_engine()

    query = text("""
        INSERT INTO user_image(user_id, image_type, image_bucket_name, image_object_key, meta_status, creation_user_id)
        VALUES(:user_id, :image_type, :image_bucket_name, :image_object_key, :meta_status, :creation_user_id)
    """)
    with db_engine.connect() as conn:
        user_image_id = conn.execute(query, user_id=user_id, image_type=image_type, image_bucket_name=image_bucket_name, image_object_key=image_object_key, meta_status='active', creation_user_id=g.user_id).lastrowid
        assert user_image_id, "failed to insert user image"

    response_body = {
        "data": {
            "user_image_id": user_image_id,
            "user_image_url": user_image_url
        },
        "action": "add_user_image",
        "status": "successful"
    }
    return jsonify(response_body)

@user_image_management_blueprint.route('/user-image/<user_image_id>', methods=['GET'])
def get_user_image(user_image_id):
    user_image_id = int(user_image_id)
    
    db_engine = jqutils.get_db_engine()
    
    # get existing user image
    query = text(f"""
        SELECT user_image_id, image_bucket_name, image_object_key, image_type
        FROM user_image
        WHERE user_image_id = :user_image_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, user_image_id=user_image_id, meta_status='active').fetchone()
        assert result, "failed to get user_image details"

    user_image_id = result['user_image_id']
    image_type = result['image_type']
    image_bucket_name = result['image_bucket_name']
    image_object_key = result['image_object_key']

    if os.getenv("MOCK_S3_UPLOAD") != '1':
        user_image_url = jqimage_uploader.create_presigned_url(image_bucket_name, image_object_key)
    else:
        user_image_url = f"https://s3.amazonaws.com/{image_bucket_name}/{image_object_key}"

    response_body = {
        "data": {
            "user_image_id": user_image_id,
            "user_image_url": user_image_url,
            "image_type": image_type
        },
        "action": "get_user_image",
        "status": "successful"
    }
    return jsonify(response_body)

@user_image_management_blueprint.route('/user/<user_id>/images', methods=['GET'])
def get_user_images_by_user(user_id):
    user_id = int(user_id)
    
    request_args = request.args
    image_type = request_args.get('image_type', None)
    
    image_type_filter_statement = ""
    if image_type:
        image_type_filter_statement = f"AND image_type = '{image_type}'"
    
    db_engine = jqutils.get_db_engine()
    
    # get user_image details
    query = text(f"""
        SELECT user_image_id, image_bucket_name, image_object_key, image_type
        FROM user_image
        WHERE user_id = :user_id
        {image_type_filter_statement}
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        results = conn.execute(query, user_id=user_id, meta_status='active').fetchall()
    
    user_image_list = []
    for user_image in results:
        user_image_id = user_image['user_image_id']
        image_type = user_image['image_type']
        image_bucket_name = user_image['image_bucket_name']
        image_object_key = user_image['image_object_key']

        if os.getenv("MOCK_S3_UPLOAD") != '1':
            user_image_url = jqimage_uploader.create_presigned_url(image_bucket_name, image_object_key)
        else:
            user_image_url = f"https://s3.amazonaws.com/{image_bucket_name}/{image_object_key}"
        
        user_image_list.append({
            "user_image_id": user_image_id,
            "user_image_url": user_image_url,
            "image_type": image_type
        })

    response_body = {
        "data": {
            "user_image_list": user_image_list
        },
        "action": "get_user_images_by_user",
        "status": "successful"
    }
    return jsonify(response_body)

@user_image_management_blueprint.route('/user-image/<user_image_id>', methods=['PUT'])
def update_user_image(user_image_id):
    user_image_id = int(user_image_id)
    
    request_dict = request.form.to_dict()
    image_type = request_dict["image_type"]
    user_image = request.files['user_image']

    db_engine = jqutils.get_db_engine()
    
    # get existing user image
    query = text(f"""
        SELECT user_id, image_bucket_name, image_object_key
        FROM user_image
        WHERE user_image_id = :user_image_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, user_image_id=user_image_id, meta_status='active').fetchone()
        assert result, "failed to get user_image details"

    user_id = result['user_id']
    old_bucket_name = result['image_bucket_name']
    old_object_key = result['image_object_key']

    filename = user_image.filename
    filename_parts = filename.rsplit('.', 1)
    
    filename = filename_parts[0].lower()
    file_extension = filename_parts[1].lower()
    action_timestamp = jqutils.get_utc_datetime()
    
    assert file_extension in allowed_filename_extension_list, "invalid file extension"
    
    image_bucket_name = os.getenv("S3_BUCKET_NAME")
    image_object_key = f"user-images/{user_id}/{filename}_{action_timestamp}.{file_extension}"

    # Upload image to S3 if not mocking
    if os.getenv("MOCK_S3_UPLOAD") != '1':
            
        is_uploaded = jqimage_uploader.upload_fileobj(user_image, image_bucket_name, image_object_key)
        assert is_uploaded, "failed to upload item image to S3"
        
        # delete the old image
        jqimage_uploader.delete_object_from_bucket(old_bucket_name, old_object_key)

        user_image_url = jqimage_uploader.create_presigned_url(image_bucket_name, image_object_key)
    else:
        user_image_url = f"https://s3.amazonaws.com/{image_bucket_name}/{image_object_key}"

    query = text("""
        UPDATE user_image
        SET image_type = :image_type,
        image_bucket_name = :image_bucket_name,
        image_object_key = :image_object_key,
        modification_user_id = :modification_user_id
        WHERE user_image_id = :user_image_id
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, image_type=image_type, image_bucket_name=image_bucket_name, image_object_key=image_object_key, modification_user_id=g.user_id, user_image_id=user_image_id).rowcount
        assert result, "failed to update user image"

    response_body = {
        "data": {
            "user_image_id": user_image_id,
            "user_image_url": user_image_url
        },
        "action": "update_user_image",
        "status": "successful"
    }
    return jsonify(response_body)

@user_image_management_blueprint.route('/user-image/<user_image_id>', methods=['DELETE'])
def delete_user_image(user_image_id):
    user_image_id = int(user_image_id)
    
    db_engine = jqutils.get_db_engine()
    
    # get existing user image
    query = text(f"""
        SELECT image_bucket_name, image_object_key, meta_status
        FROM user_image
        WHERE user_image_id = :user_image_id
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, user_image_id=user_image_id, meta_status='active').fetchone()
        assert result, "failed to get user_image details"

    action_timestamp = jqutils.get_utc_datetime()
    image_bucket_name = result['image_bucket_name']
    image_object_key = result['image_object_key']
    meta_status = result['meta_status']

    if meta_status != "deleted":
        
        if os.getenv("MOCK_S3_UPLOAD") != '1':
            jqimage_uploader.delete_object_from_bucket(image_bucket_name, image_object_key)
        
        query = text("""
            UPDATE user_image
            SET meta_status = :meta_status,
            deletion_user_id = :deletion_user_id,
            deletion_timestamp = :deletion_timestamp
            WHERE user_image_id = :user_image_id
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, meta_status='deleted', deletion_user_id=g.user_id, user_image_id=user_image_id, deletion_timestamp=action_timestamp).rowcount
            assert result, "failed to update user image"

    response_body = {
        "data": {
            "user_image_id": user_image_id
        },
        "action": "delete_user_image",
        "status": "successful"
    }
    return jsonify(response_body)