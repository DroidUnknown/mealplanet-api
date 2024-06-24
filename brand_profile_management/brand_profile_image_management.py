import os

from sqlalchemy import text
from flask import Blueprint, request, jsonify, g
from utils import jqutils, jqimage_uploader

brand_profile_image_management_blueprint = Blueprint('brand_profile_image_management', __name__)

allowed_filename_extension_list = ['jpg', 'jpeg', 'png']

@brand_profile_image_management_blueprint.route('/brand-profile-image', methods=['POST'])
def add_brand_profile_image():
    request_dict = request.form.to_dict()
    
    brand_profile_id = request_dict["brand_profile_id"]
    image_type = request_dict["image_type"]
    brand_profile_image = request.files['brand_profile_image']

    if not brand_profile_image:
        response_body = {
            "data": {},
            "action": "add_brand_profile_image",
            "status": "failed",
            "message": "No image file found"
        }
        return jsonify(response_body)

    filename = brand_profile_image.filename
    filename_parts = filename.rsplit('.', 1)
    
    filename = filename_parts[0].lower()
    file_extension = filename_parts[1].lower()
    action_timestamp = jqutils.get_utc_datetime()
    
    assert file_extension in allowed_filename_extension_list, "invalid file extension"
    
    image_bucket_name = os.getenv("S3_BUCKET_NAME")
    image_object_key = f"brand-profile-images/{brand_profile_id}/{filename}_{action_timestamp}.{file_extension}"

    # Upload image to S3 if not mocking
    if os.getenv("MOCK_S3_UPLOAD") != '1':    
        is_uploaded = jqimage_uploader.upload_fileobj(brand_profile_image, image_bucket_name, image_object_key)
        assert is_uploaded, "failed to upload item image to S3"
        brand_profile_image_url = jqimage_uploader.create_presigned_url(image_bucket_name, image_object_key)
    else:
        brand_profile_image_url = f"https://s3.amazonaws.com/{image_bucket_name}/{image_object_key}"

    db_engine = jqutils.get_db_engine()

    query = text("""
        INSERT INTO brand_profile_image (brand_profile_id, image_type, image_bucket_name, image_object_key, meta_status, creation_user_id)
        VALUES (:brand_profile_id, :image_type, :image_bucket_name, :image_object_key, :meta_status, :creation_user_id)
    """)
    with db_engine.connect() as conn:
        brand_profile_image_id = conn.execute(query, brand_profile_id=brand_profile_id, image_type=image_type, image_bucket_name=image_bucket_name, image_object_key=image_object_key, meta_status='active', creation_user_id=g.user_id).lastrowid
        assert brand_profile_image_id, "failed to insert brand profile image"

    response_body = {
        "data": {
            "brand_profile_image_id": brand_profile_image_id,
            "brand_profile_image_url": brand_profile_image_url
        },
        "action": "add_brand_profile_image",
        "status": "successful"
    }
    return jsonify(response_body)

