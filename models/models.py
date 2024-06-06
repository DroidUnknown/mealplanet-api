import json

from email.policy import default
from enum import unique
from sqlalchemy import Column, DateTime, Integer, JSON, Numeric, SmallInteger, String, Boolean, Date, Time
from sqlalchemy.schema import FetchedValue, UniqueConstraint, ForeignKeyConstraint, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy import text
from utils import jqutils

# ----------------------------------------------------------------------------------------------------------------------

def create_all(schema_name=None):
    db_engine = jqutils.get_db_engine(schema_name)
    Base.metadata.create_all(db_engine)
    print("db created people, Alhamdulillaah")

Base = declarative_base()
column_order_value = 10000

class MetaDataColumn(Column):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        global column_order_value
        column_order_value = column_order_value + 1
        self._creation_order = column_order_value

class Model(Base):
    __abstract__ = True
    __bind_key__ = 'payment_api'

    meta_status = MetaDataColumn(String(16), default=text("active"))  # active, inactive, deleted
    tags = MetaDataColumn(JSON)
    tenant_id = MetaDataColumn(Integer, server_default=text("1"))
    system_user_p = MetaDataColumn(Boolean)

    # either a user id or a system ID
    creation_user_id = MetaDataColumn(Integer)
    modification_user_id = MetaDataColumn(Integer)  # either a user id or a system ID
    deletion_user_id = MetaDataColumn(Integer)  # either a user id or a system ID
    insertion_timestamp = MetaDataColumn(DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)"))
    modification_timestamp = MetaDataColumn(DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"))
    deletion_timestamp = MetaDataColumn(DATETIME(fsp=6))

# ----------------------------------------------------------------------------------------------------------------------

class Scope(Model):
    __tablename__ = 'scope'
    scope_id = Column(Integer, primary_key=True)
    scope_name = Column(String(128)) # brand-profile:basiligo
    brand_profile_id = Column(Integer)
    keycloak_scope_id = Column(String(128))

class Resource(Model):
    __tablename__ = 'resource'
    resource_id = Column(Integer, primary_key=True)
    resource_name = Column(String(128)) # menu-management
    display_name_en = Column(String(128))
    resource_type = Column(String(32)) # module
    uri = Column(String(128))
    scope_id = Column(Integer)
    keycloak_resource_id = Column(String(128))

class Policy(Model):
    __tablename__ = 'policy'
    
    policy_id = Column(Integer, primary_key=True)
    policy_name = Column(String(128)) # admin
    keycloak_policy_id = Column(String(128))

class PolicyRoleAccessMap(Model):
    __tablename__ = 'policy_role_access_map'
    
    policy_role_access_map_id = Column(Integer, primary_key=True)
    policy_id = Column(Integer) # admin
    role_id = Column(Integer) # admin
    access_p = Column(Boolean) # 1: positive, 0: negative

class Permission(Model):
    __tablename__ = 'permission'
    
    permission_id = Column(Integer, primary_key=True)
    permission_name = Column(String(128)) # basiligo:1:menu-management:admin
    permission_type = Column(String(32)) # resource-based, scope-based
    decision_strategy = Column(String(32)) # affirmative, unanimous, consensus
    keycloak_permission_id = Column(String(128))

class PermissionPolicyMap(Model):
    __tablename__ = 'permission_policy_map'
    
    permission_policy_map_id = Column(Integer, primary_key=True)
    permission_id = Column(Integer) # basiligo:1:menu-management:admin
    policy_id = Column(Integer) # admin

class PermissionResourceMap(Model):
    __tablename__ = 'permission_resource_map'
    
    permission_resource_map_id = Column(Integer, primary_key=True)
    permission_id = Column(Integer) # all:*:menu-management:admin
    resource_id = Column(Integer) # menu-management

class PermissionScopeMap(Model):
    __tablename__ = 'permission_scope_map'
    
    permission_scope_map_id = Column(Integer, primary_key=True)
    permission_id = Column(Integer) # basiligo:1:menu-management:admin
    scope_id = Column(Integer) # brand-profile:basiligo

# ----------------------------------------------------------------------------------------------------------------------

class Role(Model):
    __tablename__ = 'role'

    role_id = Column(Integer, primary_key=True)
    role_name = Column(String(64), nullable=False)  # admin, content, member
    
    keycloak_role_id = Column(String(128))

class User(Model):
    __tablename__ = 'user'

    user_id = Column(Integer, primary_key=True)
    
    keycloak_user_id = Column(String(128))

    first_names_en = Column(String(128))
    last_name_en = Column(String(128))
    first_names_ar = Column(String(128))
    last_name_ar = Column(String(128))

    phone_nr = Column(String(32), unique=True)
    email = Column(String(128))

class UserImageMap(Model):
    __tablename__ = 'user_image_map'
    
    user_image_map_id = Column(Integer, primary_key=True)
    
    user_id = Column(Integer)
    image_type = Column(String(32)) #profile
    image_bucket_name = Column(String(128))
    image_object_key = Column(String(128))

class UserRoleMap(Model):
    __tablename__ = 'user_role_map'
    user_role_map_id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    role_id = Column(Integer)

class UserBrandProfileMap(Model):
    __tablename__ = 'user_brand_profile_map'
    user_brand_profile_map_id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    brand_profile_id = Column(Integer)

# ----------------------------------------------------------------------------------------------------------------------

class BrandProfile(Model):
    __tablename__ = 'brand_profile'

    brand_profile_id = Column(Integer, primary_key=True)
    brand_name = Column(String(128))
    external_brand_profile_id = Column(String(128))

class BrandProfileImageMap(Model):
    __tablename__ = 'brand_profile_image_map'

    brand_profile_image_map_id = Column(Integer, primary_key=True)
    brand_profile_id = Column(Integer)

    image_type = Column(String(32)) #logo
    image_bucket_name = Column(String(128))
    image_object_key = Column(String(128))

class Plan(Model):
    __tablename__ = 'plan'

    plan_id = Column(Integer, primary_key=True)
    external_plan_id = Column(String(128))
    brand_profile_id = Column(Integer)
    plan_name = Column(String(128))

class MenuGroup(Model):
    __tablename__ = 'menu_group'

    menu_group_id = Column(Integer, primary_key=True)
    menu_group_name = Column(String(128))

class PlanMenuGroupMap(Model):
    __tablename__ = 'plan_menu_group_map'

    plan_menu_group_map_id = Column(Integer, primary_key=True)
    plan_id = Column(Integer)
    menu_group_id = Column(Integer)

# ----------------------------------------------------------------------------------------------------------------------