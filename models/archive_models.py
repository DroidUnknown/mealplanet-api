from email.policy import default
from enum import unique
import json
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
    print("archive db created people, Alhamdulillaah")


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

    meta_status = MetaDataColumn(String(16), nullable=False)  # active, inactive, deleted
    tags = MetaDataColumn(JSON)
    tenant_id = MetaDataColumn(Integer, nullable=False)
    system_user_p = MetaDataColumn(Boolean)

    # either a user id or a system ID
    creation_user_id = MetaDataColumn(Integer, nullable=False)
    modification_user_id = MetaDataColumn(Integer)  # either a user id or a system ID
    insertion_timestamp = MetaDataColumn(DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)"))
    modification_timestamp = MetaDataColumn(DATETIME(fsp=6), nullable=False)

