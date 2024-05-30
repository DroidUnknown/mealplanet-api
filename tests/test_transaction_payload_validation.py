import json
from transaction_request_management.transaction_request_ninja import validate_payload



def do_transaction_payload_validation(payload):
    return validate_payload(payload)

def test_transaction_payload_validation():
    file_name = "tests/testdata/payment_link_generation_payload/stripe/correct/01_menu_items_only.json"
    with open(file_name) as f:  
        menu_items_only_payload = json.load(f)
        error_list = do_transaction_payload_validation(menu_items_only_payload)
        assert len(error_list) == 0, json.dumps(error_list, indent=2)
    
    file_name = "tests/testdata/payment_link_generation_payload/stripe/correct/02_menu_items_with_modifiers.json"
    with open(file_name) as f:  
        menu_items_with_modifiers_payload = json.load(f)
        error_list = do_transaction_payload_validation(menu_items_with_modifiers_payload)
        assert len(error_list) == 0, json.dumps(error_list, indent=2)
    
    file_name = "tests/testdata/payment_link_generation_payload/stripe/correct/03_offers_only.json"
    with open(file_name) as f:  
        offers_only_payload = json.load(f)
        error_list = do_transaction_payload_validation(offers_only_payload)
        assert len(error_list) == 0, json.dumps(error_list, indent=2)
    
    file_name = "tests/testdata/payment_link_generation_payload/stripe/correct/04_offers_with_items_and_modifiers.json"
    with open(file_name) as f:  
        offers_with_items_and_modifiers_payload = json.load(f)
        error_list = do_transaction_payload_validation(offers_with_items_and_modifiers_payload)
        assert len(error_list) == 0, json.dumps(error_list, indent=2)
        