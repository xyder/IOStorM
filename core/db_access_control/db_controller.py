import logging
import uuid

import psycopg2.extras

from core.libs.config_controller import get_config


def prepare_db_driver(connection):
    """ Loads and registers db extensions. """

    psycopg2.extras.register_uuid()
    psycopg2.extensions.register_type(psycopg2.extensions.UNICODE, connection)
    psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY, connection)


def get_connection():
    """ Creates a connection object to the database.

    :return: the connection object
    """

    config = get_config()

    # try to load from cache
    connection = getattr(get_connection, '_connection', None)

    if connection is None or connection.closed:
        # create the connection
        connection = psycopg2.connect(
            host=config.database.host,
            database=config.database.name,
            user=config.database.user,
            port=config.database.port,
            password=config.database.password
        )

        # failed to connect
        if connection.closed:
            logging.error('Could not connect to {db_name} with {user}'.format(
                db_name='', user=''))
            return

        # load extensions
        prepare_db_driver(connection)

        # cache the connection object
        setattr(get_connection, '_connection', connection)

    return connection


def get_cursor(connection=None, named=True, scrollable=None):
    """ Creates a cursor on the given connection.

    :param connection: the connection object used to create the cursor.
    :param bool named: if set to True, the cursor will be named (server-side cursor)
    :param bool scrollable: will only be considered if `named` == True.
        if set to True, cursor will be scrollable bidirectionally.
    :return: the created cursor
    """

    connection = connection or get_connection()

    if named:
        # using a named connection to create a server-side cursor for better memory performance
        # the server-side cursor will exist for the duration of the transaction
        return connection.cursor(
            str(uuid.uuid4()),
            cursor_factory=psycopg2.extras.RealDictCursor,
            scrollable=scrollable)

    return connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


