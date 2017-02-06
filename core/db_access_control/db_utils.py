import logging

import momoko
from psycopg2 import ProgrammingError
from sqlalchemy import create_engine
from sqlalchemy.dialects import postgresql
from tornado import concurrent, gen
from tornado.concurrent import Future
from tornado.ioloop import IOLoop

from core.libs.config_controller import get_config
from core.libs.exceptions import MissingArgsException

BATCH_SIZE = get_config().database.batch_size


def get_engine(echo=False):
    """ Retrieves the database engine (SQLAlchemy - sync).

    :return: the database engine
    """

    db_config = get_config().database

    engine = getattr(get_engine, '_db_engine', None)
    if engine is None:
        engine = create_engine(db_config.dsn)
        setattr(get_engine, '_db_engine', engine)

    engine.echo = echo

    return engine


def get_sync_result(func=None, future=None, *args, **kwargs):
    """ Return the results from an async function or a future, synchronously.

    :type func: collections.abc.Callable
    :param func: the function to be called

    :type future: concurrent.Future
    :param future: a future which, if specified, will be used instead of `func` and all other arguments will be ignored

    :type args: list
    :param args: the arguments to be passed to the function

    :type kwargs: dict
    :param kwargs: the keyword arguments to be passed to the function

    :return: the result of the function call
    """

    if not func and not future:
        raise MissingArgsException('Callable or Future')

    ioloop = IOLoop.instance()
    future = future or func(*args, **kwargs)  # type: concurrent.Future
    ioloop.add_future(future, lambda _: ioloop.stop())
    ioloop.start()

    return future.result()


@gen.coroutine
def get_pool(io_loop=None):
    """ Retrieves the Momoko connection pool.

    :type io_loop: IOLoop
    :param io_loop: the IO Loop that this object will be attached to.
        Defaults to a new instance if None.

    :rtype: momoko.Pool
    :return: the Momoko Pool object
    """

    io_loop = io_loop or IOLoop.current()

    pool = getattr(get_pool, '_pool', None)  # type: momoko.Pool
    if not pool:
        db_config = get_config().database

        pool = momoko.Pool(
            dsn=db_config.dsn, size=1, ioloop=io_loop, raise_connect_errors=True)

        setattr(get_pool, '_pool', pool)
    else:
        pool.ioloop = io_loop

    return pool


@gen.coroutine
def get_connection(io_loop=None):
    """ Connects to the database using a Momoko Pool.

    :type io_loop: IOLoop
    :param io_loop: the IO Loop to which the pool is attached.

    :rtype: momoko.Pool
    :return: the connected pool
    """

    pool = yield get_pool(io_loop=io_loop)  # type: momoko.Pool
    connection = yield pool.connect()

    return connection


def get_compiled_command(command, dialect=postgresql.dialect()):
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


@gen.coroutine
def exception_wrapper(function, exception_type=ProgrammingError, message_validator=lambda s: False, **kwargs):
    """ Wraps a function execution and consumes an exception which matches the type and the condition specified.

    :param function: the function to call

    :param exception_type: the type of the exception to be consumed

    :type message_validator: collections.abc.Callable
    :param message_validator: the condition for the exception message for which the exception is ignored

    :type kwargs: dict
    :param kwargs: keyword arguments that will be passed to the function

    :rtype: list
    :return: the result of the command execution
    """

    result = []
    try:
        result = yield function(**kwargs)
    except exception_type as e:
        s = str(e.args[0]).strip()

        if not message_validator(s):
            raise

    return result


@gen.coroutine
def execute_command_wrapper(exception_type=ProgrammingError, message_validator=lambda s: False, **kwargs):
    """ Wraps a SQL query execution and consumes an exception which matches the type and condition specified.

    :param exception_type: the type of the exception to be consumed

    :type message_validator: collections.abc.Callable
    :param message_validator: the validator for the exception message

    :type kwargs: dict
    :param kwargs: keyword arguments that will be passed to the command executing function

    :rtype: list
    :return: the result set of the command execution
    """

    result = yield exception_wrapper(
        function=execute_command,
        exception_type=exception_type,
        message_validator=message_validator,
        **kwargs
    )
    return result


def execute_command(command, io_loop=None, row_parser=list_mapper, parser_kwargs=None, async=True):
    """ Execute an SQL command.

    :param command: the SQL command string or an SQLAlchemy object that is compilable

    :type io_loop: IOLoop
    :param io_loop: the IO Loop to which the coroutines will be attached

    :type row_parser: collections.abc.Callable
    :param row_parser: a function that can receive the following args: values, columns, converter
        (see `list_mapper` for an example)

    :type parser_kwargs: dict
    :param parser_kwargs: keyword arguments that will be passed to `row_parser` for each item

    :type async: bool
    :param async: determines if the command should by executed asynchronously

    :rtype: list
    :return: a list of results generated after running row_parser on each row
    """

    if async:
        return execute_command_async(
            command=command,
            io_loop=io_loop,
            row_parser=row_parser,
            parser_kwargs=parser_kwargs
        )
    else:
        return get_sync_result(
            func=execute_command_async,
            command=command,
            io_loop=io_loop,
            row_parser=row_parser,
            parser_kwargs=parser_kwargs
        )


@gen.coroutine
def execute_command_async(command, io_loop=None, row_parser=list_mapper, parser_kwargs=None):
    """ Executes a database command asynchronously.

    :param command: the SQL command string or an SQLAlchemy object that is compilable

    :type io_loop: IOLoop
    :param io_loop: the IO Loop to which the coroutines will be attached

    :type row_parser: collections.abc.Callable
    :param row_parser: a function that can receive the following args: values, columns, converter
        (see `list_mapper` for an example)

    :type parser_kwargs: dict
    :param parser_kwargs: kwargs that will be passed to `row_parser` for each item

    :rtype: list
    :return: a list of results generated after running row_parser on each row
    """

    parser_kwargs = parser_kwargs or {}
    ret_values = []
    db_config = get_config().database

    # get a database connection
    conn = yield get_connection(io_loop=io_loop)

    # compile the command if necessary
    if not isinstance(command, str):
        command = get_compiled_command(command)

    if db_config.debug_sql:
        logging.info('Running SQL:\n {}'.format(str(command).strip()))

    # execute the command
    cursor = yield conn.execute(command)

    while True:
        # call fetchmany asynchronously
        results = yield exception_wrapper(
            function=gen.Task,
            message_validator=lambda s: s == 'no results to fetch',
            func=lambda callback: callback(cursor.fetchmany(db_config.batch_size))
        )

        # exit the loop if no more results where found
        if not results:
            break

        for result in results:
            # parse the results and store the returned value
            ret_value = row_parser(result, cursor.description, **parser_kwargs)

            # if the row_parser returned a Future object, yield it
            if isinstance(ret_value, Future):
                # warning: using coroutines for small operations on each row greatly increases execution time
                ret_value = yield ret_value

            # don't store if no value was returned
            if not ret_value:
                continue

            # store the return value
            ret_values.append(ret_value)

    return ret_values
