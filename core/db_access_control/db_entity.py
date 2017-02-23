from functools import partial

import sqlalchemy
from tornado import concurrent

from core.db_access_control.db_connection import DBConnection
from core.db_access_control.db_exceptions import IncorrectResultSizeException, SaveEntityFailedException
from core.db_access_control.ddl_utils.query_builder import QueryBuilder


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

        self.columns = self.__table__.columns.items()
        self.pk_columns = self.__table__.primary_key.columns.items()
        self.non_pk_columns = [x for x in self.columns if x not in self.pk_columns]

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

        return DBConnection.execute_command(command=command, async=async)

    def delete(self, async=True):
        """ Deletes this instance from the database.

        :type async: bool
        :param async: if True, it will perform the action asynchronously.
        """

        self.delete_element(condition=QueryBuilder.build_pk_clause(self.__table__, **self.get_pk_fields()), async=async)

    @classmethod
    def delete_element(cls, condition=None, async=True):
        """ Performs a delete with the given condition.

        :type condition: sqlalchemy.sql.elements.BooleanClauseList|sqlalchemy.sql.elements.BinaryExpression
        :param condition: the condition on which the delete will be performed

        :type async: bool
        :param async: if True, it will perform the action asynchronously
        """

        command = cls.__table__.delete()

        if condition is not None:
            command = command.where(condition)

        return DBConnection.execute_command(command=command, async=async)

    def get_all_fields(self):
        """ Retrieves a dict of all column names and their values.

        :rtype: dict
        :return: a dict containing the column names and their types
        """

        return QueryBuilder.columns_to_dict(self, self.columns)

    def get_non_pk_fields(self):
        """ Retrieves a dict of non-primary key column names and their values.

        :rtype: dict
        :return: dict containing the column names and their values
        """

        return QueryBuilder.columns_to_dict(self, self.non_pk_columns)

    def get_pk_fields(self):
        """ Retrieves a dict of primary key column names and their values.

        :rtype: dict
        :return: dict containing the column names and their values
        """

        return QueryBuilder.columns_to_dict(self, self.pk_columns)

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
        command = cls.__table__.select()
        if condition is not None:
            command = command.where(condition)

        # build the row parser to convert to class instance
        row_parser = partial(QueryBuilder.list_mapper, converter=cls)

        return DBConnection.execute_command(command=command, row_parser=row_parser, async=async)

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

        result = cls.get(condition=QueryBuilder.build_pk_clause(cls.__table__, **kwargs), async=async)

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

    def save(self, async=True):
        """ Saves the instance to the database and fills in the generated values.

        :type async: bool
        :param async: If True, will run the command asynchronously.
        """

        # TODO: fill in based on custom subclass `returning` list for default/generated values
        returned = self.create(async=async, **self.get_non_pk_fields())
        if len(returned) != 1:
            raise SaveEntityFailedException('Invalid number of pk fields used - {}.'.format(len(returned)))

        returned = returned[0]  # type: dict
        for k, v in returned.items():
            setattr(self, k, v)

    def update(self, async=True):
        """ Updates the database with the information from this instance.

        :type async: bool
        :param async: if True, it will perform the action asynchronously.
        """

        self.update_element(
            condition=QueryBuilder.build_pk_clause(self.__table__, **self.get_pk_fields()),
            async=async, **self.get_non_pk_fields()
        )

    @classmethod
    def update_element(cls, condition=None, async=True, **kwargs):
        """ Performs an update with the given args and condition.

        :type condition: sqlalchemy.sql.elements.BooleanClauseList|sqlalchemy.sql.elements.BinaryExpression
        :param condition: the condition on which the update will be performed.

        :type async: bool
        :param async: if True, it will run the command asynchronously.

        :type kwargs: dict
        :param kwargs: args with values to be updated
        """

        command = cls.__table__.update().values(**kwargs)

        if condition is not None:
            command = command.where(condition)

        return DBConnection.execute_command(command=command, async=async)

    def __repr__(self):
        """ Returns the representation of this instance. """

        # sort the column keys
        sorted_columns = sorted(self.__table__.columns, key=lambda c: c.key)

        # build a generator for the instance attributes
        sorted_pairs = ((column.key, getattr(self, column.key)) for column in sorted_columns)

        return '<{name}: {data}>'.format(
            name=self.__class__.__name__,
            data=', '.join('{} = {}'.format(k, v) for k, v in sorted_pairs))

    # str of this object will return the same as repr
    __str__ = __repr__
