import sqlalchemy
from sqlalchemy.sql import ddl
from tornado import gen
from tornado.ioloop import IOLoop

from core.db_access_control.db_utils import execute_command_wrapper
from core.libs.config_controller import get_config


class DBController(object):

    _exception_wrapper = staticmethod(execute_command_wrapper)

    @classmethod
    @gen.coroutine
    def create_schema(cls):
        """ Creates a schema if it does not already exist. """

        config = get_config()
        yield cls._exception_wrapper(
            message_validator=lambda s: s.startswith('schema ') and s.endswith(' already exists'),
            command=ddl.CreateSchema(config.database.schema)
        )

    @classmethod
    @gen.coroutine
    def drop_schema(cls, cascade=False):
        """ Drops a schema if it exists.

        :type cascade: bool
        :param cascade: if true it will also drop the objects contained in the specified schema.
        """

        config = get_config()
        yield cls._exception_wrapper(
            message_validator=lambda s: s.startswith('schema ') and s.endswith(' does not exist'),
            command=ddl.DropSchema(config.database.schema, cascade=cascade)
        )

    @classmethod
    @gen.coroutine
    def create_table(cls, table):
        """ Creates a table.

        :type table: sqlalchemy.Table
        :param table: a SQLAlchemy Table specification used in the table creation
        """

        yield cls._exception_wrapper(
            message_validator=lambda s: s.startswith('relation ') and s.endswith(' already exists'),
            command=ddl.CreateTable(table))

    @classmethod
    @gen.coroutine
    def create_all(cls, metadata=None, tables=None):
        """ Creates all the tables in the specified metadata or list of tables.

        :type metadata: sqlalchemy.MetaData
        :param metadata: a SQLAlchemy metadata object for which all tables will be created

        :type tables: list[sqlalchemy.Table]
        :param tables: a list of tables that, if specified, will take priority over the metadata argument
        """

        tables = tables or metadata.tables.values()
        for table in tables:
            yield cls.create_table(table)

    @classmethod
    @gen.coroutine
    def drop_table(cls, table):
        """ Drops a table.

        :type table: sqlalchemy.Table
        :param table: the table to be dropped
        """

        yield cls._exception_wrapper(
            message_validator=lambda s: s.startswith('table ') and s.endswith(' does not exist'),
            command=ddl.DropTable(table))

    @classmethod
    @gen.coroutine
    def drop_all(cls, metadata=None, tables=None):
        """ Drops all tables in a metadata.

        :type metadata: sqlalchemy.MetaData
        :param metadata: the metadata that contains information about the tables about to be dropped

        :type tables: list[sqlalchemy.Table]
        :param tables: if specified, this list of tables will be dropped instead of the ones in the metadata
        """

        tables = tables or metadata.tables.values()
        for table in tables:
            yield cls.drop_table(table)

    @classmethod
    @gen.coroutine
    def _setup_database(cls, clean=False):
        """ Creates the application schema and tables asynchronously, optionally deleting existing objects.

        :type clean: bool
        :param clean: if true it will also delete the schema and tables that are already present
        """

        from models import drop_order, create_order

        if clean:
            yield cls.drop_all(tables=drop_order)
            yield cls.drop_schema()

        yield cls.create_schema()
        yield cls.create_all(tables=create_order)

    @classmethod
    @gen.coroutine
    def setup_database(cls, clean=False, async=False):
        """ Creates the necessary database layout for the application.

        :type clean: bool
        :param clean: if true it will delete the application schema and tables before creating them

        :type async: bool
        :param async: if true it will run the functions asynchronously. This might cause unexpected results.
        """

        if async:
            yield cls._setup_database(clean=clean)
        else:
            instance = IOLoop.instance()
            instance.run_sync(lambda: cls._setup_database(clean=clean))
