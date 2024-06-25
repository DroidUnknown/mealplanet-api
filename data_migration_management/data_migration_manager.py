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
        
        self.log("> Uploading brand_profile.. ", False)
        jqutils.upload_csv("brand_profile", self.top_path + "brand_profile.csv")
        self.log("Done\n> Uploading plan.. ", False)
        jqutils.upload_csv("plan", self.top_path + "plan.csv")
        self.log("Done\n> Uploading menu_group.. ", False)
        jqutils.upload_csv("menu_group", self.top_path + "menu_group.csv")
        self.log("Done\n> Uploading plan_menu_group_map.. ", False)
        jqutils.upload_csv("plan_menu_group_map", self.top_path + "plan_menu_group_map.csv")
        self.log("Done\n")

    def log(self, message, new_line=True):
        if debug:
            if new_line:
                print(message)
            else:
                print(message, end='')