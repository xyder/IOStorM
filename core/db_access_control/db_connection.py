import logging

import momoko
from psycopg2 import ProgrammingError
from tornado import gen
from tornado.concurrent import Future
from tornado.ioloop import IOLoop

from core.async_controller import run_sync
from core.db_access_control import sqla_utils
from core.db_access_control.db_exceptions import exception_wrapper
from core.db_access_control.ddl_utils.exist_condition_patcher import enable_patches
from core.db_access_control.ddl_utils.query_builder import QueryBuilder
from core.libs.config_controller import get_config


# enable conditional SQL statements
enable_patches()


@gen.coroutine
def _get_pool(io_loop=None):
    """ Retrieves the Momoko connection pool.

    :type io_loop: IOLoop
    :param io_loop: the IO Loop that this object will be attached to.
        Defaults to a new instance if None.

    :rtype: momoko.Pool
    :return: the Momoko Pool object
    """

    io_loop = io_loop or IOLoop.current()

    pool = getattr(_get_pool, '_pool', None)  # type: momoko.Pool
    if not pool:
        db_config = get_config().database

        pool = momoko.Pool(
            dsn=db_config.dsn, size=1, ioloop=io_loop, raise_connect_errors=True)

        setattr(_get_pool, '_pool', pool)
    else:
        pool.ioloop = io_loop

    return pool


class DBConnection(object):

    get_pool = staticmethod(_get_pool)

    @classmethod
    @gen.coroutine
    def get_connection(cls, io_loop=None):
        """ Connects to the database using a Momoko Pool.

        :type io_loop: IOLoop
        :param io_loop: the IO Loop to which the pool is attached.

        :rtype: momoko.Pool
        :return: the connected pool
        """

        pool = yield cls.get_pool(io_loop=io_loop)  # type: momoko.Pool
        connection = yield pool.connect()

        return connection

    @classmethod
    @gen.coroutine
    def execute_command_wrapper(
            cls, exception_type=ProgrammingError, message_validator=lambda s: False, **kwargs):
        """ Wraps a SQL query execution and consumes an exception which matches the type and
        condition specified.

        :param exception_type: the type of the exception to be consumed

        :type message_validator: collections.abc.Callable
        :param message_validator: the validator for the exception message

        :type kwargs: dict
        :param kwargs: keyword arguments that will be passed to the command executing function

        :rtype: list
        :return: the result set of the command execution
        """

        result = yield exception_wrapper(
            function=cls.execute_command,
            exception_type=exception_type,
            message_validator=message_validator,
            **kwargs
        )
        return result

    @classmethod
    def execute_command(
            cls, command, io_loop=None, row_parser=QueryBuilder.list_mapper,
            parser_kwargs=None, async=True):
        """ Execute an SQL command.

        :param command: the SQL command string or an SQLAlchemy object that is compilable

        :type io_loop: IOLoop
        :param io_loop: the IO Loop to which the coroutines will be attached

        :type row_parser: collections.abc.Callable
        :param row_parser: a function that can receive the following args:
            values, columns, converter (see `list_mapper` for an example)

        :type parser_kwargs: dict
        :param parser_kwargs: keyword arguments that will be passed to `row_parser` for each item

        :type async: bool
        :param async: determines if the command should by executed asynchronously

        :rtype: list
        :return: a list of results generated after running row_parser on each row
        """

        if async:
            return cls.execute_command_async(
                command=command,
                io_loop=io_loop,
                row_parser=row_parser,
                parser_kwargs=parser_kwargs
            )
        else:
            return run_sync(
                func=cls.execute_command_async,
                command=command,
                io_loop=io_loop,
                row_parser=row_parser,
                parser_kwargs=parser_kwargs
            )

    @classmethod
    @gen.coroutine
    def execute_command_async(
            cls, command, io_loop=None, row_parser=QueryBuilder.list_mapper, parser_kwargs=None):
        """ Executes a database command asynchronously.

        :param command: the SQL command string or an SQLAlchemy object that is compilable

        :type io_loop: IOLoop
        :param io_loop: the IO Loop to which the coroutines will be attached

        :type row_parser: collections.abc.Callable
        :param row_parser: a function that can receive the following args:
            values, columns, converter (see `list_mapper` for an example)

        :type parser_kwargs: dict
        :param parser_kwargs: kwargs that will be passed to `row_parser` for each item

        :rtype: list
        :return: a list of results generated after running row_parser on each row
        """

        parser_kwargs = parser_kwargs or {}
        ret_values = []
        db_config = get_config().database

        # get a database connection
        conn = yield cls.get_connection(io_loop=io_loop)

        # compile the command if necessary
        if not isinstance(command, str):
            command.bind = sqla_utils.SQLAUtils.get_engine()
            command = QueryBuilder.get_compiled_command(command)

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
                    # warning: using coroutines for small operations on each row
                    # greatly increases execution time
                    ret_value = yield ret_value

                # don't store if no value was returned
                if not ret_value:
                    continue

                # store the return value
                ret_values.append(ret_value)

        return ret_values
