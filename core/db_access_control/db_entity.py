from functools import partial

import sqlalchemy
from tornado import concurrent

from core.db_access_control.db_utils import execute_command, list_mapper, get_sync_result
from core.libs.exceptions import IncorrectResultSizeException


class DBEntity(object):
    __tablename__ = ''
    __table__ = None  # type: sqlalchemy.Table

    get_sync_result = staticmethod(get_sync_result)

    def __init__(self, *args, **kwargs):
        del args  # ignore the args

        # not calling super() to prevent SQLA default constructor to trigger
        # providing this functionality manually
        for key in kwargs:
            if not hasattr(self, key):
                raise TypeError('{key} is an invalid keyword argument for {cls}'.format(
                    key=key, cls=self.__class__.__name__
                ))

            setattr(self, key, kwargs[key])

        self.columns = self.__table__.c

    @staticmethod
    def _build_clause(comparator, columns, **kwargs):
        """ Builds a clause separated by the given comparator.

        :type comparator: collections.abc.Callable
        :param comparator: the comparator function which will be used to join all the clauses

        :type columns: sqlalchemy.sql.base.ColumnCollection
        :param columns: the columns which will be compared

        :type kwargs: dict
        :param kwargs: the values associated with the column names which will be compared

        :rtype: sqlalchemy.sql.elements.BooleanClauseList|sqlalchemy.sql.elements.BinaryExpression
        :return: the built clause
        """

        return comparator(*(column == kwargs[column.name] for column in columns))

    @classmethod
    def _build_pk_clause(cls, **kwargs):
        """ Builds an AND clause with the pk fields and the values received as function arguments.

        :type kwargs: dict
        :param kwargs: the pk names and their desired values

        :rtype: sqlalchemy.sql.elements.BooleanClauseList|sqlalchemy.sql.elements.BinaryExpression
        :return: the built clause
        """

        # join the conditions for the pk using AND operator
        return cls._build_clause(sqlalchemy.and_, cls.__table__.primary_key.columns, **kwargs)

    @classmethod
    def get(cls, condition=None, async=True):
        """ Retrieve a list of elements from the database using the given condition.

        :type condition: sqlalchemy.sql.elements.BooleanClauseList|sqlalchemy.sql.elements.BinaryExpression
        :param condition: the condition applied when selecting the elements

        :type async: bool
        :param async: if True, retrieves the result asynchronously

        :rtype: concurrent.Future|list
        :return: a Future for the result or a list of elements
        """

        # build the sql command
        command = sqlalchemy.select([cls])
        if condition is not None:
            command = command.where(condition)

        # build the row parser to convert to class instance
        row_parser = partial(list_mapper, converter=cls)

        if async:
            return execute_command(command=command, row_parser=row_parser)  # type: concurrent.Future
        else:
            return cls.get_sync_result(func=execute_command, command=command, row_parser=row_parser)

    @classmethod
    def get_first(cls, condition=None):
        """ Retrieves sync the first element returned by a select with the specified condition, or None.

        :rtype: sqlalchemy.sql.elements.BooleanClauseList|sqlalchemy.sql.elements.BinaryExpression
        :param condition: the condition for the select

        :return: an instance of this class
        """

        result = cls.get(condition=condition, async=False)

        if not result:
            return None

        return result[0]

    @classmethod
    def get_by_pk(cls, async=True, **kwargs):
        """ Retrieve an element by primary key(s).

        :type async: bool
        :param async: if True, retrieves the result asynchronously

        :type kwargs: dict
        :param kwargs: the primary key fields and their values

        :return: if async is True, it will return a list of objects.
        If async is False, it will return an object, or None
        """

        result = cls.get(condition=cls._build_pk_clause(**kwargs), async=async)

        # return async result
        if async:
            return result

        # check if sync result is None
        if not result:
            return None

        # check query did not return multiple values (in case of incorrect PK clause)
        expected_result_size = 1
        if len(result) != expected_result_size:
            raise IncorrectResultSizeException(len(result), expected_result_size)

        # return the first and only element
        return result[0]

    @classmethod
    def create(cls, returning=(), async=True, **kwargs):
        """ Performs an insert with the given values.

        :type returning: tuple|list
        :param returning: the columns which will be returned after the insert is performed

        :type async: bool
        :param async: if True, performs the action asynchronously

        :type kwargs: dict
        :param kwargs: values which will be used to populate the element to be inserted

        :return: the value of the column(s) specified in the `returning` field
        """

        command = cls.__table__.insert().values(**kwargs)

        # if no `returning` columns are specified, add the primary key columns
        returning = returning if len(returning) else cls.__table__.primary_key.columns
        command = command.returning(*returning)

        if async:
            return execute_command(command=command)
        else:
            return cls.get_sync_result(func=execute_command, command=command)

    def update(self):
        pass

    def delete(self):
        pass

    def __repr__(self):
        # sort the column keys
        sorted_columns = sorted(self.__table__.columns, key=lambda c: c.key)

        # build a generator for the instance attributes
        sorted_pairs = ((column.key, getattr(self, column.key)) for column in sorted_columns)

        return '<{name}: {data}>'.format(
            name=self.__class__.__name__,
            data=', '.join('{} = {}'.format(k, v) for k, v in sorted_pairs))
