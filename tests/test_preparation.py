import json

base_api_url = "/api"

##########################
# TEST - PREPARATIONS
##########################
def do_get_preparation(client, headers, preparation_id):
    """
    Get Preparation Detail
    """
    response = client.get(base_api_url + f"/preparation/{preparation_id}", headers=headers)
    return response

def do_create_preparation(client, headers, payload):
    """
    Create Preparation
    """
    response = client.post(f"{base_api_url}/preparation", headers=headers, json=payload)
    return response

def do_update_preparation(client, headers, preparation_id, payload):
    """
    Update Preparation
    """
    response = client.put(f"{base_api_url}/preparation/{preparation_id}", headers=headers, json=payload)
    return response

def do_delete_preparation(client, headers, preparation_id):
    """
    Delete Preparation
    """
    response = client.delete(f"{base_api_url}/preparation/{preparation_id}", headers=headers)
    return response

def do_get_preparations(client, headers, filter_map={}):
    """
    Get Preparations
    """
    filter_str = ""
    if filter_map:
        filter_str = "&".join([f"{key}={value}" for key, value in filter_map.items()])
    response = client.get(f"{base_api_url}/preparations?{filter_str}", headers=headers)
    return response
