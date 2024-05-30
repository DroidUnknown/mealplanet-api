import json

base_api_url = "/api"

##########################
# TEST - BRANDS
##########################
def do_extract_text(client, headers, payload):
    """
    Get Upload brand menu items
    """
    cand_headers = headers.copy()
    cand_headers["Content-Type"] = "multipart/form-data"
    response = client.post(base_api_url + "/menu-ingestion/extract", headers=cand_headers, data=payload)
    return response

def test_extract_text(client, headers):
    """
    Test extract text from image
    """
    with open('tests/testdata/menus/menu_ingestion/appetizers.jpg', 'rb') as image_file:
        payload = {
            'text': None,
            'criteria': json.dumps({
                'contains_category_p': 1,
                'contains_nutritional_info_p': 0
            }),
            'image_file': image_file,
        }

        response = do_extract_text(client, headers, payload)
        assert response.status_code == 200
        
        response_body = response.json
        assert response_body['status'] == 'successful'
        assert response_body['action'] == 'extract_menu'

    with open('tests/testdata/menus/menu_ingestion/wraps.jpg', 'rb') as image_file:
        payload = {
            'text': None,
            'criteria': json.dumps({
                'contains_category_p': 1,
                'contains_nutritional_info_p': 0
            }),
            'image_file': image_file
        }

        response = do_extract_text(client, headers, payload)
        assert response.status_code == 200
        
        response_body = response.json
        assert response_body['status'] == 'successful'
        assert response_body['action'] == 'extract_menu'