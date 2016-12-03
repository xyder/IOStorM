class Modifiers:
    pk = 'PRIMARY KEY'
    default = 'DEFAULT'
    reference = 'REFERENCES {}'
    cascade_delete = 'ON DELETE CASCADE'


class Types:
    blob = 'BYTEA'
    uuid = 'UUID'
    text = 'TEXT'
    auto_uuid = '{}{{}} extensions.uuid_generate_v4()'.format(uuid)


class SQLQueryBuilder(object):
    """ Class containing methods for building SQL queries. """

    @staticmethod
    def _build_params_list(separator, params_dict):
        """ Builds a string containing a list of query params.

        :param str separator: separates the query params
        :param dict params_dict: the params to be inserted in the string
        :return: the built string
        """

        return separator.join('{key} = %({key})s'.format(key=k) for k in sorted(params_dict.keys()))

    @staticmethod
    def get_column(column_type, *modifiers):
        """ Builds a SQL column string.

        :param str column_type: the type of the column
        :param iterable modifiers: modifiers to be added to the column
        :return: the built column string
        :rtype: str
        """

        column_modifiers = '' if not modifiers else ' {}'.format(' '.join(modifiers))

        # if necessary, build the modifiers using str.format
        if column_type in [Types.auto_uuid]:
            return column_type.format(column_modifiers)

        return '{}{}'.format(column_type, column_modifiers)

    @staticmethod
    def create_schema(schema_name):
        """ Builds a schema creation SQL query.

        :param schema_name: the name of the schema
        :return: the built query.
        :rtype: str
        """

        return 'CREATE SCHEMA IF NOT EXISTS {};'.format(schema_name)

    @staticmethod
    def create_table(schema_name, table_name, structure, check_exist=True):
        """ Creates a table creation SQL query.

        :param str table_name: the name of the table to be created
        :param str schema_name: the name of the schema to which the table should be attached
        :param dict[str] structure: a dict containing columns and their column strings
        :param bool check_exist: if True it will add an `IF NOT EXISTS` to the query
        :return: the built SQL query
        :rtype: str
        """

        # adds the table existence check if specified
        check_exist = 'IF NOT EXISTS ' if check_exist else ''

        return 'CREATE TABLE {exists}{schema}.{table_name} (\n\t{data}\n);'.format(
            exists=check_exist,
            schema=schema_name,
            table_name=table_name,
            data=',\n\t'.join('{} {}'.format(k, v) for k, v in structure.items())
        )

    @classmethod
    def get_all(cls, schema_name, table_name):
        return 'SELECT * from {schema_name}.{table_name};'.format(
            schema_name=schema_name,
            table_name=table_name
        )

    @classmethod
    def get_element(cls, schema_name, table_name, cond_dict):
        """ Creates a row select SQL query.

        :param str schema_name: the name of the schema
        :param str table_name: the name of the table
        :param dict cond_dict: a dictionary containing the condition with columns and expected values.
        :return: the built SQL query
        :rtype: str
        """

        return 'SELECT * FROM {schema}.{table_name} WHERE {cond};'.format(
            schema=schema_name,
            table_name=table_name,
            cond=cls._build_params_list(' AND ', cond_dict)
        ), cond_dict

    @classmethod
    def get_element_by_id(cls, schema_name, table_name, id_value, id_column='id'):
        """ Creates a row select SQL query filtered by the pk value.

        :param str schema_name: the name of the schema
        :param str table_name: the name of the table
        :param id_value: the value of the pk
        :param str id_column: the name of the pk column
        :return: the built SQL query
        :rtype: str
        """

        return cls.get_element(
            schema_name=schema_name,
            table_name=table_name,
            cond_dict={id_column: id_value}
        )

    @staticmethod
    def count(schema_name, table_name):
        """ Creates a row count SQL query.

        :param str schema_name: the name of the schema
        :param str table_name: the name of the table
        """

        return 'SELECT count(*) FROM {schema_name}.{table_name}'.format(
            schema_name=schema_name,
            table_name=table_name
        )

    @staticmethod
    def create_element(schema_name, table_name, values, returning_columns=''):
        """ Creates a row insertion SQL query.

        :param str schema_name: the name of the schema for the table
        :param str table_name: the name of the table where the row will be inserted.
        :param dict values: a dict containings columns and their values
        :param list[str] returning_columns: a list containing the names of the columns to be returned by the method
        :return: (query, values) - a tuple containing the built SQL query and the values
        :rtype: (str, dict)
        """

        # add the RETURNING modifier if needed
        modifiers = '' if not returning_columns else ' RETURNING {}'.format(
            ', '.join(returning_columns))

        keys = sorted(values.keys())
        return 'INSERT INTO {schema}.{table_name}({columns}) VALUES ({values}){modifiers};'.format(
            schema=schema_name,
            table_name=table_name,
            columns=', '.join(keys),
            values=', '.join('%({})s'.format(k) for k in keys),
            modifiers=modifiers
        ), values

    @classmethod
    def delete_element(cls, schema_name, table_name, cond_dict):
        """ Creates a row delete SQL query.

        :param str schema_name: the name of the schema
        :param str table_name: the name of the table
        :param cond_dict: a dictionary containing the condition with columns and their expected values
        :return: the built SQL query
        :rtype: str
        """

        return 'DELETE FROM {schema}.{table_name} WHERE {cond};'.format(
            schema=schema_name,
            table_name=table_name,
            cond=cls._build_params_list(' AND ', cond_dict)
        ), cond_dict

    @classmethod
    def delete_element_by_id(cls, schema_name, table_name, id_value, id_column='id'):
        """ Creates a row delete SQL query filtered by pk value.

        :param str schema_name: the name of the schema
        :param str table_name: the name of the table
        :param id_value: the value of the pk column
        :param str id_column: the name of the pk column
        :return: the built SQL query
        :rtype: str
        """

        return cls.delete_element(
            schema_name=schema_name,
            table_name=table_name,
            cond_dict={id_column: id_value}
        )

    @classmethod
    def update_element_by_id(cls, schema_name, table_name, values, id_value, id_column='id'):
        """ Crates a row update SQL query filtered by pk value.

        :param str schema_name: the name of the schema
        :param str table_name: the name of the table
        :param dict values: dictionary containing the values to be updated
        :param id_value: value of the pk column
        :param str id_column: name of the pk column
        :return: the built SQL query
        :rtype: str
        """

        return cls.update_element(
            schema_name=schema_name,
            table_name=table_name,
            cond_dict={id_column: id_value},
            values=values
        )

    @classmethod
    def update_element(cls, schema_name, table_name, cond_dict, values):
        """ Creates a row update SQL query.

        :param str schema_name: the name of the schema
        :param str table_name: the name of the table
        :param dict cond_dict: dictionary containing the columns and their expected values
        :param dict values: dictionary containing the values to be updated
        :return: the built SQL query
        :rtype: str
        """

        query_params = cond_dict.copy()
        query_params.update(values)

        return 'UPDATE {schema}.{table_name} SET {data} WHERE {cond};'.format(
            schema=schema_name,
            table_name=table_name,
            data=cls._build_params_list(', ', values),
            cond=cls._build_params_list(' AND ', cond_dict)
        ), query_params
