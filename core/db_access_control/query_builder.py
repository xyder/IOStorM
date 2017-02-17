import sqlalchemy
from sqlalchemy.dialects import postgresql

from core.db_access_control.db_exceptions import PartialPrimaryKeyException

DIALECT = postgresql.dialect()


class QueryBuilder(object):
    """ Class that holds methods for SQL query and objects preparation. """
    @staticmethod
    def columns_to_dict(obj, columns, filtered=True):
        """ Retrives a dict of column names and their values.

        :param obj: the object from where the params are extracted.

        :type columns: list
        :param columns: the column names used in building the result

        :type filtered: bool
        :param filtered: if True, then None and Empty objects will be removed from the result.

        :rtype: dict
        :return: a dict containing the column names and their values
        """

        # create dict with all columns
        params = {c[0]: getattr(obj, c[0]) for c in columns}

        if not filtered:
            return params

        # filter out those which are None or Empty
        return {k: v for k, v in params.items() if v not in (None, '')}

    @staticmethod
    def build_clause(comparator, columns, **kwargs):
        """ Builds a clause separated by the given comparator.

        :type comparator: collections.abc.Callable
        :param comparator: the comparator function which will be used to join all the clauses

        :type columns: sqlalchemy.sql.base.ColumnCollection
        :param columns: the columns which will be compared

        :type kwargs: dict
        :param kwargs: the values associated with the column names which will be compared

        :rtype: sqlalchemy.sql.elements.BooleanClauseList
        :return: the built clause
        """

        return comparator(*(column == kwargs[column.name] for column in columns))

    @classmethod
    def build_pk_clause(cls, table, **kwargs):
        """ Builds an AND clause with the pk fields and the values received as function arguments.

        :type table: sqlalchemy.Table
        :param table: the SQLAlchemy table

        :type kwargs: dict
        :param kwargs: the pk names and their desired values

        :rtype: sqlalchemy.sql.elements.BooleanClauseList
        :return: the built clause
        """

        # get columns which were not specified in kwargs
        missing_keys = [column.name for column in table.primary_key.columns if column.name not in kwargs]

        if len(missing_keys) != 0:
            raise PartialPrimaryKeyException(missing_keys=missing_keys)

        # join the conditions for the pk using AND operator
        return cls.build_clause(sqlalchemy.and_, table.primary_key.columns, **kwargs)

    @staticmethod
    def list_mapper(values, columns, converter=lambda **kwargs: kwargs):
        """ A base row parser that maps the row values to the columns and passes them to an object constructor

        :type values: list
        :param values: the row values

        :param columns: the columns (cursor.description)

        :type converter: collections.abc.Callable
        :param converter: an object instance constructor

        :return: the resulting object instance
        """

        return converter(**{column[0]: values[index] for index, column in enumerate(columns)})

    @staticmethod
    def get_compiled_command(command, dialect=DIALECT):
        """ Compiles a SQLAlchemy commmand and binds the command parameters.

        :param command: the SQLAlchemy command
        :param dialect: the SQL dialect that will be used for command compiling

        :rtype: str
        :return: the SQL command
        """

        try:
            return str(command.compile(dialect=dialect, compile_kwargs={'literal_binds': True}))
        except TypeError as t:
            # suppress exception for literal_binds argument not being expected
            if 'literal_binds' not in t.args[0]:
                raise

            return str(command)
