from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base

from core.db_access_control.sqla_utils import SQLAUtils
from core.libs.config_controller import get_config

Base = declarative_base(metadata=MetaData(schema=get_config().database.schema, bind=SQLAUtils.get_engine()))
