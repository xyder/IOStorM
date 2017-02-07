from sqlalchemy import create_engine

from core.libs.config_controller import get_config


def _get_engine(echo=False):
    """ Retrieves the database engine (SQLAlchemy - sync).

    :return: the database engine
    """

    db_config = get_config().database

    engine = getattr(_get_engine, '_db_engine', None)
    if engine is None:
        engine = create_engine(db_config.dsn)
        setattr(_get_engine, '_db_engine', engine)

    engine.echo = echo

    return engine


class SQLAUtils(object):
    """ Class that provides generic methods to work with SQLAlchemy. """

    get_engine = staticmethod(_get_engine)
