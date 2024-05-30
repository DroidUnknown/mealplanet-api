base_api_url = "/api"

##############
# TEST - MERCHANT CAMPAIGN
##############

def do_get_merchant_campaigns(client, headers, merchant_id):
    """
    Get Merchant Campaigns
    """
    response = client.get(f'{base_api_url}/active-merchant-campaigns/{merchant_id}', headers=headers)
    return response

###########
# TESTS
###########

def test_get_merchant_campaigns(client, headers):
    """
    Test get merchant campaigns
    """
    merchant_id = 1
    response = do_get_merchant_campaigns(client, headers, merchant_id)
    assert response.status_code == 200
    response_body = response.json

    assert response_body["status"] == "successful"
    assert len(response_body["merchant_campaigns"]) == 1, f"merchant campaign doesn't exists"

    merchant_campaigns = response_body["merchant_campaigns"]

    assert len(merchant_campaigns[0]["ui_element_list"]) == 1, f"ui element for merchant campaign doesn't exists"
    assert len(merchant_campaigns[0]["ui_element_list"][0]["ui_element_placement_list"]) == 1, f"ui element placement for ui element doesn't exists"