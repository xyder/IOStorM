from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base

from core.libs.config_controller import get_config

metadata = MetaData(schema=get_config().database.schema)
Base = declarative_base(metadata=metadata)

from models.test_item import TestItem
