from tornado import gen

from models.tag import Tag
from models.user import User
from models.user_property import UserProperty

_create_order = (User, UserProperty, Tag,)
_drop_order = (UserProperty, Tag, User,)


@gen.coroutine
def get_table_order(for_drop=False):
    """ Retrieves the order of tables for creation/deletion

    :type for_drop: bool
    :param for_drop: if True - it will retrieve the drop order,
        otherwise it will retrieve the create order

    :rtype: tuple
    :return: a tuple of tables
    """

    if for_drop:
        return tuple(x.__table__ for x in _drop_order)

    return tuple(x.__table__ for x in _create_order)
