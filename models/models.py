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
    
    keycloak_scope_id = Column(String(256))
    scope_name = Column(String(128)) # brand-profile:all, brand-profile:basiligo
    brand_profile_id = Column(Integer)

class Resource(Model):
    __tablename__ = 'resource'
    resource_id = Column(Integer, primary_key=True)
    
    keycloak_resource_id = Column(String(256))
    resource_name = Column(String(128)) # all:*:menu-management:admin, basiligo:1:menu-management:admin
    display_name_en = Column(String(128))
    resource_type = Column(String(32)) # role
    module_id = Column(Integer)
    uri = Column(String(128))

class ResourceScopeMap(Model):
    __tablename__ = 'resource_scope_map'
    
    resource_scope_map_id = Column(Integer, primary_key=True)
    
    resource_id = Column(Integer)
    scope_id = Column(Integer) # brand-profile:all, brand-profile:basiligo

class Policy(Model):
    __tablename__ = 'policy'
    
    policy_id = Column(Integer, primary_key=True)
    keycloak_policy_id = Column(String(256))
    
    policy_name = Column(String(128)) # all:*:menu-management:admin
    policy_type = Column(String(32)) # role, user, client, group, time, resource etc.
    logic = Column(String(32)) # POSITIVE, NEGATIVE
    decision_strategy = Column(String(32)) # AFFIRMATIVE, UNANIMOUS, CONSENSUS
    policy_config = Column(JSON)

class PolicyUserMap(Model):
    __tablename__ = 'policy_user_map'
    
    policy_user_map_id = Column(Integer, primary_key=True)
    
    policy_id = Column(Integer) # all:*:menu-management:admin
    user_id = Column(Integer) # cody

class PolicyResourceMap(Model):
    __tablename__ = 'policy_resource_map'
    
    policy_resource_map_id = Column(Integer, primary_key=True)
    policy_id = Column(Integer) # all:*:menu-management:admin
    resource_id = Column(Integer) # all:*:menu-management:admin

class PolicyApplyPolicyMap(Model):
    __tablename__ = 'policy_apply_policy_map'
    
    policy_apply_policy_map = Column(Integer, primary_key=True)
    policy_id = Column(Integer) # all:*:menu-management:admin
    apply_policy_map_id = Column(Integer) # cody

# ----------------------------------------------------------------------------------------------------------------------

class Role(Model):
    __tablename__ = 'role'

    role_id = Column(Integer, primary_key=True)
    role_name = Column(String(64), nullable=False)  # mp-team, brand-owner, kitchen-partner, delivery-partner

class User(Model):
    __tablename__ = 'user'

    user_id = Column(Integer, primary_key=True)
    keycloak_user_id = Column(String(256))

    username = Column(String(128))
    first_names_en = Column(String(128))
    last_name_en = Column(String(128))
    first_names_ar = Column(String(128))
    last_name_ar = Column(String(128))
    
    password = Column(String(128))
    phone_nr = Column(String(32))
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

class UserBrandProfileModuleAccess(Model):
    __tablename__ = 'user_brand_profile_module_access'
    
    user_brand_profile_module_access_id = Column(Integer, primary_key=True)
    
    user_id = Column(Integer)
    brand_profile_id = Column(Integer)
    module_access_id = Column(Integer)

class OneTimePassword(Model):
    __tablename__ = 'one_time_password'

    one_time_password_id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    
    intent = Column(String(32))  # user_signup, user_forgot_password
    contact_method = Column(String(32))  # email, sms

    otp = Column(String(128))
    otp_request_count = Column(Integer)
    
    otp_requested_timestamp = Column(DATETIME(fsp=6))
    otp_expiry_timestamp = Column(DATETIME(fsp=6))
    otp_verified_timestamp = Column(DATETIME(fsp=6))

    otp_status = Column(String(32))  # pending, sent, verified, expired

class Module(Model):
    __tablename__ = 'module'
    
    module_id = Column(Integer, primary_key=True)
    module_name = Column(String(128)) # menu-management, kitchen-provider, delivery-provider
    module_description = Column(String(128))

class ModuleAccess(Model):
    __tablename__ = 'module_access'
    
    module_access_id = Column(Integer, primary_key=True)
    
    module_id = Column(Integer)
    access_level = Column(String(32)) #admin, content, member

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