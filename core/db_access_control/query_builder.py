import sqlalchemy

from core.libs.exceptions import PartialPrimaryKeyException


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
        params = {c[0]: getattr(obj, c[0], None) for c in columns}

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

        :rtype: sqlalchemy.sql.elements.BooleanClauseList|sqlalchemy.sql.elements.BinaryExpression
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

        :rtype: sqlalchemy.sql.elements.BooleanClauseList|sqlalchemy.sql.elements.BinaryExpression
        :return: the built clause
        """

        expected = len(table.primary_key.columns)
        received = len(kwargs)
        if expected != received:
            raise PartialPrimaryKeyException(received=received, expected=expected)

        # join the conditions for the pk using AND operator
        return cls.build_clause(sqlalchemy.and_, table.primary_key.columns, **kwargs)
