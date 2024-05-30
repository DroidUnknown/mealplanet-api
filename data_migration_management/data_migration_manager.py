import csv
import os
from logging import debug
from os import path
from sqlalchemy.sql import text
from utils import jqutils, jqsecurity

class DataMigrationManager:

    top_path = './data_migration_management/data/'
    
    def __init__(self, schema_name=None, debug = False):
        self.debug = debug
        if schema_name:
            self.schema_name = schema_name
        else:
            self.schema_name = os.getenv("MYSQL_SCHEMA_NAME")
    
    def run(self):
        self.log("\n")
        self.log("-^-" * 50)
        
        self.upload_base_data()
        self.upload_merchant_data()
        self.upload_merchant_campaign_data()
        self.upload_payment_point_data()
        self.upload_credentials()
        # self.upload_aws_resources()
        
        self.log("\nCompleted!", False)
        
        self.log("\n")
        self.log("-^-" * 50)
        self.log("\n")

    def upload_base_data(self):
        self.log("\nUploading base data:")
        
        self.log("> Uploading city.. ", False)
        jqutils.upload_csv("city", self.top_path + "city.csv")
        self.log("Done\n> Uploading emirate.. ", False)
        jqutils.upload_csv("emirate", self.top_path + "emirate.csv")
        self.log("Done\n> Uploading country.. ", False)
        jqutils.upload_csv("country", self.top_path + "country.csv")
        self.log("Done\n> Uploading branch.. ", False)
        jqutils.upload_csv("branch", self.top_path + "branch.csv")
        self.log("Done\n> Uploading address_type.. ", False)
        jqutils.upload_csv("address_type", self.top_path + "address_type.csv")
        self.log("Done\n> Uploading finance_account_type.. ", False)
        jqutils.upload_csv("finance_account_type", self.top_path + "finance_account_type.csv")
        self.log("Done\n> Uploading finance_account.. ", False)
        jqutils.upload_csv("finance_account", self.top_path + "finance_account.csv")
        self.log("Done\n> Uploading unit_conversion.. ", False)
        jqutils.upload_csv("unit_conversion", self.top_path + "unit_conversion.csv")
        self.log("Done\n> Uploading stock_item_facility_balance.. ", False)
        jqutils.upload_csv("stock_item_facility_balance", self.top_path + "stock_item_facility_balance.csv")
        self.log("Done\n> Uploading stock_item_facility_ledger.. ", False)
        jqutils.upload_csv("stock_item_facility_ledger", self.top_path + "stock_item_facility_ledger.csv")
        self.log("Done\n> Uploading stock_item_department_balance.. ", False)
        jqutils.upload_csv("stock_item_department_balance", self.top_path + "stock_item_department_balance.csv")
        self.log("Done\n> Uploading stock_item_department_ledger.. ", False)
        jqutils.upload_csv("stock_item_department_ledger", self.top_path + "stock_item_department_ledger.csv")
        self.log("Done\n> Uploading supplier.. ", False)
        jqutils.upload_csv("supplier", self.top_path + "supplier.csv")
        self.log("Done\n> Uploading stock_category.. ", False)
        jqutils.upload_csv("stock_category", self.top_path + "stock_category.csv")
        self.log("Done\n> Uploading stock_item_category_map.. ", False)
        jqutils.upload_csv("stock_item_category_map", self.top_path + "stock_item_category_map.csv")
        self.log("Done\n> Uploading stock_item.. ", False)
        jqutils.upload_csv("stock_item", self.top_path + "stock_item.csv")
        self.log("Done\n> Uploading packaging.. ", False)
        jqutils.upload_csv("packaging", self.top_path + "packaging.csv")
        self.log("Done\n> Uploading stock_item_packaging_map.. ", False)
        jqutils.upload_csv("stock_item_packaging_map", self.top_path + "stock_item_packaging_map.csv")
        self.log("Done\n> Uploading return_reason.. ", False)
        jqutils.upload_csv("return_reason", self.top_path + "return_reason.csv")
        self.log("Done\n> Uploading cuisine.. ", False)
        jqutils.upload_csv("cuisine", self.top_path + "cuisine.csv")
        
        self.log("Done\n> Uploading merchant_role.. ", False)
        jqutils.upload_csv("merchant_role", self.top_path + "merchant_role.csv")
        self.log("Done\n> Uploading process.. ", False)
        jqutils.upload_csv("process", self.top_path + "process.csv")
        self.log("Done\n> Uploading process_approval_config_user_role_map.. ", False)
        jqutils.upload_csv("process_approval_config_user_role_map", self.top_path + "process_approval_config_user_role_map.csv")
        self.log("Done\n> Uploading process_approval_config.. ", False)
        jqutils.upload_csv("process_approval_config", self.top_path + "process_approval_config.csv")
        self.log("Done\n> Uploading process_approval_config_facility_map.. ", False)
        jqutils.upload_csv("process_approval_config_facility_map", self.top_path + "process_approval_config_facility_map.csv")
        self.log("Done\n> Uploading tax.. ", False)
        jqutils.upload_csv("tax", self.top_path + "tax.csv")
        self.log("Done\n> Uploading ai_model.. ", False)
        jqutils.upload_csv("ai_model", self.top_path + "ai_model.csv")
        self.log("Done\n> Uploading ai_quota_config.. ", False)
        jqutils.upload_csv("ai_quota_config", self.top_path + "ai_quota_config.csv")
        self.log("Done\n> Uploading wastage_reason.. ", False)
        jqutils.upload_csv("wastage_reason", self.top_path + "wastage_reason.csv")
        self.log("Done\n> Uploading policy.. ", False)
        jqutils.upload_csv("policy", self.top_path + "policy.csv")


        self.log("Done\n> Uploading discount.. ", False)
        jqutils.upload_csv("discount", self.top_path + "discount.csv")
        self.log("Done\n> Uploading discount_item_map.. ", False)
        jqutils.upload_csv("discount_item_map", self.top_path + "discount_item_map.csv")
        self.log("Done\n> Uploading discount_item_category_map.. ", False)
        jqutils.upload_csv("discount_item_category_map", self.top_path + "discount_item_category_map.csv")
        self.log("Done\n> Uploading schedule.. ", False)
        jqutils.upload_csv("schedule", self.top_path + "schedule.csv")
        self.log("Done\n> Uploading facility_fulfillment_type_map.. ", False)
        jqutils.upload_csv("facility_fulfillment_type_map", self.top_path + "facility_fulfillment_type_map.csv")
        self.log("Done\n> Uploading facility_fulfillment_type_discount_map.. ", False)
        jqutils.upload_csv("facility_fulfillment_type_discount_map", self.top_path + "facility_fulfillment_type_discount_map.csv")
        
        self.log("Done\n> Uploading brand.. ", False)
        jqutils.upload_csv("brand", self.top_path + "brand.csv")
        self.log("Done\n> Uploading brand_cuisine_map.. ", False)
        jqutils.upload_csv("brand_cuisine_map", self.top_path + "brand_cuisine_map.csv")
        self.log("Done\n> Uploading modifier_choice_branch_map.. ", False)
        jqutils.upload_csv("modifier_choice_branch_map", self.top_path + "modifier_choice_branch_map.csv")
        self.log("Done\n> Uploading modifier_choice.. ", False)
        jqutils.upload_csv("modifier_choice", self.top_path + "modifier_choice.csv")
        self.log("Done\n> Uploading modifier_section_branch_map.. ", False)
        jqutils.upload_csv("modifier_section_branch_map", self.top_path + "modifier_section_branch_map.csv")
        self.log("Done\n> Uploading modifier_section.. ", False)
        jqutils.upload_csv("modifier_section", self.top_path + "modifier_section.csv")
        self.log("Done\n> Uploading item_category_branch_map.. ", False)
        jqutils.upload_csv("item_category_branch_map", self.top_path + "item_category_branch_map.csv")
        self.log("Done\n> Uploading item_category.. ", False)
        jqutils.upload_csv("item_category", self.top_path + "item_category.csv")
        self.log("Done\n> Uploading item_display_group.. ", False)
        jqutils.upload_csv("item_display_group", self.top_path + "item_display_group.csv")
        self.log("Done\n> Uploading item_branch_map.. ", False)
        jqutils.upload_csv("item_branch_map", self.top_path + "item_branch_map.csv")
        self.log("Done\n> Uploading item.. ", False)
        jqutils.upload_csv("item", self.top_path + "item.csv")
        self.log("Done\n> Uploading unavailability_reason.. ", False)
        jqutils.upload_csv("unavailability_reason", self.top_path + "unavailability_reason.csv")
        self.log("Done\n> Uploading item_branch_price_map.. ", False)
        jqutils.upload_csv("item_branch_price_map", self.top_path + "item_branch_price_map.csv")

        self.log("Done\n> Uploading facility.. ", False)
        jqutils.upload_csv("facility", self.top_path + "facility.csv")
        self.log("Done\n> Uploading department.. ", False)
        jqutils.upload_csv("department", self.top_path + "department.csv")
        self.log("Done\n> Uploading marketplace.. ", False)
        jqutils.upload_csv("marketplace", self.top_path + "marketplace.csv")
        self.log("Done\n> Uploading currency.. ", False)
        jqutils.upload_csv("currency", self.top_path + "currency.csv")
        self.log("Done\n> Uploading conversion_rate.. ", False)
        jqutils.upload_csv("conversion_rate", self.top_path + "conversion_rate.csv")
        self.log("Done\n> Uploading service_provider.. ", False)
        jqutils.upload_csv("service_provider", self.top_path + "service_provider.csv")
        self.log("Done\n> Uploading fulfillment_type.. ", False)
        jqutils.upload_csv("fulfillment_type", self.top_path + "fulfillment_type.csv")
        self.log("Done\n> Uploading payment_method.. ", False)
        jqutils.upload_csv("payment_method", self.top_path + "payment_method.csv")
        self.log("Done\n> Uploading merchant_payment_method_config.. ", False)
        jqutils.upload_csv("merchant_payment_method_config", self.top_path + "merchant_payment_method_config.csv")
        self.log("Done\n> Uploading merchant_service_map.. ", False)
        jqutils.upload_csv("merchant_service_map", self.top_path + "merchant_service_map.csv")
        self.log("Done\n> Uploading merchant_service_facility_map.. ", False)
        jqutils.upload_csv("merchant_service_facility_map", self.top_path + "merchant_service_facility_map.csv")
        self.log("Done\n> Uploading service_provider_payment_method_currency_map.. ", False)
        jqutils.upload_csv("service_provider_payment_method_currency_map", self.top_path + "service_provider_payment_method_currency_map.csv")
        self.log("Done\n> Uploading default_merchant_commission.. ", False)
        jqutils.upload_csv("default_merchant_commission", self.top_path + "default_merchant_commission.csv")
        self.log("Done\n> Uploading merchant_commission.. ", False)
        jqutils.upload_csv("merchant_commission", self.top_path + "merchant_commission.csv")
        self.log("Done\n> Uploading service_provider_commission.. ", False)
        jqutils.upload_csv("service_provider_commission", self.top_path + "service_provider_commission.csv")
        self.log("Done\n> Uploading payment_failure_reason.. ", False)
        jqutils.upload_csv("payment_failure_reason", self.top_path + "payment_failure_reason.csv")
        self.log("Done\n> Uploading transaction_type.. ", False)
        jqutils.upload_csv("transaction_type", self.top_path + "transaction_type.csv")
        self.log("Done\n> Uploading merchant_transaction_balance.. ", False)
        jqutils.upload_csv("merchant_transaction_balance", self.top_path + "merchant_transaction_balance.csv")
        self.log("Done\n> Uploading webhook.. ", False)
        jqutils.upload_csv("webhook", self.top_path + "webhook.csv")
        self.log("Done\n> Uploading webhook_type.. ", False)
        jqutils.upload_csv("webhook_type", self.top_path + "webhook_type.csv")
        self.log("Done\n> Uploading merchant_webhook_map.. ", False)
        jqutils.upload_csv("merchant_webhook_map", self.top_path + "merchant_webhook_map.csv")
        self.log("Done\n> Uploading feature.. ", False)
        jqutils.upload_csv("feature", self.top_path + "feature.csv")
        self.log("Done\n> Uploading service.. ", False)
        jqutils.upload_csv("service", self.top_path + "service.csv")
        self.log("Done\n> Uploading notification_type.. ", False)
        jqutils.upload_csv("notification_type", self.top_path + "notification_type.csv")
        self.log("Done\n> Uploading cancellation_reason.. ", False)
        jqutils.upload_csv("cancellation_reason", self.top_path + "cancellation_reason.csv")
        self.log("Done\n> Uploading measurement.. ", False)
        jqutils.upload_csv("measurement", self.top_path + "measurement.csv")
        self.log("Done\n> Uploading business_type.. ", False)
        jqutils.upload_csv("business_type", self.top_path + "business_type.csv")
        self.log("Done\n> Uploading business_category.. ", False)
        jqutils.upload_csv("business_category", self.top_path + "business_category.csv")
        self.log("Done\n> Uploading email_template.. ", False)
        jqutils.upload_csv("email_template", self.top_path + "email_template.csv")
        self.log("Done\n> Uploading digital_wallet.. ", False)
        jqutils.upload_csv("digital_wallet", self.top_path + "digital_wallet.csv")
        self.log("Done\n> Uploading digital_wallet_service_provider_payment_method_currency_map.. ", False)
        jqutils.upload_csv("digital_wallet_service_provider_payment_method_currency_map", self.top_path + "digital_wallet_service_provider_payment_method_currency_map.csv")
        self.log("Done\n> Uploading telr_transaction_status_code.. ", False)
        jqutils.upload_csv("telr_transaction_status_code", self.top_path + "telr_transaction_status_code.csv")
        self.log("Done\n> Uploading social_media.. ", False)
        jqutils.upload_csv("social_media", self.top_path + "social_media.csv")
        self.log("Done\n> Uploading printer_model.. ", False)
        jqutils.upload_csv("printer_model", self.top_path + "printer_model.csv")
        self.log("Done\n> Uploading printer.. ", False)
        jqutils.upload_csv("printer", self.top_path + "printer.csv")
        self.log("Done\n> Uploading printer_facility_config.. ", False)
        jqutils.upload_csv("printer_facility_config", self.top_path + "printer_facility_config.csv")
        self.log("Done\n> Uploading printer_template.. ", False)
        jqutils.upload_csv("printer_template", self.top_path + "printer_template.csv")
        self.log("Done\n> Uploading printer_rule.. ", False)
        jqutils.upload_csv("printer_rule", self.top_path + "printer_rule.csv")
        self.log("Done\n> Uploading printer_template_rule.. ", False)
        jqutils.upload_csv("printer_template_rule", self.top_path + "printer_template_rule.csv")
        self.log("Done\n> Uploading customer_review.. ", False)
        jqutils.upload_csv("customer_review", self.top_path + "customer_review.csv")
        self.log("Done\n> Uploading customer_loyalty_reward.. ", False)
        jqutils.upload_csv("customer_loyalty_reward", self.top_path + "customer_loyalty_reward.csv")
        self.log("Done\n> Uploading loyalty_reward_type.. ", False)
        jqutils.upload_csv("loyalty_reward_type", self.top_path + "loyalty_reward_type.csv")
        
        # Upload security keys needed for encryption
        self.log("Done\n> Uploading security keys.. ", False)
        self.upload_security_keys()
        self.log("Done\n")

    # Note: must be uploaded after merchant and marketplace data
    def upload_credentials(self):
        self.log("Uploading credentials:")
        
        with open(self.top_path + "credentials.csv", "r") as csv_file:
            csv_reader = csv.DictReader(csv_file, delimiter='|')
            for row in csv_reader:
                credential_type = row['credential_type']
                username = row['username']
                password = row['password']
                # access_token = row['access_token'] if len(row['access_token']) > 0 else None
                # token_expiry_timestamp = row['token_expiry_timestamp'] if len(row['token_expiry_timestamp']) > 0 else None
                password_bytes = self.encrypt_password(password)
                
                self.log(f"> Credentials for {credential_type} with username: {username}.. ", False)
                
                # Get DB engine
                db_engine = jqutils.get_db_engine(self.schema_name)
                
                if credential_type == 'merchant':
                    query = text("""
                                UPDATE
                                    merchant
                                SET
                                    merchant_api_key = :password
                                WHERE
                                    merchant_name = :username
                            """)
                    with db_engine.connect() as conn:
                        result = conn.execute(query, username=username, password=password_bytes).rowcount
                        assert result, f"Failed to update credentials for merchant: {username}"
                elif credential_type == 'merchant_third_party_credential':
                    merchant_id = row['merchant_id']
                    third_party_credential_type = row['third_party_credential_type']
                    query = text("""
                                UPDATE
                                    merchant_third_party_credential
                                SET
                                    password = :password
                                WHERE
                                    merchant_id = :merchant_id
                                AND
                                    third_party_credential_type = :third_party_credential_type
                            """)
                    with db_engine.connect() as conn:
                        result = conn.execute(query, merchant_id=merchant_id, third_party_credential_type=third_party_credential_type, password=password_bytes).rowcount
                        assert result, f"Failed to update credentials for merchant: {username}"
                elif credential_type == 'branch':
                    merchant_id = row['merchant_id']
                    query = text("""
                                UPDATE
                                    branch
                                SET
                                    password = :password
                                WHERE
                                    username = :username
                                AND
                                    merchant_id = :merchant_id
                            """)
                    with db_engine.connect() as conn:
                        result = conn.execute(query, merchant_id=merchant_id, username=username, password=password_bytes).rowcount
                        assert result, f"Failed to update credentials for merchant: {username}"

                elif credential_type == 'service_provider':
                    query = text("""
                                UPDATE
                                    service_provider
                                SET
                                    service_provider_password = :password
                                WHERE
                                    service_provider_name = :service_provider_name
                    """)
                    with db_engine.connect() as conn:
                        result = conn.execute(query, service_provider_name=username, password=password_bytes).rowcount
                        assert result, f"Failed to update credentials for service_provider: {username}"

                self.log("Done")

    def upload_aws_resources(self):
        if path.exists(self.top_path + "sns_topic.csv") and path.isfile(self.top_path + "sns_topic_subscriber.csv"):
            self.log("Uploading AWS Resource definitions:")
            
            self.log("> Uploading sns_topic.. ", False)
            jqutils.upload_csv("sns_topic", self.top_path + "sns_topic.csv")
            self.log("Done\n> Uploading sns_topic_subscriber.. ", False)
            jqutils.upload_csv("sns_topic_subscriber", self.top_path + "sns_topic_subscriber.csv")
            self.log("Done\n")

    def upload_security_keys(self):
        db_engine = jqutils.get_db_engine(self.schema_name)
        
        # load server keys
        password_protector_key = jqsecurity.read_symmetric_key_from_file('tests/testdata/test-password-protector.key')
        server_token_private_key = jqsecurity.read_key_bytes_from_file('tests/testdata/server-key.private')
        server_token_public_key = jqsecurity.read_key_bytes_from_file('tests/testdata/server-key.public')

        with db_engine.connect() as conn:
            query = text(""" 
                        insert into payment_api_secret(key_algorithm, version, key_name, description, symmetric_key, meta_status) 
                        values (:key_algorithm, :version, :key_name, :description, :symmetric_key, :meta_status)
                    """)
            result = conn.execute(query, key_algorithm='aes', version=1, key_name='password-protector-key',
                                description='password-protector-key', symmetric_key=password_protector_key, meta_status='active').lastrowid
            assert result, "Failed to insert password protector key"

        with db_engine.connect() as conn:
            query = text("""
                        insert into payment_api_secret(key_algorithm, version, key_name, description, private_key, public_key, meta_status) 
                        values (:key_algorithm, :version, :key_name, :description, :private_key, :public_key, :meta_status)
                    """)
            result = conn.execute(query, key_algorithm='rsa', version=1, key_name='token-protector-key', description='token-protector-key',
                                private_key=server_token_private_key, public_key=server_token_public_key, meta_status='active').lastrowid
            assert result, "Failed to insert server keys"

    def encrypt_password(self, password):
        db_engine = jqutils.get_db_engine(self.schema_name)
        password_bytes = password.encode()

        with db_engine.connect() as conn:
            query = text("""
                    select symmetric_key 
                    from payment_api_secret
                    where description = 'password-protector-key' and meta_status = 'active'
                """)
            result = conn.execute(query).fetchone()
            assert result, "Failed to get password protector key"
            
            key_string_db = result['symmetric_key']
            key_string_db_bytes = key_string_db.encode()

        cipher_text_bytes = jqsecurity.encrypt_bytes_symmetric_to_bytes(password_bytes, key_string_db_bytes)
        return cipher_text_bytes

    def decrypt_password(self, password):
        db_engine = jqutils.get_db_engine(self.schema_name)

        with db_engine.connect() as conn:
            query = text("""
                    select symmetric_key 
                    from payment_api_secret
                    where description = 'password-protector-key' and meta_status = 'active'
                """)
            result = conn.execute(query).fetchone()
            assert result, "Failed to get password protector key"
            
            key_string_db = result['symmetric_key']
            key_string_db_bytes = key_string_db.encode()
        
        password = jqsecurity.decrypt_bytes_symmetric_to_bytes(password, key_string_db_bytes)
        return password
    
    def log(self, message, new_line=True):
        if debug:
            if new_line:
                print(message)
            else:
                print(message, end='')