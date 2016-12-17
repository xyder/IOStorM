from sqlalchemy.exc import ProgrammingError
from sqlalchemy.sql.ddl import CreateSchema, DropSchema

from core.db_access_control.db_utils import get_connection
from core.libs.config_controller import get_config
from models.base import Base


class DBController(object):
    @staticmethod
    def create_schema():
        """ Creates a schema if it does not already exist. """

        config = get_config()

        try:
            get_connection().execute(CreateSchema(config.database.schema))
        except ProgrammingError as p:
            s = str(p.orig).strip()
            if not (s.startswith('schema ') and s.endswith(' already exists')):
                raise

    @staticmethod
    def drop_schema():
        """ Drops a schema if it exists. """

        config = get_config()

        try:
            get_connection().execute(DropSchema(config.database.schema))
        except ProgrammingError as p:
            s = str(p.orig).strip()
            if not (s.startswith('schema ') and s.endswith(' does not exist')):
                raise

    @classmethod
    def setup_database(cls, clean=False):
        """ Creates the necessary database layout for the application.

        :param bool clean: if true it will delete the application schema and tables before creating them
        """

        if clean:
            Base.metadata.drop_all()
            cls.drop_schema()

        cls.create_schema()
        # get_metadata().create_all()
        Base.metadata.create_all()
