import os
from logging import debug
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
        
        self.log("\nCompleted!", False)
        
        self.log("\n")
        self.log("-^-" * 50)
        self.log("\n")

    def upload_base_data(self):
        self.log("\nUploading base data:")
        
        self.log("> Uploading module.. ", False)
        jqutils.upload_csv("module", self.top_path + "module.csv")
        self.log("Done\n> Uploading module_access.. ", False)
        jqutils.upload_csv("module_access", self.top_path + "module_access.csv")
        self.log("Done\n> Uploading role.. ", False)
        jqutils.upload_csv("role", self.top_path + "role.csv")
        
        # Upload security keys needed for encryption
        # self.log("Done\n> Uploading security keys.. ", False)
        # self.upload_security_keys()
        self.log("Done\n")
   
    def encrypt_password(self, password):
        db_engine = jqutils.get_db_engine(self.schema_name)
        password_bytes = password.encode()

        with db_engine.connect() as conn:
            query = text("""
                    select symmetric_key 
                    from portal_profile_service_secret
                    where key_name = 'password-protector-key' and meta_status = 'active'
                """)
            result = conn.execute(query).fetchone()
            assert result, "Failed to get password protector key"
            
            key_string_db = result['symmetric_key']
            key_string_db_bytes = key_string_db.encode()

        cipher_text_bytes = jqsecurity.encrypt_bytes_symmetric_to_bytes(password_bytes, key_string_db_bytes)
        return cipher_text_bytes
    
    def log(self, message, new_line=True):
        if debug:
            if new_line:
                print(message)
            else:
                print(message, end='')