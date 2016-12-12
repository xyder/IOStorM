import os
import yaml

from core.libs.utils import get_parent_directory

PROJECT_PATH = get_parent_directory(os.path.abspath(__file__), levels_count=3)

# change this to load a different config file
APPLICATION_CONFIG_FILE = os.path.normpath(os.path.join(PROJECT_PATH, 'config.yml'))


def load_config(config_file_path):
    """ Loads a yaml config file into a dict.

    :param str config_file_path:
    :return: the config dict
    :rtype: dict
    """

    with open(config_file_path, 'r') as f:
        config_dict = yaml.load(f)

    # append the base_path element which stores the project directory path
    if 'base_path' not in config_dict or not config_dict['base_path']:
        config_dict['base_path'] = PROJECT_PATH

    return config_dict


def reccursive_formatter(val, config_dict, is_path=False):
    """ Recursively formats the strings and normalizes paths.

    :param val: current value to process
    :param dict config_dict: the configuration dict which is used for string replacements
    :param bool is_path: if set to True, it will normalize the path
    :return: the formatted value
    """

    if type(val) is str:
        # replace string format placeholders repeatedly until no change is detected
        while True:
            aux = val
            val = val.format(_=config_dict)
            if val == aux:
                break

        # if the string is a path, normalize it
        if is_path:
            return os.path.normpath(val)
        return val

    if type(val) is list:
        return [reccursive_formatter(x, config_dict, is_path) for x in val]

    if type(val) is dict:
        return {k: reccursive_formatter(v, config_dict, 'path' in k) for k, v in val.items()}

    return val


class BaseEntity:
    """ A base entity class to serve as base for config classes. """

    def _load_attributes(self, attributes, config_dict=None):
        """ Loads the specified attributes values into the instance attributes.

        :param dict attributes: the attributes to be loaded
        :param dict config_dict: the config dictionary to be used for formatting any contained strings
        """

        config_dict = config_dict or {}
        for k, v in attributes.items():
            if hasattr(self, k):
                setattr(self, k, reccursive_formatter(v, config_dict, 'path' in k))
            else:
                raise AttributeError('Object has no attribute {}'.format(k))

    def __str__(self):
        return '<{}>\n{}'.format(
            self.__class__.__name__,
            '\n'.join('    \'{}\': {}'.format(
                k, str(v).replace('\n', '\n    ')
            ) for k, v in sorted(self.__dict__.items())))


class BaseConfig(BaseEntity):
    """ A base config class. """

    def __init__(self, key_path, config_dict):
        """ Initializes the config object.

        :param list[str] key_path: list containing the path in the config_dict tree
        :param dict config_dict: a dict containing the  configuration for this object. treated as a tree.
        """

        section = config_dict
        for key in key_path:
            section = section[key]

        section = section or {}
        self._load_attributes(section, config_dict)


class DatabaseConfig(BaseConfig):
    """ Stores the database configuration parameters. """

    def __init__(self, key_path, config_dict):
        self.schema = ''
        self.name = ''
        self.user = ''
        self.password = ''
        self.host = ''
        self.port = 5432
        self.stream_results = None
        self.batch_size = 10000

        super(DatabaseConfig, self).__init__(key_path, config_dict)

        self.host = self.host or 'localhost'


class ServerConfig(BaseConfig):
    """ Stores the server configuration parameters. """

    def __init__(self, key_path, config_dict):
        self.host = ''
        self.port = 0
        self.name = ''
        self.app_name = ''
        self.debug = False
        self.testing = False

        super(ServerConfig, self).__init__(key_path, config_dict)


class WebSocketsConfig(BaseConfig):
    """ Stores the web sockets configuration parameters. """

    def __init__(self, key_path, config_dict):
        self.ws_sts_max_age = 0
        self.cors_origins = []

        super(WebSocketsConfig, self).__init__(key_path, config_dict)


class CertificatesConfig(BaseConfig):
    """ Stores the SSL certificates configuration parameters. """

    def __init__(self, key_path, config_dict):
        self.certs_path = ''
        self.base_certificate = {}
        self.certificates = {}

        super(CertificatesConfig, self).__init__(key_path, config_dict)

    def get_cert_path(self, key, ext):
        """ Builds the path to a certificate file.

        :param str key: the key used to retrieve the directory path and file name from the certificates dict
        :param str ext: the extension used as the second section of the file name
        :return: the built and normalized path
        :rtype: str
        """

        return os.path.join(
            os.path.normpath(self.certificates[key]['dir_path']),
            os.path.normpath('{}.{}.pem'.format(self.certificates[key]['file_name'], ext))
        )


class ApplicationConfig(BaseEntity):
    """ Stores the application configuration parameters. """

    def __init__(self, config_file_path):
        """ Loads the specified configuration file and creates the configuration objects.

        :param str config_file_path: the file path to load as config file.
        """

        config_dict = load_config(config_file_path)

        # load server config
        self.server = ServerConfig(['server'], config_dict)

        # load web sockets config
        self.web_sockets = WebSocketsConfig(['web_sockets'], config_dict)

        # load certificates config
        self.certificates = CertificatesConfig(['certificates'], config_dict)

        # load database config
        self.database = DatabaseConfig(['database'], config_dict)


def get_config(config_file=''):
    """ Loads configuration into cache.

    :return: the app configuration object
    :rtype: ApplicationConfig
    """

    config_file = config_file or APPLICATION_CONFIG_FILE

    if getattr(get_config, '_config', None) is None:
        setattr(get_config, '_config', ApplicationConfig(config_file))

    return getattr(get_config, '_config')

