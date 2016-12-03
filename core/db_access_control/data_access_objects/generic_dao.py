from core.db_access_control.db_controller import get_cursor, get_connection
from core.db_access_control.sql_query_builder import SQLQueryBuilder
from core.libs.config_controller import get_config


class GenericDAO(object):
    """ A generic DAO used to manage database operations """

    table_name = '<not specified>'
    pk_column = 'id'
    structure = {}

    @classmethod
    def create_element(cls, obj):
        """ Adds base container type object to the table.

        :param BaseContainer obj: a BaseContainer type object.
        """

        ret = cls._create_element(table_name=cls.table_name, values=obj.to_row_dict())

        # update returned values in the object
        obj.update(**ret)

    @classmethod
    def create_table(cls):
        """ Create the table using the class attributes. """

        cls._init_table_structure()
        cls._create_table(cls.table_name, cls.structure)

    @classmethod
    def count(cls):
        """ Returns the number of rows in the table. """
        return cls._count(cls.table_name)

    @classmethod
    def update_element(cls, obj):
        """ Updates a base container type object from the table.

        :param BaseContainer obj: the object to be updated.
        """

        cls._update_element(table_name=cls.table_name, values=obj.to_row_dict(), id_value=obj.id)

    @classmethod
    def _count(cls, table_name, connection=None):
        """ Retrieves the number of rows in the table. """
        connection = connection or cls._get_connection()
        cursor = cls._get_cursor(connection)
        config = cls._get_database_config()

        command = SQLQueryBuilder.count(
            schema_name=config.schema,
            table_name=table_name
        )

        cursor.execute(command)
        return cursor.fetchone()['count']

    @classmethod
    def _create_element(cls, table_name, values, connection=None):
        """ Inserts an element into the table.

        :param str table_name: the name of the table
        :param dict values: a dict containing the columns and their values
        :param connection: a database connection to be used
        :return: if the `values` dict contains an `'@returning_columns'` list specified, a list of all specified
        columns and their values will be returned.
        """

        connection = connection or cls._get_connection()
        cursor = cls._get_cursor(connection)
        config = cls._get_database_config()

        # store and remove the '@returning_columns' pair to ensure is not sent to the query builder
        returning_columns = values.pop('@returning_columns', [])

        command = SQLQueryBuilder.create_element(
            schema_name=config.schema,
            table_name=table_name,
            values=values,
            returning_columns=returning_columns
        )

        cursor.execute(*command)
        connection.commit()

        if returning_columns:
            return cursor.fetchone()

    @classmethod
    def _create_table(cls, table_name, structure, connection=None):
        """ Creates a table.

        :param str table_name: the name of the table
        :param dict[str] structure: the structure of the table columns
        :param connection: a database connection to be used
        """

        connection = connection or cls._get_connection()
        cursor = cls._get_cursor(connection)
        config = cls._get_database_config()

        command = SQLQueryBuilder.create_table(schema_name=config.schema, table_name=table_name, structure=structure)

        cursor.execute(command)
        connection.commit()

    @classmethod
    def _delete_element(cls, table_name, id_value, id_column=pk_column, connection=None):
        """ Deletes an element from the table.

        :param str table_name: the name of the table
        :param id_value: the value of the pk column
        :param str id_column: the name of the pk column
        :param connection: a database connection to be used
        :return: True if a row was deleted.
        :rtype: bool
        """

        connection = connection or cls._get_connection()
        cursor = cls._get_cursor(connection)
        config = cls._get_database_config()

        command = SQLQueryBuilder.delete_element_by_id(
            schema_name=config.schema,
            table_name=table_name,
            id_value=id_value,
            id_column=id_column
        )

        cursor.execute(*command)
        connection.commit()

        return cursor.rowcount > 0

    @staticmethod
    def _get_connection():
        """ Returns a database connection object.

        :return: a connection object.
        """

        return get_connection()

    @classmethod
    def _get_cursor(cls, connection=None, named=False, scrollable=None):
        """ Creates and returns a cursor object.

        :param connection: a database connection object.
        """

        return get_cursor(connection or cls._get_connection(), named, scrollable)

    @staticmethod
    def _get_database_config(config_file=''):
        """ Retrieves the database config parameters.

        :return: the database config
        :rtype: DatabaseConfig
        """

        return get_config(config_file=config_file).database

    @classmethod
    def _get_all(cls, table_name, converter=(lambda **a: a), converter_args=None, connection=None):
        connection = connection or cls._get_connection()
        cursor = cls._get_cursor(connection, named=True)
        config = cls._get_database_config()

        command = SQLQueryBuilder.get_all(
            schema_name=config.schema,
            table_name=table_name
        )

        cursor.execute(command)

        converter_args = converter_args or {}
        for row in cursor:
            row.update(converter_args)
            yield converter(**row)

    @classmethod
    def _get_element(
            cls, table_name, id_value, id_column=pk_column,
            converter=(lambda **a: a), converter_args=None, connection=None
    ):
        """ Retrieves an element from the table.

        :param str table_name: the name of the table
        :param id_value: the value of the pk column
        :param str id_column: the name of the pk column
        :param callable converter: a converter function which will parse the retrieved values.
        :param dict converter_args: a dictionary of args to be passed to the converter
        :param connection: a database connection to be used
        :return: the values of select row
        """

        connection = connection or cls._get_connection()
        cursor = cls._get_cursor(connection)
        config = cls._get_database_config()

        command = SQLQueryBuilder.get_element_by_id(
            schema_name=config.schema,
            table_name=table_name,
            id_column=id_column,
            id_value=id_value
        )

        cursor.execute(*command)
        ret = cursor.fetchone()

        converter_args = converter_args or {}
        try:
            ret.update(converter_args)
        except AttributeError:
            raise Exception('Element "{}" in table {}.{} could not be found.'.format(
                id_value, config.schema, table_name))

        return converter(**ret)

    @classmethod
    def _init_table_structure(cls):
        """ Initializes the table and columns structure (types and names)
        """

        raise NotImplementedError

    @classmethod
    def _update_element(cls, table_name, values, id_value, id_column=pk_column, connection=None):
        """ Updates an element from the table.

        :param str table_name: the name of the table
        :param dict values: dict containing the columns and values to be changed.
        :param id_value: value of the pk column
        :param str id_column: name of the pk column
        :param connection: a database connection
        """

        values.pop('@returning_columns', [])

        connection = connection or cls._get_connection()
        cursor = cls._get_cursor(connection)
        config = cls._get_database_config()

        command = SQLQueryBuilder.update_element_by_id(
            schema_name=config.schema,
            table_name=table_name,
            values=values,
            id_column=id_column,
            id_value=id_value
        )

        cursor.execute(*command)
        connection.commit()
