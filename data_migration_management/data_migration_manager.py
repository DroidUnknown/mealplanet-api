import os
from logging import debug
from utils import jqutils

class DataMigrationManager:

    top_path = './data_migration_management/data/'
    
    def __init__(self, schema_name=None, debug=False):
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
        
        # self.log("> Uploading module.. ", False)
        # jqutils.upload_csv("module", self.top_path + "module.csv")
        self.log("> Uploading module_access.. ", False)
        jqutils.upload_csv("module_access", self.top_path + "module_access.csv")
        self.log("Done\n> Uploading role.. ", False)
        jqutils.upload_csv("role", self.top_path + "role.csv")
        self.log("Done\n> Uploading plan.. ", False)
        jqutils.upload_csv("plan", self.top_path + "plan.csv")
        self.log("Done\n> Uploading menu_group.. ", False)
        jqutils.upload_csv("menu_group", self.top_path + "menu_group.csv")
        self.log("Done\n")

    def log(self, message, new_line=True):
        if debug:
            if new_line:
                print(message)
            else:
                print(message, end='')