from sqlalchemy import Column, Integer, Text
from sqlalchemy.orm import relationship

from core.db_access_control import DBEntity
from core.libs.utils import get_func_args
from models import Base


class User(DBEntity, Base):
    __tablename__ = 'users'

    uid = Column('uid', Integer, primary_key=True, unique=True, nullable=False)

    user_name = Column('user_name', Text, unique=True, nullable=False)
    full_name = Column('full_name', Text)

    key_hash = Column('key_hash', Text)
    settings = relationship('UserSettings', cascade='all, delete-orphan', backref='user')

    @staticmethod
    def get_hash(key):
        # TODO: implement this
        return '<hash generator is not implemented yet>'

    def __init__(self, user_name, uid=None, key=None, full_name='', key_hash=''):
        # fetch all arguments for this function
        kwargs = get_func_args()
        kwargs.pop('self')

        if 'key' in kwargs:
            kwargs['key_hash'] = self.get_hash(kwargs.pop('key'))

        super().__init__(**kwargs)
