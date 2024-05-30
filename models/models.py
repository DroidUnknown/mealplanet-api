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
    insertion_timestamp = MetaDataColumn(DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)"))
    modification_timestamp = MetaDataColumn(DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"))

# ----------------------------------------------------------------------------------------------------------------------

class Scope(Model):
    __tablename__ = 'scope'
    scope_id = Column(Integer, primary_key=True)
    scope_name = Column(String(128)) # content-team
    keycloak_scope_id = Column(Integer)

class Resource(Model):
    __tablename__ = 'resource'
    resource_id = Column(Integer, primary_key=True)
    resource_name = Column(String(128)) # brand-profile
    display_name = Column(String(128))
    uri = Column(String(128))
    scope_id = Column(Integer) # content-team
    keycloak_resource_id = Column(Integer)

class Policy(Model):
    __tablename__ = 'policy'
    
    policy_id = Column(Integer, primary_key=True)
    policy_name = Column(String(128)) # brand-profile:view
    keycloak_policy_id = Column(Integer)

class PolicyRoleAccessMap(Model):
    __tablename__ = 'policy_role_access_map'
    
    policy_role_access_map_id = Column(Integer, primary_key=True)
    policy_id = Column(Integer) # brand-profile:view
    role_id = Column(Integer) # content-team
    access_p = Column(Boolean) # 1: positive, 0: negative

class Permission(Model):
    __tablename__ = 'permission'
    
    permission_id = Column(Integer, primary_key=True)
    permission_name = Column(String(128)) # View Brand Profile Permission
    permission_type = Column(String(32)) # resource-based, scope-based
    decision_strategy = Column(String(32)) # affirmative, unanimous, consensus
    keycloak_permission_id = Column(Integer)

class PermissionResourceMap(Model):
    __tablename__ = 'permission_resource_map'
    
    permission_resource_map_id = Column(Integer, primary_key=True)
    permission_id = Column(Integer) # View Brand Profile Permission
    resource_id = Column(Integer) # brand-profile

class PermissionPolicyMap(Model):
    __tablename__ = 'permission_policy_map'
    
    permission_policy_map_id = Column(Integer, primary_key=True)
    permission_id = Column(Integer) # View Brand Profile Permission
    policy_id = Column(Integer) # brand-profile:view

# ----------------------------------------------------------------------------------------------------------------------

# Backend access control at an API level
class Resource(Model):
    __tablename__ = 'resource'
    resource_id = Column(Integer, primary_key=True)
    resource_name = Column(String(128))
    resource_type = Column(String(32))
    business_context = Column(String(32))
    path_regex = Column(String(128))
    action_name = Column(String(64))
    method = Column(String(32))
    input_fields = Column(JSON)
    output_fields = Column(JSON)
    resource_parent_id = Column(String(128))
    pagination_max_limit = Column(Integer)

class RoleResourcePermissionMap(Model):
    __tablename__ = 'role_resource_permission_map'
    role_resource_permission_map_id = Column(Integer, primary_key=True)
    role_id = Column(Integer)
    resource_id = Column(Integer)
    permission = Column(String(2))

class Role(Model):
    __tablename__ = 'role'

    role_id = Column(Integer, primary_key=True)
    role_name = Column(String(64), nullable=False)  # admin, manager, user
    role_description = Column(String(128), nullable=False)
    
    keycloak_role_id = Column(Integer)

class User(Model):
    __tablename__ = 'user'

    user_id = Column(Integer, primary_key=True)

    username = Column(String(64))
    keycloak_user_id = Column(Integer)

    first_names_en = Column(String(128))
    last_name_en = Column(String(128))
    first_names_ar = Column(String(128))
    last_name_ar = Column(String(128))

    phone_nr = Column(String(32), unique=True)
    email = Column(String(128))

    access_token = Column(String(64))
    token_expiry_timestamp = Column(DATETIME(fsp=6))

    root_p = Column(Boolean)

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

