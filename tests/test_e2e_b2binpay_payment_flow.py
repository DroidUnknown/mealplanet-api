import json
import random

from sqlalchemy import text

from tests.test_transaction_request import do_create_payment_transaction_request, do_get_transaction_request, do_update_payment_transaction_request, do_update_payment_transaction_request_currency, do_cancel_transaction_request
from tests.test_merchant import do_add_merchant_and_user
from tests.test_b2binpay import do_handle_invoice_webhook
from tests.test_merchant import do_get_merchant_balance
from tests import test_merchant_dashboard
from utils import jqutils

base_api_url = "/api"

##############

##############

def validate_calculations(merchant_transaction_id, b2binpay_invoice_id, expectations):

    db_engine = jqutils.get_db_engine()

    # Get the actual calculations for the merchant transaction
    query = text("""
        SELECT mt.payable_amount, mt.paid_amount, mt.discount_amount, mt.tax_amount, mt.tip_amount, mt.charge_amount,
        mtd.paid_by_merchant_p, mtd.actual_merchant_comission_amount, mtd.actual_service_provider_commission_amount, mtd.actual_merchant_share_amount,
        mtd.actual_total_commission_amount, mt.merchant_id, mt.service_provider_payment_method_currency_map_id, sppmc.service_provider_id
        FROM merchant_transaction mt
        JOIN merchant_transaction_detail mtd ON mt.merchant_transaction_id = mtd.merchant_transaction_id
        JOIN service_provider_payment_method_currency_map sppmc ON mt.service_provider_payment_method_currency_map_id = sppmc.service_provider_payment_method_currency_map_id
        WHERE mt.merchant_transaction_id = :merchant_transaction_id
        AND mtd.b2binpay_invoice_id = :b2binpay_invoice_id
        AND mt.meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, merchant_transaction_id=merchant_transaction_id, b2binpay_invoice_id=b2binpay_invoice_id, meta_status="active").fetchone()
        assert result, "unable to get merchant transaction details"

        merchant_id = result["merchant_id"]
        service_provider_id = result["service_provider_id"]
        service_provider_payment_method_currency_map_id = result["service_provider_payment_method_currency_map_id"]
        transaction_calculation_details = {
            "payable_amount": jqutils.round_half_up(float(result["payable_amount"]), 2),
            "paid_amount": jqutils.round_half_up(float(result["paid_amount"]), 2),
            "discount_amount": jqutils.round_half_up(float(result["discount_amount"]), 2),
            "tax_amount": jqutils.round_half_up(float(result["tax_amount"]), 2),
            "tip_amount": jqutils.round_half_up(float(result["tip_amount"]), 2),
            "charge_amount": jqutils.round_half_up(float(result["charge_amount"]), 2),
            "paid_by_merchant_p": result["paid_by_merchant_p"],
            "actual_merchant_commission_amount": jqutils.round_half_up(float(result["actual_merchant_comission_amount"]), 2),
            "actual_service_provider_commission_amount": jqutils.round_half_up(float(result["actual_service_provider_commission_amount"]), 2),
            "actual_total_commission_amount": jqutils.round_half_up(float(result["actual_total_commission_amount"]), 2),
            "actual_merchant_share_amount": jqutils.round_half_up(float(result["actual_merchant_share_amount"]), 2),
        }

    """
    Get commission rates for this merchant
    """
    query = text("""
        SELECT minimum_transaction_amount, maximum_transaction_amount, commission_cap_amount, commission_percentage,
        fixed_commission, currency_id
        FROM merchant_commission
        WHERE merchant_id = :merchant_id
        AND service_provider_id = :service_provider_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        results = conn.execute(query, merchant_id=merchant_id, service_provider_id=service_provider_id, meta_status="active").fetchall()
        assert results, "unable to get merchant commission rates"

    commission_rates = []
    for one_row in results:
        commission_rates.append({
            "minimum_transaction_amount": jqutils.round_half_up(float(one_row["minimum_transaction_amount"]), 2),
            "maximum_transaction_amount": one_row["maximum_transaction_amount"],
            "commission_cap_amount": one_row["commission_cap_amount"],
            "commission_percentage": jqutils.round_half_up(float(one_row["commission_percentage"]), 2),
            "fixed_commission": jqutils.round_half_up(float(one_row["fixed_commission"]), 2),
            "currency_id": one_row["currency_id"]
        })

    """
    Get commission rates for Service Provider
    """
    query = text("""
        SELECT minimum_transaction_amount, maximum_transaction_amount, commission_cap_amount, commission_percentage,
        fixed_commission
        FROM service_provider_commission
        WHERE service_provider_payment_method_currency_map_id = :service_provider_payment_method_currency_map_id
        AND meta_status = :meta_status
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, service_provider_payment_method_currency_map_id=service_provider_payment_method_currency_map_id, meta_status="active").fetchone()
        assert result, "unable to get service provider commission rates"

    service_provider_commission_rates = {
        "minimum_transaction_amount": jqutils.round_half_up(float(result["minimum_transaction_amount"]), 2),
        "maximum_transaction_amount": result["maximum_transaction_amount"],
        "commission_cap_amount": result["commission_cap_amount"],
        "commission_percentage": jqutils.round_half_up(float(result["commission_percentage"]), 2),
        "fixed_commission": jqutils.round_half_up(float(result["fixed_commission"]), 2),
    }

    # validate these calculations with the expected calculations
    # note: payable amount will be greater than the amount in the payload because customer will pay the additional service charges
    assert transaction_calculation_details["paid_amount"] == expectations["paid_amount"], "paid_amount mismatch"
    assert transaction_calculation_details["discount_amount"] == expectations["discount_amount"], "discount_amount mismatch"

    if expectations["tip_amount"] == 0 and expectations["default_tip_amount"] > 0:
        assert transaction_calculation_details["charge_amount"] == expectations["original_payable_amount"] + expectations["discount_amount"], "charge_amount mismatch"
        assert transaction_calculation_details["tip_amount"] == expectations["default_tip_amount"], "tip_amount mismatch"
    else:
        assert transaction_calculation_details["charge_amount"] == expectations["original_payable_amount"] + expectations["discount_amount"] - expectations["tip_amount"], "charge_amount mismatch"
        assert transaction_calculation_details["tip_amount"] == expectations["tip_amount"], "tip_amount mismatch"

    # determine which commission rule will apply
    commission_rule = None
    for one_rule in commission_rates:
        cand_payable_amount = transaction_calculation_details["payable_amount"]
        cand_min_amount = one_rule["minimum_transaction_amount"]
        cand_max_amount = one_rule["maximum_transaction_amount"]
        if cand_payable_amount >= cand_min_amount:
            if cand_max_amount:
                if cand_payable_amount <= cand_max_amount:
                    commission_rule = one_rule
                    break
            else:
                commission_rule = one_rule
                break

    # calculate iblinkpay commission
    if expectations["tip_amount"] == 0 and expectations["default_tip_amount"] > 0:
        expected_iblinkpay_commission = jqutils.round_half_up(((expectations["original_payable_amount"] + expectations["default_tip_amount"]) * (commission_rule["commission_percentage"] / 100.0)) + commission_rule["fixed_commission"], 2)
    else:
        expected_iblinkpay_commission = jqutils.round_half_up((expectations["original_payable_amount"] * (commission_rule["commission_percentage"] / 100.0)) + commission_rule["fixed_commission"], 2)

    if commission_rule["commission_cap_amount"]:
        if expected_iblinkpay_commission > commission_rule["commission_cap_amount"]:
            expected_iblinkpay_commission = jqutils.round_half_up(commission_rule["commission_cap_amount"], 2)

    # calculate new payable amount
    if transaction_calculation_details["paid_by_merchant_p"]:
        if expectations["tip_amount"] == 0 and expectations["default_tip_amount"] > 0:
            new_payable_amount = expectations["original_payable_amount"] + expectations["default_tip_amount"]
        else:
            new_payable_amount = expectations["original_payable_amount"]
    else:
        if expectations["tip_amount"] == 0 and expectations["default_tip_amount"] > 0:
            subtotal = expectations["original_payable_amount"] + expectations["default_tip_amount"] + expected_iblinkpay_commission
        else:
            subtotal = expectations["original_payable_amount"] + expected_iblinkpay_commission

        new_payable_amount = ( subtotal + float(jqutils.round_half_up(service_provider_commission_rates["fixed_commission"], 2)) ) / ( 1 - (service_provider_commission_rates["commission_percentage"] / 100.0) )

    new_payable_amount = float(jqutils.round_half_up(new_payable_amount, 2))
    calculated_tax = jqutils.round_half_up(new_payable_amount - (new_payable_amount / 1.05), 2)
    assert transaction_calculation_details["tax_amount"] == calculated_tax, "tax_amount mismatch"

    # calculate service provider commission
    expected_service_provider_commission = jqutils.round_half_up( float(jqutils.round_half_up((new_payable_amount * service_provider_commission_rates["commission_percentage"]) / 100.0, 2 )) + float(jqutils.round_half_up(service_provider_commission_rates["fixed_commission"], 2)), 2)

    # overall expected commission
    expected_total_commission = jqutils.round_half_up(expected_iblinkpay_commission + expected_service_provider_commission, 2)

    # calculate merchant share
    expected_merchant_share = jqutils.round_half_up(new_payable_amount - expected_total_commission, 2)

    assert expected_iblinkpay_commission == transaction_calculation_details["actual_merchant_commission_amount"], "actual_merchant_comission_amount mismatch"
    assert expected_service_provider_commission == transaction_calculation_details["actual_service_provider_commission_amount"], "actual_service_provider_commission_amount mismatch"
    assert expected_total_commission == transaction_calculation_details["actual_total_commission_amount"], "actual_total_commission_amount mismatch"
    assert expected_merchant_share == transaction_calculation_details["actual_merchant_share_amount"], "actual_merchant_share_amount mismatch"

    if transaction_calculation_details["paid_by_merchant_p"]:
        if expectations["tip_amount"] == 0 and expectations["default_tip_amount"] > 0:
            assert transaction_calculation_details["payable_amount"] == expectations["original_payable_amount"] + expectations["default_tip_amount"], "payable_amount mismatch"
        else:
            assert transaction_calculation_details["payable_amount"] == expectations["original_payable_amount"], "payable_amount mismatch"

        assert transaction_calculation_details["payable_amount"] == new_payable_amount, "payable_amount mismatch"
        assert transaction_calculation_details["payable_amount"] + transaction_calculation_details["discount_amount"] - transaction_calculation_details["tip_amount"] == transaction_calculation_details["charge_amount"], "charge_amount mismatch"
    else:
        if expectations["tip_amount"] == 0 and expectations["default_tip_amount"] > 0:
            assert transaction_calculation_details["payable_amount"] == expectations["original_payable_amount"] + expectations["default_tip_amount"] + expected_total_commission, "payable_amount mismatch"
        else:
            assert transaction_calculation_details["payable_amount"] == expectations["original_payable_amount"] + expected_total_commission, "payable_amount mismatch"

        assert transaction_calculation_details["payable_amount"] == new_payable_amount, "payable_amount mismatch"
        assert transaction_calculation_details["payable_amount"] - transaction_calculation_details["actual_total_commission_amount"] + transaction_calculation_details["discount_amount"] - transaction_calculation_details["tip_amount"] == transaction_calculation_details["charge_amount"], "charge_amount mismatch"

    assert transaction_calculation_details["payable_amount"] == new_payable_amount, "new_payable_amount mismatch"

    validated_calculations = {
        "service_charges": "paid by " + ("merchant" if transaction_calculation_details["paid_by_merchant_p"] else "customer"),
        "original_payable_amount": expectations["original_payable_amount"],
        "new_payable_amount": transaction_calculation_details["payable_amount"],
        "paid_amount": transaction_calculation_details["paid_amount"],
        "discount_amount": transaction_calculation_details["discount_amount"],
        "tax_amount": transaction_calculation_details["tax_amount"],
        "tip_amount": transaction_calculation_details["tip_amount"],
        "charge_amount": transaction_calculation_details["charge_amount"],
        "actual_merchant_comission_amount": transaction_calculation_details["actual_merchant_commission_amount"],
        "actual_service_provider_commission_amount": transaction_calculation_details["actual_service_provider_commission_amount"],
        "actual_total_commission_amount": transaction_calculation_details["actual_total_commission_amount"],
        "actual_merchant_share_amount": transaction_calculation_details["actual_merchant_share_amount"],
        "paid_by_merchant_p": transaction_calculation_details["paid_by_merchant_p"],
    }

    return validated_calculations


def generate_merchant(client, connect_account_p, default_currency_id, default_country_id, commission_paid_by_merchant_p, default_tip):

    """
    Create New Merchant (Normal)
    """
    logged_in_user_details, merchant_details, logged_in_order_panel_details, logged_in_marketplace_details = do_add_merchant_and_user(client, connect_account_p, default_currency_id=default_currency_id, default_country_id=default_country_id, commission_paid_by_merchant_p=commission_paid_by_merchant_p, default_tip=default_tip)

    user_headers = {
        "X-User-Id": logged_in_user_details["user_id"],
        "X-Api-Key": logged_in_user_details["merchant_api_key"]
    }

    return {
        "logged_in_user_details": logged_in_user_details,
        "merchant_details": merchant_details,
        "logged_in_order_panel_details": logged_in_order_panel_details,
        "logged_in_marketplace_details": logged_in_marketplace_details,
        "user_headers": user_headers,
        "connect_account_p": connect_account_p,
        "default_currency": {
            "default_currency_id": default_currency_id,
            "currency_alpha_3": jqutils.get_column_by_id(str(default_currency_id),"currency_alpha_3","currency")
        },
        "default_country_id": default_country_id,
        "commission_paid_by_merchant_p": commission_paid_by_merchant_p,
        "default_tip": default_tip
    }

##############
# TEST-CASE
##############

def test_e2e_normal_transaction_flow(client):

    db_engine = jqutils.get_db_engine()

    """
    Generate Merchant List
    """
    logged_in_user_details, merchant_details, logged_in_order_panel_details, logged_in_marketplace_details = do_add_merchant_and_user(client)

    merchant_list = []

    # AED
    merchant_list.append(generate_merchant(client, connect_account_p=0, default_currency_id=1, default_country_id=1, commission_paid_by_merchant_p=0, default_tip=0))
    merchant_list.append(generate_merchant(client, connect_account_p=0, default_currency_id=1, default_country_id=1, commission_paid_by_merchant_p=0, default_tip=1))
    merchant_list.append(generate_merchant(client, connect_account_p=0, default_currency_id=1, default_country_id=1, commission_paid_by_merchant_p=1, default_tip=0))
    merchant_list.append(generate_merchant(client, connect_account_p=0, default_currency_id=1, default_country_id=1, commission_paid_by_merchant_p=1, default_tip=1))

    """
    Correct 'item_list' so sum of all prices match 'payable_amount'
    """
    test_file_list = [
        "tests/testdata/payment_link_generation_payload/b2binpay/correct/00_no_item_breakdown.json",
        "tests/testdata/payment_link_generation_payload/b2binpay/correct/01_menu_items_only.json",
        "tests/testdata/payment_link_generation_payload/b2binpay/correct/02_menu_items_with_modifiers.json",
        "tests/testdata/payment_link_generation_payload/b2binpay/correct/03_offers_only.json",
        "tests/testdata/payment_link_generation_payload/b2binpay/correct/04_offers_with_items_and_modifiers.json",
        "tests/testdata/payment_link_generation_payload/b2binpay/correct/05_all_item_types.json",
        "tests/testdata/payment_link_generation_payload/b2binpay/correct/06_all_item_types_for_payment_point.json"
    ]

    test_count = 1
    print("\n")
    for one_merchant in merchant_list:
        user_headers = one_merchant["user_headers"]
        merchant_details = one_merchant["merchant_details"]
        default_tip = one_merchant["default_tip"]
        commission_paid_by_merchant_p = one_merchant['commission_paid_by_merchant_p']
        connect_account_p = one_merchant['connect_account_p']

        # tip_settings
        default_tip_amount = 5
        default_percentage_p = 1
        equivalent_currency_id = 2

        for one_test_file in test_file_list:
            with open(one_test_file) as f:
                transaction_payload = json.load(f)
                transaction_payload["payment_details"]["currency_name"] = one_merchant["default_currency"]["currency_alpha_3"]
                payable_amount = transaction_payload["payment_details"]["payable_amount"]
                discount_amount = transaction_payload["payment_details"]["discount_amount"]
                tax_amount = transaction_payload["payment_details"]["tax_amount"]
                tip_amount = transaction_payload["payment_details"]["tip_amount"]
                calculated_tip_amount = None

                if default_tip:
                    if tip_amount == 0 and default_tip_amount > 0:
                        if default_percentage_p == 1:
                            calculated_tip_amount = float(payable_amount) * (float(default_tip_amount)/100)
                        else:
                            calculated_tip_amount = float(default_tip_amount)

            print(f"Test Case: {'%02d' % (test_count,)}, Connect Account: {connect_account_p}, Commission Paid By Merchant: {commission_paid_by_merchant_p}, Default Tip: {default_tip}, tip_amount: {tip_amount}")
            test_count += 1

            response = do_create_payment_transaction_request(client, user_headers, transaction_payload)
            j = json.loads(response.data)
            assert j["status"] == 'successful'
            assert "payment_url" in j

            merchant_transaction_id = j["merchant_transaction_id"]
            b2binpay_invoice_id = j["b2binpay_invoice_id"]

            # VALIDATE CALCULATIONS
            expectations = {
                "original_payable_amount": payable_amount,
                "paid_amount": 0,
                "discount_amount": discount_amount,
                "tip_amount": tip_amount,
                "default_tip_amount": calculated_tip_amount if calculated_tip_amount else 0,
            }
            validated_calculations = validate_calculations(merchant_transaction_id, b2binpay_invoice_id, expectations)

            original_payable_amount = validated_calculations["original_payable_amount"]
            new_payable_amount = validated_calculations["new_payable_amount"]
            service_charges = validated_calculations["actual_total_commission_amount"]
            charge_amount = validated_calculations["charge_amount"]
            discount_amount = validated_calculations["discount_amount"]
            tip_amount = validated_calculations["tip_amount"]

            print(f"Original Amount: {original_payable_amount}, New Amount: {new_payable_amount}, Service Charges: {service_charges}, Charge Amount: {charge_amount}, Discount Amount: {discount_amount}, Tip Amount: {tip_amount}\n")

            # """
            # Sending Stripe Payment Intent 'CREATE' Event To Webhook
            # """
            # query = text("""
            #     SELECT si.stripe_intent_id, si.stripe_intent_reference_number, mtc.stripe_customer_id, m.merchant_code
            #     FROM stripe_intent si
            #     JOIN merchant_transaction mt ON mt.merchant_transaction_id = si.merchant_transaction_id
            #     JOIN merchant m ON m.merchant_id = mt.merchant_id
            #     JOIN merchant_transaction_customer mtc ON mtc.merchant_transaction_id = si.merchant_transaction_id
            #     WHERE si.merchant_transaction_id = :merchant_transaction_id
            #     AND si.parent_stripe_intent_id IS NULL
            #     AND si.meta_status = :meta_status
            # """)
            # with db_engine.connect() as conn:
            #     result = conn.execute(query, merchant_transaction_id=merchant_transaction_id, meta_status="active").fetchone()
            #     assert result, "Stripe Intent not found for this transaction"
            #     stripe_intent_id = result["stripe_intent_id"]
            #     stripe_intent_reference_number = result["stripe_intent_reference_number"]
            #     stripe_customer_id = result["stripe_customer_id"]
            #     merchant_code = result["merchant_code"]

            # # payment request initiated
            # with open(f'tests/testdata/stripe/normal/sample_intent_created_webhook_response.json') as f:
            #     sample_payment_request_webhook_response = json.load(f)
            #     sample_payment_request_webhook_response["data"]["object"]["id"] = stripe_intent_reference_number
            #     sample_payment_request_webhook_response["data"]["object"]["amount"] = validated_calculations["new_payable_amount"] * 100
            #     sample_payment_request_webhook_response["data"]["object"]["customer"] = stripe_customer_id
            #     sample_payment_request_webhook_response["data"]["object"]["metadata"]["merchant_code"] = merchant_code
            #     sample_payment_request_webhook_response["data"]["object"]["currency"] = one_merchant["default_currency"]["currency_alpha_3"]

            #     response = do_handle_payment_intent_webhook(client,sample_payment_request_webhook_response)
            #     assert response.status_code == 200
            #     response_body = json.loads(response.data.decode("utf-8"))
            #     assert "success" in response_body,"Stripe Payment Intent Creation webhook failed"
            #     assert response_body["success"] == True, f"Stripe Payment Intent Creation webhook failed"
            
            # # validate the status for intent changed to 'requires_payment_method' after creation event
            # query = text("""
            #     SELECT intent_status
            #     FROM stripe_intent
            #     WHERE stripe_intent_id = :stripe_intent_id
            #     AND meta_status = :meta_status
            # """)
            # with db_engine.connect() as conn:
            #     result = conn.execute(query, stripe_intent_id=stripe_intent_id, meta_status="active").fetchone()
            #     assert result, "Stripe Intent not found for this transaction"
            #     assert result["intent_status"] == "requires_payment_method", "Stripe Intent not in correct status"

            # Extracting transaction code from payment-link
            splitted_str_list = j["payment_url"].split("/")
            transaction_code = splitted_str_list[len(splitted_str_list)-1]

            """
            Get Transaction Request Details
            """
            response = do_get_transaction_request(client, transaction_code)
            assert response.status_code == 200
            response_body = response.json

            assert response_body["status"] == 'successful'
            assert "feature_list" in response_body["data"]
            assert "merchant_details" in response_body["data"]
            assert len(response_body["data"]["item_list"]) == len(transaction_payload["item_list"])
            assert len(response_body["data"]["offer_list"]) == len(transaction_payload["offer_list"])
            assert merchant_transaction_id == response_body["data"]["merchant_transaction_id"]

            b2binpay_invoice_id = response_body["data"]["b2binpay_invoice_id"]

            assert float(response_body["data"]["payable_amount"]) == validated_calculations["new_payable_amount"], "Payable amount is not correct"
            assert float(response_body["data"]["charge_amount"]) == validated_calculations["charge_amount"], "Charge amount is not correct"
            assert float(response_body["data"]["paid_amount"]) == validated_calculations["paid_amount"], "Paid amount is not correct"
            assert float(response_body["data"]["tip_amount"]) == validated_calculations["tip_amount"], "Tip amount is not correct"
            assert float(response_body["data"]["discount_amount"]) == validated_calculations["discount_amount"], "Discount amount is not correct"
            assert float(response_body["data"]["tax_amount"]) == validated_calculations["tax_amount"], "Tax amount is not correct"
            assert float(response_body["data"]["actual_total_commission_amount"]) == validated_calculations["actual_total_commission_amount"], "Commission amount is not correct"

            """
            Update Transaction Request Tip
            """
            tip_amount = 25
            payload = {
                "stripe_intent_id": None,
                "b2binpay_invoice_id": b2binpay_invoice_id,
                "telr_transaction_request_id": None,
                "merchant_transaction_id": merchant_transaction_id,
                "tip_amount":tip_amount
            }
            response = do_update_payment_transaction_request(client, payload)
            j = json.loads(response.data)
            assert j["status"] == 'successful'

            b2binpay_invoice_id = j["data"]["b2binpay_invoice_id"]

            # VALIDATE CALCULATIONS
            expectations = {
                "original_payable_amount": charge_amount - discount_amount + tip_amount,
                "paid_amount": 0,
                "discount_amount": discount_amount,
                "tax_amount": tax_amount,
                "tip_amount": tip_amount,
                "default_tip_amount": calculated_tip_amount if calculated_tip_amount else 0,
            }
            validated_calculations = validate_calculations(merchant_transaction_id, b2binpay_invoice_id, expectations)

            """
            Get Transaction Request Details
            """
            response = do_get_transaction_request(client, transaction_code)
            response_body = json.loads(response.data)
            assert response_body["status"] == 'successful'
            assert "feature_list" in response_body["data"]
            assert "merchant_details" in response_body["data"]
            assert len(response_body["data"]["item_list"]) == len(transaction_payload["item_list"])
            assert len(response_body["data"]["offer_list"]) == len(transaction_payload["offer_list"])
            assert merchant_transaction_id == response_body["data"]["merchant_transaction_id"]

            assert float(response_body["data"]["payable_amount"]) == validated_calculations["new_payable_amount"], "Payable amount is not correct"
            assert float(response_body["data"]["charge_amount"]) == validated_calculations["charge_amount"], "Charge amount is not correct"
            assert float(response_body["data"]["paid_amount"]) == validated_calculations["paid_amount"], "Paid amount is not correct"
            assert float(response_body["data"]["tip_amount"]) == validated_calculations["tip_amount"], "Tip amount is not correct"
            assert float(response_body["data"]["discount_amount"]) == validated_calculations["discount_amount"], "Discount amount is not correct"
            assert float(response_body["data"]["tax_amount"]) == validated_calculations["tax_amount"], "Tax amount is not correct"
            assert float(response_body["data"]["actual_total_commission_amount"]) == validated_calculations["actual_total_commission_amount"], "Commission amount is not correct"
            assert float(response_body["data"]["actual_merchant_share_amount"]) == validated_calculations["actual_merchant_share_amount"], "Merchant share amount is not correct"

            """
            Update Transaction Request Currency
            """
            payload = {
                "b2binpay_invoice_id": b2binpay_invoice_id,
                "b2binpay_currency_id": "1002"
            }
            response = do_update_payment_transaction_request_currency(client, payload)
            j = json.loads(response.data)
            assert j["status"] == 'successful'

            """
            Get Transaction Request Details
            """
            response = do_get_transaction_request(client, transaction_code)
            response_body = json.loads(response.data)
            assert response_body["status"] == 'successful'
            assert "feature_list" in response_body["data"]
            assert "merchant_details" in response_body["data"]
            assert len(response_body["data"]["item_list"]) == len(transaction_payload["item_list"])
            assert len(response_body["data"]["offer_list"]) == len(transaction_payload["offer_list"])
            assert merchant_transaction_id == response_body["data"]["merchant_transaction_id"]

            assert response_body["data"]["b2binpay_payable_wallet_address"], "b2binpay payable wallet address not set"
            assert response_body["data"]["b2binpay_payable_currency_id"], "b2binpay payable wallet currency not set"

            currency_id = response_body['data']['payable_currency_id']

            assert float(response_body["data"]["payable_amount"]) == validated_calculations["new_payable_amount"], "Payable amount is not correct"
            assert float(response_body["data"]["charge_amount"]) == validated_calculations["charge_amount"], "Charge amount is not correct"
            assert float(response_body["data"]["paid_amount"]) == validated_calculations["paid_amount"], "Paid amount is not correct"
            assert float(response_body["data"]["tip_amount"]) == validated_calculations["tip_amount"], "Tip amount is not correct"
            assert float(response_body["data"]["discount_amount"]) == validated_calculations["discount_amount"], "Discount amount is not correct"
            assert float(response_body["data"]["tax_amount"]) == validated_calculations["tax_amount"], "Tax amount is not correct"
            assert float(response_body["data"]["actual_total_commission_amount"]) == validated_calculations["actual_total_commission_amount"], "Commission amount is not correct"
            assert float(response_body["data"]["actual_merchant_share_amount"]) == validated_calculations["actual_merchant_share_amount"], "Merchant share amount is not correct"

            """
            Sending b2binpay invoice "PARTIALLY_PAID" Event To Webhook
            """
            query = text("""
                SELECT bi.b2binpay_invoice_id, bi.external_b2binpay_invoice_id, m.merchant_code
                FROM b2binpay_invoice bi
                JOIN merchant_transaction mt ON mt.merchant_transaction_id = bi.merchant_transaction_id
                JOIN merchant m ON m.merchant_id = mt.merchant_id
                JOIN merchant_transaction_customer mtc ON mtc.merchant_transaction_id = bi.merchant_transaction_id
                WHERE bi.merchant_transaction_id = :merchant_transaction_id
                AND bi.meta_status = :meta_status
            """)
            with db_engine.connect() as conn:
                result = conn.execute(query, merchant_transaction_id=merchant_transaction_id, meta_status="active").fetchone()
                assert result, "b2binpay not found for this transaction"
                b2binpay_invoice_id = result["b2binpay_invoice_id"]
                external_b2binpay_invoice_id = result["external_b2binpay_invoice_id"]

            query = text("""
                SELECT conversion_rate
                FROM conversion_rate
                WHERE from_currency_id = :from_currency_id
                AND to_currency_id = :to_currency_id
                AND meta_status = :meta_status
            """)
            with db_engine.connect() as conn:
                result = conn.execute(query, from_currency_id=currency_id, to_currency_id=equivalent_currency_id, meta_status='active').fetchone()

            conversion_rate = float(result['conversion_rate'])
            partial_payment_1_charge_amount = 10

            # payment request initiated
            with open('tests/testdata/b2binpay/sample_partially_paid_invoice_webhook.json') as f:
                sample_payment_request_webhook_response = json.load(f)
                sample_payment_request_webhook_response["data"]["id"] = external_b2binpay_invoice_id
                sample_payment_request_webhook_response["data"]["attributes"]["target_paid"] = partial_payment_1_charge_amount * conversion_rate
                sample_payment_request_webhook_response["included"][1]["id"] = random.randint(1, 1000000)
                sample_payment_request_webhook_response["included"][1]["attributes"]["amount_target"] = partial_payment_1_charge_amount * conversion_rate
                sample_payment_request_webhook_response["included"][1]["attributes"]["amount"] = (partial_payment_1_charge_amount * conversion_rate) / float(sample_payment_request_webhook_response["included"][1]["attributes"]["rate_target"])

                response = do_handle_invoice_webhook(client, sample_payment_request_webhook_response)
                assert response.status_code == 200, "b2binpay webhook failed"

            # VALIDATE CALCULATIONS
            expectations = {
                "original_payable_amount": charge_amount - discount_amount + tip_amount,
                "paid_amount": partial_payment_1_charge_amount,
                "discount_amount": discount_amount,
                "tip_amount": tip_amount,
                "default_tip_amount": calculated_tip_amount if calculated_tip_amount else 0,
            }
            validated_calculations = validate_calculations(merchant_transaction_id, b2binpay_invoice_id, expectations)

            """
            Get Transaction Request Details
            """
            response = do_get_transaction_request(client, transaction_code)
            response_body = json.loads(response.data)
            assert response_body["status"] == 'successful'
            assert "feature_list" in response_body["data"]
            assert "merchant_details" in response_body["data"]
            assert len(response_body["data"]["item_list"]) == len(transaction_payload["item_list"])
            assert len(response_body["data"]["offer_list"]) == len(transaction_payload["offer_list"])
            assert merchant_transaction_id == response_body["data"]["merchant_transaction_id"]

            b2binpay_invoice_id = response_body["data"]["b2binpay_invoice_id"]

            assert float(response_body["data"]["payable_amount"]) == validated_calculations["new_payable_amount"], "Payable amount is not correct"
            assert float(response_body["data"]["charge_amount"]) == validated_calculations["charge_amount"], "Charge amount is not correct"
            assert float(response_body["data"]["paid_amount"]) == validated_calculations["paid_amount"], "Paid amount is not correct"
            assert float(response_body["data"]["tip_amount"]) == validated_calculations["tip_amount"], "Tip amount is not correct"
            assert float(response_body["data"]["discount_amount"]) == validated_calculations["discount_amount"], "Discount amount is not correct"
            assert float(response_body["data"]["tax_amount"]) == validated_calculations["tax_amount"], "Tax amount is not correct"
            assert float(response_body["data"]["actual_total_commission_amount"]) == validated_calculations["actual_total_commission_amount"], "Commission amount is not correct"
            assert float(response_body["data"]["actual_merchant_share_amount"]) == validated_calculations["actual_merchant_share_amount"], "Merchant share amount is not correct"

            """
            Sending b2binpay invoice "PAID" Event To Webhook
            """
            query = text("""
                SELECT bi.b2binpay_invoice_id, bi.external_b2binpay_invoice_id, m.merchant_code
                FROM b2binpay_invoice bi
                JOIN merchant_transaction mt ON mt.merchant_transaction_id = bi.merchant_transaction_id
                JOIN merchant m ON m.merchant_id = mt.merchant_id
                JOIN merchant_transaction_customer mtc ON mtc.merchant_transaction_id = bi.merchant_transaction_id
                WHERE bi.merchant_transaction_id = :merchant_transaction_id
                AND bi.meta_status = :meta_status
            """)
            with db_engine.connect() as conn:
                result = conn.execute(query, merchant_transaction_id=merchant_transaction_id, meta_status="active").fetchone()
                assert result, "b2binpay not found for this transaction"
                b2binpay_invoice_id = result["b2binpay_invoice_id"]
                external_b2binpay_invoice_id = result["external_b2binpay_invoice_id"]

            query = text("""
                SELECT conversion_rate
                FROM conversion_rate
                WHERE from_currency_id = :from_currency_id
                AND to_currency_id = :to_currency_id
                AND meta_status = :meta_status
            """)
            with db_engine.connect() as conn:
                result = conn.execute(query, from_currency_id=currency_id, to_currency_id=equivalent_currency_id, meta_status='active').fetchone()

            conversion_rate = float(result['conversion_rate'])

            # payment request initiated
            with open('tests/testdata/b2binpay/sample_paid_invoice_webhook.json') as f:
                sample_payment_request_webhook_response = json.load(f)
                sample_payment_request_webhook_response["data"]["id"] = external_b2binpay_invoice_id
                sample_payment_request_webhook_response["data"]["attributes"]["target_paid"] = (validated_calculations["new_payable_amount"] - partial_payment_1_charge_amount) * conversion_rate
                sample_payment_request_webhook_response["included"][1]["id"] = random.randint(1, 1000000)
                sample_payment_request_webhook_response["included"][1]["attributes"]["amount_target"] = (validated_calculations["new_payable_amount"] - partial_payment_1_charge_amount) * conversion_rate
                sample_payment_request_webhook_response["included"][1]["attributes"]["amount"] = ((validated_calculations["new_payable_amount"] - partial_payment_1_charge_amount) * conversion_rate) / float(sample_payment_request_webhook_response["included"][1]["attributes"]["rate_target"])

                response = do_handle_invoice_webhook(client, sample_payment_request_webhook_response)
                assert response.status_code == 200, "b2binpay webhook failed"

            # VALIDATE CALCULATIONS
            expectations = {
                "original_payable_amount": charge_amount - discount_amount + tip_amount,
                "paid_amount": validated_calculations["new_payable_amount"] - partial_payment_1_charge_amount,
                "discount_amount": discount_amount,
                "tip_amount": tip_amount,
                "default_tip_amount": calculated_tip_amount if calculated_tip_amount else 0,
            }
            validated_calculations = validate_calculations(merchant_transaction_id, b2binpay_invoice_id, expectations)

            """
            Get Transaction Request Details
            """
            response = do_get_transaction_request(client, transaction_code)
            response_body = json.loads(response.data)
            assert response_body["status"] == 'successful'
            assert "feature_list" in response_body["data"]
            assert "merchant_details" in response_body["data"]
            assert len(response_body["data"]["item_list"]) == len(transaction_payload["item_list"])
            assert len(response_body["data"]["offer_list"]) == len(transaction_payload["offer_list"])
            assert merchant_transaction_id == response_body["data"]["merchant_transaction_id"]

            b2binpay_invoice_id = response_body["data"]["b2binpay_invoice_id"]

            assert float(response_body["data"]["payable_amount"]) == validated_calculations["new_payable_amount"], "Payable amount is not correct"
            assert float(response_body["data"]["charge_amount"]) == validated_calculations["charge_amount"], "Charge amount is not correct"
            assert float(response_body["data"]["paid_amount"]) == validated_calculations["paid_amount"], "Paid amount is not correct"
            assert float(response_body["data"]["tip_amount"]) == validated_calculations["tip_amount"], "Tip amount is not correct"
            assert float(response_body["data"]["discount_amount"]) == validated_calculations["discount_amount"], "Discount amount is not correct"
            assert float(response_body["data"]["tax_amount"]) == validated_calculations["tax_amount"], "Tax amount is not correct"
            assert float(response_body["data"]["actual_total_commission_amount"]) == validated_calculations["actual_total_commission_amount"], "Commission amount is not correct"
            assert float(response_body["data"]["actual_merchant_share_amount"]) == validated_calculations["actual_merchant_share_amount"], "Merchant share amount is not correct"

            """
            Get Balance For Merchant
            """
            response = do_get_merchant_balance(client, user_headers, merchant_details["merchant_id"], 7)
            response_body = json.loads(response.data)
            assert response_body["status"] == 'successful'
            assert response_body["action"] == 'get_merchant_balance'

            """
            Get Merchant Transaction History
            """
            response = test_merchant_dashboard.do_get_merchant_transaction_history_v2(client, user_headers)
            response_body = json.loads(response.data)
            assert response_body["status"] == 'successful'
            assert response_body["action"] == 'get_merchant_transaction_history_v2'

            
#     # --------- Payment-Link Expired Flow ---------- #

#     """
#     Normal Transaction Request Creation
#     """

#     transaction_payload["settings"].update({
#         "payment_link_expiry_duration" :1,
#         "expiry_duration_measurement_name" :"seconds"
#     })
#     transaction_payload["remote_transaction_id"] = "to-be-expired"

#     response = do_create_payment_transaction_request(client, user_headers, transaction_payload)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
#     assert "payment_url" in j

#     # Extracting transaction code from payment-link
#     splitted_str_list = j["payment_url"].split("/")
#     transaction_code = splitted_str_list[len(splitted_str_list)-1]
#     merchant_transaction_id = j["merchant_transaction_id"]

#     # Fetching merchant_transaction_code from database
#     db_engine = jqutils.get_db_engine()
#     query = text("""
#         SELECT merchant_transaction_code
#         FROM merchant_transaction
#         WHERE merchant_transaction_id = :merchant_transaction_id
#         AND meta_status = :meta_status
#     """)
#     with db_engine.connect() as conn:
#         result = conn.execute(query, merchant_transaction_id=merchant_transaction_id, meta_status="active").fetchone()
#         assert result, "No record found in merchant_transaction table"
#         merchant_transaction_code = result["merchant_transaction_code"]

#     """
#     Trying to access 'expired' link after 1 second
#     """
#     time.sleep(1)
#     response = do_get_transaction_request(client, transaction_code)
#     j = json.loads(response.data)
#     assert j["status"] == 'failed'
#     assert j["error"] == 'Payment link expired.'

#     """
#     Trying to access 'expired' link with correct permissions
#     """
#     response = do_get_transaction_request(client, merchant_transaction_code, user_headers)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
#     assert j["data"]["transaction_status"] == "expired"

# # --------- Payment-Link Cancelled Flow ---------- #

#     """
#     Normal Transaction Request Creation
#     """

#     transaction_payload["settings"].update({
#         "payment_link_expiry_duration": None,
#         "expiry_duration_measurement_name": None
#     })
#     transaction_payload["remote_transaction_id"] = "to-be-cancelled"

#     response = do_create_payment_transaction_request(client, user_headers, transaction_payload)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
#     assert "payment_url" in j

#     # Extracting transaction code from payment-link
#     splitted_str_list = j["payment_url"].split("/")
#     transaction_code = splitted_str_list[len(splitted_str_list)-1]
#     merchant_transaction_id = j["merchant_transaction_id"]

#     # Fetching merchant_transaction_code from database
#     db_engine = jqutils.get_db_engine()
#     query = text("""
#         SELECT merchant_transaction_code
#         FROM merchant_transaction
#         WHERE merchant_transaction_id = :merchant_transaction_id
#         AND meta_status = :meta_status
#     """)
#     with db_engine.connect() as conn:
#         result = conn.execute(query, merchant_transaction_id=merchant_transaction_id, meta_status="active").fetchone()
#         assert result, "No record found in merchant_transaction table"
#         merchant_transaction_code = result["merchant_transaction_code"]

#     """
#     Cancel The Transaction Request
#     """
#     payload = {
#         "cancellation_reason_id": 1,
#         "cancellation_reason_note": "test"
#     }
#     response = do_cancel_transaction_request(client, user_headers, transaction_code, payload)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'

#     """
#     Trying to access 'expired' link after 1 second
#     """
#     time.sleep(1)
#     response = do_get_transaction_request(client, transaction_code)
#     j = json.loads(response.data)
#     assert j["status"] == 'failed'
#     assert j["error"] == 'Payment link cancelled.'

#     """
#     Sending Stripe Payment Intent 'CANCELLED' Event To Webhook
#     """
#     if os.getenv("MOCK_STRIPE") == "1":
#         external_payment_intent_id = jqutils.get_column_by_id(str(stripe_intent_id), "stripe_intent_reference_number", "stripe_intent")

#         with open(f'tests/testdata/stripe/webhook/sample_normal_cancellation_response.json') as f:
#             sample_payment_cancelled_webhook_response = json.load(f)
#             sample_payment_cancelled_webhook_response["data"]["object"]["metadata"]["merchant_code"] = merchant_details["merchant_code"]
#             sample_payment_cancelled_webhook_response["data"]["object"]["id"] = external_payment_intent_id
#             sample_payment_cancelled_webhook_response["data"]["object"]["amount"] = float(transaction_payload["payment_details"]["payable_amount"])
#             sample_payment_cancelled_webhook_response["data"]["object"]["currency"] = one_merchant["default_currency"]["currency_alpha_3"]

#             response = do_handle_payment_intent_webhook(client,sample_payment_cancelled_webhook_response)
#             assert response.status_code == 200
#             response_body = json.loads(response.data.decode("utf-8"))
#             assert response_body["success"] is True, "Stripe Payment Intent Failure webhook failed"

#     """
#     Trying to access 'cancelled' link with correct permissions
#     """
#     response = do_get_transaction_request(client, merchant_transaction_code, user_headers)
#     j = json.loads(response.data)
#     assert j["status"] == 'successful'
#     assert j["data"]["transaction_status"] == "cancelled"

#     """
#     Trying to access 'cancelled' link with incorrect permissions
#     """
#     db_engine = jqutils.get_db_engine()
#     query = text("""
#         SELECT u.user_id, m.merchant_api_key, m.merchant_name
#         FROM user u
#         JOIN user_merchant_map umm ON umm.user_id = u.user_id
#         JOIN merchant m ON m.merchant_id = umm.merchant_id
#         JOIN user_role_map urm ON urm.user_id = u.user_id
#         WHERE u.user_id <> :user_id
#         AND urm.role_id <> 1
#         AND m.merchant_name <> :merchant_name
#         AND u.meta_status = :meta_status
#     """)
#     with db_engine.connect() as conn:
#         result = conn.execute(query, user_id=user_headers["X-User-Id"], merchant_name=merchant_details["merchant_name"], meta_status="active").fetchone()
#         assert result, "No user found with merchant permissions"

#     merchant_api_key = jqaccess_control_engine.decrypt_password(result['merchant_api_key']).decode()

#     other_user_headers = {
#         "X-User-Id": result["user_id"],
#         "X-Api-Key": merchant_api_key,
#         "X-Merchant-Name": result["merchant_name"]
#     }

#     response = do_get_transaction_request(client, merchant_transaction_code, other_user_headers)
#     j = json.loads(response.data)
#     assert j["status"] == 'failed'
#     assert j["error"] == "Access Denied"

#     """
#     In-Correct 'item_list' so sum of all prices doesnot match 'payable_amount'
#     """
#     file_name = "tests/testdata/payment_link_generation_payload/telr/incorrect_menu_items_only.json"
#     with open(file_name) as f:
#         transaction_payload = json.load(f)

#     # Transaction Request Creation Failed
#     response = do_create_payment_transaction_request(client, user_headers, transaction_payload)
#     j = json.loads(response.data)
#     assert j["status"] == 'failed'
#     assert "error_list" in j
#     assert len(j["error_list"]) > 0
