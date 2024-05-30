# from careem_management import careem_ninja
# from pos_management import pos_ninja
# from utils import my_utils
# import os
# import json
# from dotenv import load_dotenv
# load_dotenv()

# merchant_id = 93
# merchant_code = 'mfl_7272'

# one_branch = {
#     "branch_id": 156,
#     "brand_id": 136,
#     "country_id": 1,
#     "facility_id": 141,
#     "marketplace_id": 3,
#     "merchant_id": 93,
#     "external_branch_id": 1051082,
#     "external_branch_code": None,
#     "merchant_code": 'mfl_7272',
#     "auto_accept_p": None
# }

# def test(one_order):
#     print("translating")
#     one_payload = careem_ninja.translate_careem_payload(one_order, one_branch)
#     print("translated order")
#     print(one_payload)
#     pos_ninja.punch_order_to_pos(merchant_id, merchant_code, one_payload, one_branch, "careem")

# # path = 'D:/repos/iblinkpay-api/test/testdata/customer_orders/careem/sample_careem_order_payload.json'

# # with open('tests/testdata/customer_orders/careem/sample_standard_item_order_payload.json') as f:
# #     one_order = json.load(f)
# #     test(one_order)

# with open('tests/testdata/customer_orders/careem/sample_modifiers_order_payload.json') as f:
#     one_order = json.load(f)
#     test(one_order)