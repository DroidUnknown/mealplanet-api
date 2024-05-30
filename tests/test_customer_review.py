# import json

# from datetime import datetime

# base_api_url = "/api"

# ##########################
# # TEST - CUSTOMER REVIEW
# ##########################
# def do_get_customer_reviews(client, headers, payload):
#     """
#     Get Customer Reviews
#     """

#     response = client.post(f'{base_api_url}/customer_reviews', headers=headers, json=payload)
#     return response

# def do_scrape_customer_reviews(client, headers):
#     """
#     Scrape Customer Reviews
#     """
#     response = client.get(base_api_url + "/scrape_customer_reviews", headers=headers)
#     return response

# def do_get_customer_reviews_stats(client, headers, payload):
#     """
#     Get Customer Review Stats
#     """

#     response = client.post(f'{base_api_url}/customer_reviews_stats', headers=headers, json=payload)
#     return response

# ##########################
# # TEST CASES
# ##########################

# def test_get_customer_reviews(client, headers):
#     """
#     Test get customer_reviews
#     """
#     payload = {
#         "start_date": "2023-09-01",
#         "end_date": "2023-09-01",
#     }
#     response = do_get_customer_reviews(client, headers, payload)
#     assert response.status_code == 200
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
#     assert len(j["data"]) > 0
#     assert j["action"] == 'get_customer_reviews'

# def test_get_customer_reviews_with_filters(client, headers):
#     """
#     Test get customer_reviews
#     """
#     payload = {
#         "start_date": "2023-09-01",
#         "marketplace_id_list": [3],
#     }
#     response = do_get_customer_reviews(client, headers, payload)
#     assert response.status_code == 200
#     j = json.loads(response.data)
#     assert j["status"] == 'failed'
#     assert j["message"] == 'no rows'
#     assert j["action"] == 'get_customer_reviews'

# def test_scrape_customer_reviews(client, headers):
#     """
#     Test scrape customer_reviews
#     """
#     response = do_scrape_customer_reviews(client, headers)
#     assert response.status_code == 200
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
#     assert j["action"] == 'scrape_customer_reviews'

# def test_get_customer_reviews_stats(client, headers):
#     """
#     Test get customer_reviews_stats
#     """
#     payload = {
#         "start_date": "2023-09-01",
#         "end_date": "2023-09-01",
#         "group_by": "default"
#     }
#     response = do_get_customer_reviews_stats(client, headers, payload)
#     assert response.status_code == 200
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
#     assert len(j["data"]) > 0
#     assert j["action"] == 'get_customer_reviews_stats'