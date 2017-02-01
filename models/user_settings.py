from sqlalchemy import Column, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID

from models import Base


class UserSettings(Base):
    __tablename__ = 'user_settings'

    uid = Column('uid', Integer, primary_key=True, unique=True, nullable=False)
    user_id = Column('user_id', UUID, ForeignKey('users.uid', ondelete='CASCADE'), nullable=False)

    key = Column('key', Text)
    value = Column('value', Text)
    value_type = Column('value_type', Text)
