from utils import jqutils
from sqlalchemy import text
import json

base_api_url = "/api"

##########################
# TEST - FEATURE
########################## 
def do_get_features(client,headers):
    """
    Get Interface Types
    """
    response = client.get(base_api_url + "/features", headers=headers)
    return response

def do_get_merchant_features(client,headers, merchant_id):
    """
    Get Merchant Features
    """
    response = client.get(base_api_url + "/merchant/" + str(merchant_id) + "/features", headers=headers)
    return response

def do_update_merchant_feature(client,headers, payload):
    """
    Update Merchant Feature
    """
    response = client.put(base_api_url + "/merchant-features", headers=headers, json=payload)
    return response


##########################
# TEST CASES
########################## 

def test_get_features(client,headers):
    """
    Test get features
    """
    response = do_get_features(client,headers)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert len(j["data"]) > 0
    assert j["action"] == 'search_feature_by_filter'

def test_get_merchant_features(client,headers):
    """
    Test get features for merchant
    """
    merchant_id = 1
    response = do_get_merchant_features(client,headers, merchant_id)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'get_merchant_features'

def test_update_feature(client,headers):
    """
    Test update feature
    """
    merchant_id = 1
    response = do_get_features(client,headers)
    assert response.status_code == 200
    j = json.loads(response.data)

    assert j["status"] == 'successful'
    feature_list = j["data"]



    updated_feature_list = []
    for one_feature in feature_list:
        feature_name = one_feature["feature_name"]
        if feature_name not in ['kitchen-display-system']:
            updated_feature_list.append({
                "feature_id": one_feature["feature_id"],
                "enabled_p": 1
            })

    payload = {
        "merchant_id" : merchant_id,
        "feature_list" : updated_feature_list,
        "user_id" : 1
    }
    response = do_update_merchant_feature(client,headers, payload)
    assert response.status_code == 200
    j = json.loads(response.data)
    assert j["status"] == 'successful'
    assert j["action"] == 'update_features_by_merchant'