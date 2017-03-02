from sqlalchemy import Column, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID

from models import Base


class UserProperty(Base):
    __tablename__ = 'user_property'

    uid = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey('user.uid', ondelete='CASCADE'), nullable=False)

    key = Column(Text)
    value = Column(Text)
    value_type = Column(Text)
