from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy_utils import LtreeType

from core.db_access_control.db_entity import DBEntity
from models import Base


class Tag(DBEntity, Base):
    __tablename__ = 'tag'

    uid = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey('user.uid', ondelete='CASCADE'), nullable=False)

    path = Column(LtreeType, nullable=False, unique=True)
    position = Column(Integer, nullable=False)

    title = Column(Text)
    description = Column(Text)
