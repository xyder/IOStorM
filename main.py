import logging
import ssl

from tornado import ioloop, httpserver
from tornado.log import enable_pretty_logging, LogFormatter

from core.application import Application
from core.libs.config_controller import get_config


def set_logger(config):
    """ Sets logging for the server.

    :param config: the application configuration
    """

    level = logging.DEBUG if config.server.debug or config.server.testing else logging.INFO

    log_formatter = LogFormatter(
        fmt='[%(asctime)s][%(module)s:%(lineno)d] --> %(levelname)s: %(message)s',
        datefmt='%y.%m.%d-%H:%M:%S'
    )

    handler = logging.StreamHandler()
    handler.setFormatter(log_formatter)
    handler.setLevel(level)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)

    enable_pretty_logging(logger=root_logger)


def create_server(config):
    """ Creates a HTTPS Tornado Server.

    :param config: the application config
    """

    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    # set the key and certificate used by the server
    ssl_context.load_cert_chain(
        config.certificates.get_cert_path('server', 'cert'),
        config.certificates.get_cert_path('server', 'key'),
    )

    # set and enforce the certificate expected from the client
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    ssl_context.load_verify_locations(
        config.certificates.get_cert_path('cert_authority', 'cert')
    )

    return httpserver.HTTPServer(Application(), ssl_options=ssl_context)


def create_database():
    # TODO: implement database creation function
    pass


def main():
    config = get_config()
    set_logger(config)

    create_database()
    create_server(config).listen(port=config.server.port, address=config.server.host)

    logging.info('Starting server: {}'.format(config.server.name))

    ioloop.IOLoop.current().start()

if __name__ == '__main__':
    main()