@brand_profile_image_management_blueprint.route('/brand-profile-image/<brand_profile_image_id>', methods=['GET'])
def get_brand_profile_image(brand_profile_image_id):
    brand_profile_image_id = int(brand_profile_image_id)
    
    db_engine = jqutils.get_db_engine()
    
    # get existing brand_profile image
    query = text(f"""
        SELECT brand_profile_image_id, image_bucket_name, image_object_key, image_type
        FROM brand_profile_image
        WHERE brand_profile_image_id = :brand_profile_image_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, brand_profile_image_id=brand_profile_image_id, meta_status='active').fetchone()
        assert result, "failed to get brand_profile_image details"

    brand_profile_image_id = result['brand_profile_image_id']
    image_type = result['image_type']
    image_bucket_name = result['image_bucket_name']
    image_object_key = result['image_object_key']

    if os.getenv("MOCK_S3_UPLOAD") != '1':
        brand_profile_image_url = jqimage_uploader.create_presigned_url(image_bucket_name, image_object_key)
    else:
        brand_profile_image_url = f"https://s3.amazonaws.com/{image_bucket_name}/{image_object_key}"

    response_body = {
        "data": {
            "brand_profile_image_id": brand_profile_image_id,
            "brand_profile_image_url": brand_profile_image_url,
            "image_type": image_type
        },
        "action": "get_brand_profile_image",
        "status": "successful"
    }
    return jsonify(response_body)

@brand_profile_image_management_blueprint.route('/brand-profile/<brand_profile_id>/images', methods=['GET'])
def get_brand_profile_images_by_brand_profile(brand_profile_id):
    brand_profile_id = int(brand_profile_id)
    
    request_args = request.args
    image_type = request_args.get('image_type', None)
    
    image_type_filter_statement = ""
    if image_type:
        image_type_filter_statement = f"AND image_type = '{image_type}'"
    
    db_engine = jqutils.get_db_engine()
    
    # get brand_profile_image details
    query = text(f"""
        SELECT brand_profile_image_id, image_bucket_name, image_object_key, image_type
        FROM brand_profile_image
        WHERE brand_profile_id = :brand_profile_id
        {image_type_filter_statement}
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        results = conn.execute(query, brand_profile_id=brand_profile_id, meta_status='active').fetchall()
    
    brand_profile_image_list = []
    for brand_profile_image in results:
        brand_profile_image_id = brand_profile_image['brand_profile_image_id']
        image_type = brand_profile_image['image_type']
        image_bucket_name = brand_profile_image['image_bucket_name']
        image_object_key = brand_profile_image['image_object_key']

        if os.getenv("MOCK_S3_UPLOAD") != '1':
            brand_profile_image_url = jqimage_uploader.create_presigned_url(image_bucket_name, image_object_key)
        else:
            brand_profile_image_url = f"https://s3.amazonaws.com/{image_bucket_name}/{image_object_key}"
        
        brand_profile_image_list.append({
            "brand_profile_image_id": brand_profile_image_id,
            "brand_profile_image_url": brand_profile_image_url,
            "image_type": image_type
        })

    response_body = {
        "data": {
            "brand_profile_image_list": brand_profile_image_list
        },
        "action": "get_brand_profile_images_by_brand_profile",
        "status": "successful"
    }
    return jsonify(response_body)

@brand_profile_image_management_blueprint.route('/brand-profile-image/<brand_profile_image_id>', methods=['PUT'])
def update_brand_profile_image(brand_profile_image_id):
    brand_profile_image_id = int(brand_profile_image_id)
    
    request_dict = request.form.to_dict()
    image_type = request_dict["image_type"]
    brand_profile_image = request.files['brand_profile_image']

    db_engine = jqutils.get_db_engine()
    
    # get existing brand_profile image
    query = text(f"""
        SELECT brand_profile_id, image_bucket_name, image_object_key
        FROM brand_profile_image
        WHERE brand_profile_image_id = :brand_profile_image_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, brand_profile_image_id=brand_profile_image_id, meta_status='active').fetchone()
        assert result, "failed to get brand_profile_image details"

    brand_profile_id = result['brand_profile_id']
    old_bucket_name = result['image_bucket_name']
    old_object_key = result['image_object_key']

    filename = brand_profile_image.filename
    filename_parts = filename.rsplit('.', 1)
    
    filename = filename_parts[0].lower()
    file_extension = filename_parts[1].lower()
    action_timestamp = jqutils.get_utc_datetime()
    
    assert file_extension in allowed_filename_extension_list, "invalid file extension"
    
    image_bucket_name = os.getenv("S3_BUCKET_NAME")
    image_object_key = f"brand-profile-images/{brand_profile_id}/{filename}_{action_timestamp}.{file_extension}"

    # Upload image to S3 if not mocking
    if os.getenv("MOCK_S3_UPLOAD") != '1':
            
        is_uploaded = jqimage_uploader.upload_fileobj(brand_profile_image, image_bucket_name, image_object_key)
        assert is_uploaded, "failed to upload item image to S3"
        
        # delete the old image
        jqimage_uploader.delete_object_from_bucket(old_bucket_name, old_object_key)

        brand_profile_image_url = jqimage_uploader.create_presigned_url(image_bucket_name, image_object_key)
    else:
        brand_profile_image_url = f"https://s3.amazonaws.com/{image_bucket_name}/{image_object_key}"

    query = text("""
        UPDATE brand_profile_image
        SET image_type = :image_type,
        image_bucket_name = :image_bucket_name,
        image_object_key = :image_object_key,
        modification_user_id = :modification_user_id
        WHERE brand_profile_image_id = :brand_profile_image_id
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, image_type=image_type, image_bucket_name=image_bucket_name, image_object_key=image_object_key, modification_user_id=g.user_id, brand_profile_image_id=brand_profile_image_id).rowcount
        assert result, "failed to update brand profile image"

    response_body = {
        "data": {
            "brand_profile_image_id": brand_profile_image_id,
            "brand_profile_image_url": brand_profile_image_url
        },
        "action": "update_brand_profile_image",
        "status": "successful"
    }
    return jsonify(response_body)

@brand_profile_image_management_blueprint.route('/brand-profile-image/<brand_profile_image_id>', methods=['DELETE'])
def delete_brand_profile_image(brand_profile_image_id):
    brand_profile_image_id = int(brand_profile_image_id)
    
    db_engine = jqutils.get_db_engine()
    
    # get existing brand_profile image
    query = text(f"""
        SELECT image_bucket_name, image_object_key, meta_status
        FROM brand_profile_image
        WHERE brand_profile_image_id = :brand_profile_image_id
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, brand_profile_image_id=brand_profile_image_id, meta_status='active').fetchone()
        assert result, "failed to get brand_profile_image details"

    action_timestamp = jqutils.get_utc_datetime()
    image_bucket_name = result['image_bucket_name']
    image_object_key = result['image_object_key']
    meta_status = result['meta_status']

    if meta_status != "deleted":
        
        if os.getenv("MOCK_S3_UPLOAD") != '1':
            jqimage_uploader.delete_object_from_bucket(image_bucket_name, image_object_key)
        
        query = text("""
            UPDATE brand_profile_image
            SET meta_status = :meta_status,
            deletion_user_id = :deletion_user_id,
            deletion_timestamp = :deletion_timestamp
            WHERE brand_profile_image_id = :brand_profile_image_id
        """)
        with db_engine.connect() as conn:
            result = conn.execute(query, meta_status='deleted', deletion_user_id=g.user_id, brand_profile_image_id=brand_profile_image_id, deletion_timestamp=action_timestamp).rowcount
            assert result, "failed to update brand profile image"

    response_body = {
        "data": {
            "brand_profile_image_id": brand_profile_image_id
        },
        "action": "delete_brand_profile_image",
        "status": "successful"
    }
    return jsonify(response_body)