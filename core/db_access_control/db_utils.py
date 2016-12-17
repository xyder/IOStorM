from functools import partial
from sqlalchemy import create_engine

from core.libs.config_controller import get_config

BATCH_SIZE = get_config().database.batch_size


def get_engine(echo=False):
    """ Retrieves the database engine.

    :return: the database engine.
    """

    db_config = get_config().database

    if getattr(get_engine, '_db_engine', None) is None:
        engine = create_engine('postgresql://{user}:{password}@{host}:{port}/{database}'.format(
            user=db_config.user,
            password=db_config.password,
            host=db_config.host,
            port=db_config.port,
            database=db_config.name
        ))
        engine = engine
        setattr(get_engine, '_db_engine', engine)

    getattr(get_engine, '_db_engine').echo = echo
    return getattr(get_engine, '_db_engine')


def get_connection():
    """ Retrieves a database connection.

    :return: a db connection.
    """

    return get_engine().connect()


class BatchedResult(object):
    """ Class that enables batched iteration over a database result set. """

    def __init__(self, cursor, converter=None, batch_size=BATCH_SIZE):
        self.cursor = cursor
        self.converter = partial(self._convert_to_instance, converter)
        self.batch_size = batch_size

    @staticmethod
    def _convert_to_instance(converter, args):
        """ Applies a conversion over a set of arguments using a given converter.

        :param converter: the converter function (constructor)
        :param args: arguments for the converter function
        :return:
        """

        return args if not converter else converter(*args)

    @classmethod
    def _generator_func(cls, cursor, converter, batch_size=BATCH_SIZE):
        """ Batched generator function for the db result set.

        :param cursor: a cursor over the database results.
        :param converter: a function to convert rows to instances (constructor)
        :param int batch_size: the size of the batch to be iterated on each pass.
        :return: a generator for the results
        """

        while True:
            # fetch the results
            results = cursor.fetchmany(batch_size)

            # generate the results and convert them to instances
            yield from (converter(result) for result in results)

            # finished the results set
            if not results:
                break

    def __iter__(self):
        return self._generator_func(cursor=self.cursor, converter=self.converter, batch_size=self.batch_size)
