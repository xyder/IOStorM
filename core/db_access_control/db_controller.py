from sqlalchemy.sql import ddl
from tornado import gen

from core.async_controller import run_sync
from core.db_access_control.db_connection import DBConnection
from core.libs.config_controller import get_config
from models.table_orders import get_table_order


def create_schema(schema='', check_first=True, async=True):
    """ Creates a schema.

    :type schema: str
    :param schema: the name of the schema to be created

    :type check_first: bool
    :param check_first: if True, it will check first if the schema already exists

    :type async: bool
    :param async: if True, it will run this function asynchronously

    :return: a Future if async was True, or the result of the cursor.execute function
    """

    schema = schema or get_config().database.schema
    command = ddl.CreateSchema(schema).check_first(check_first)

    return DBConnection.execute_command(command, async=async)


def drop_schema(schema='', cascade=False, check_first=True, async=True):
    """ Drops a schema.

    :type schema: str
    :param schema: the name of the schema to be dropped.

    :type cascade: bool
    :param cascade: if true it will also drop the objects contained in the specified schema

    :type check_first: bool
    :param check_first: if True, it will check if the schema does not already exist

    :type async: bool
    :param async: if True, it will run this function asynchronously

    :return: a Future if async was True, or the result of the cursor.execute function
    """

    schema = schema or get_config().database.schema
    command = ddl.DropSchema(schema, cascade=cascade).check_first(check_first)

    return DBConnection.execute_command(command, async=async)


def create_table(table, check_first=True, async=True):
    """ Creates a table.

    :type table: sqlalchemy.Table
    :param table: a SQLAlchemy Table specification used in the table creation

    :type check_first: bool
    :param check_first: if True, it will check if the table already exists

    :type async: bool
    :param async: if True, it will run the function asynchronously
    """

    command = ddl.CreateTable(table).check_first(check_first)

    return DBConnection.execute_command(command, async=async)


def drop_table(table, check_first=True, async=True):
    """ Drops a table.

    :type table: sqlalchemy.Table
    :param table: a SQLAlchemy Table specification used in the table deletion

    :type check_first: bool
    :param check_first: if True, it will check if the table actually exists

    :type async: bool
    :param async: if True, it will run the function asynchronously
    """

    command = ddl.DropTable(table).check_first(check_first)

    return DBConnection.execute_command(command, async=async)


@gen.coroutine
def create_tables(metadata=None, tables=None, check_first=True):
    """ Creates all specified tables or all tables in a specified metadata, async.

    :param metadata: the metadata which will be used to determine the tables to be created

    :type tables: Iterable
    :param tables: an Iterable containing tables

    :type check_first: bool
    :param check_first: if True, it will check if the tables actually exist
    """

    tables = tables or metadata.tables.values()

    for table in tables:
        yield create_table(table, check_first)


@gen.coroutine
def drop_tables(metadata=None, tables=None, check_first=True):
    """ Drops all specified tables or all tables in a specified metadata, async.

    :param metadata: the metadata which will be used to determine the tables to be dropped

    :type tables: Iterable
    :param tables: an Iterable containing tables

    :type check_first: bool
    :param check_first: if True, it will check if the tables actually exist
    """

    tables = tables or metadata.tables.values()

    for table in tables:
        yield drop_table(table, check_first)


@gen.coroutine
def setup_database(clean=False):
    """ Creates the schema and all tables required by the app.

    :param clean: if True, it will delete all existing elements
    """

    if clean:
        drop_order = yield get_table_order(for_drop=True)
        yield drop_tables(tables=drop_order)
        yield drop_schema()

    yield create_schema()
    create_order = yield get_table_order()
    yield create_tables(tables=create_order)


def setup_database_sync(clean=False):
    run_sync(setup_database, clean=clean)
