from functools import partial

import sqlalchemy
from tornado import concurrent, gen
from tornado.ioloop import IOLoop

from core.db_access_control.db_utils import execute_command, list_mapper


class DBEntity(object):
    __tablename__ = ''
    __table__ = None  # type: sqlalchemy.Table

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
    @gen.coroutine
    def get(cls, condition=None):
        """ Retrieve a list of elements from the database using the given condition.

        :type condition: sqlalchemy.sql.elements.BooleanClauseList|sqlalchemy.sql.elements.BinaryExpression
        :param condition: the condition applied when selecting the elements

        :rtype: concurrent.Future
        :return: a list of elements
        """

        if condition is None:
            raise Exception("Can't fetch item without a filter.")

        # build the sql command
        command = sqlalchemy.select([cls]).where(condition)

        # build the row parser to convert to class instance
        row_parser = partial(list_mapper, converter=cls)

        result = yield execute_command(command=command, row_parser=row_parser)
        return result

    @classmethod
    def get_by_pk(cls, **kwargs):
        """ Retrieve an element by primary key(s).

        :type kwargs: dict
        :param kwargs: the primary key fields and their values

        :return: an instance of this class or None
        """

        result = cls.get(cls._build_pk_clause(**kwargs))  # type: concurrent.Future

        # run the async function synchronously
        instance = IOLoop.instance()
        instance.run_sync(lambda: result)

        # fetch the result
        result = result.result()

        if not result:
            return None

        if len(result) != 1:
            raise Exception('get_by_pk returned more than 1 result.')

        return result[0]

    def create(self):
        pass

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
