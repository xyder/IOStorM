from sqlalchemy import Column, Integer, Text
from sqlalchemy.orm import relationship

from models import Base


class User(Base):
    __tablename__ = 'users'

    uid = Column('uid', Integer, primary_key=True, unique=True, nullable=False)
    user_name = Column('user_name', Text, unique=True, nullable=False)
    full_name = Column('full_name', Text)
    key_hash = Column('key_hash', Text)
    settings = relationship('UserSettings', cascade='all, delete-orphan', backref='user')
