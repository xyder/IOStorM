from sqlalchemy import Column, Text
from sqlalchemy import Integer
from sqlalchemy.orm import relationship

from core.db_access_control.db_entity import DBEntity
from core.libs.utils import get_func_args
from models import Base


class User(DBEntity, Base):
    __tablename__ = 'users'

    uid = Column(Integer, primary_key=True)

    user_name = Column(Text, unique=True, nullable=False)
    first_name = Column(Text)
    last_name = Column(Text)

    key_hash = Column(Text)
    settings = relationship('UserSettings', cascade='all, delete-orphan', backref='user')

    @staticmethod
    def get_hash(key):
        # TODO: implement this
        return '<hash generator is not implemented yet>'

    def __init__(self, user_name, uid=None, key=None, first_name=None, last_name=None, key_hash=None):
        # fetch all arguments for this function
        kwargs = get_func_args()
        kwargs.pop('self')

        if 'key' in kwargs:
            kwargs['key_hash'] = self.get_hash(kwargs.pop('key'))

        super().__init__(**kwargs)
