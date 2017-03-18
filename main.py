import logging
import ssl

from tornado import ioloop, httpserver
from tornado.log import enable_pretty_logging, LogFormatter

from core.application import Application
from core.db_access_control import db_controller
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


def create_server(config, enable_client_validation=True):
    """ Creates a HTTPS Tornado Server.

    :param config: the application config
    :param enable_client_validation: if set to True, client certificates will be required
        for https connections
    """

    if enable_client_validation:
        ssl_context = ssl.create_default_context(
            ssl.Purpose.CLIENT_AUTH,
            cafile=config.certificates.get_cert_path('cert_authority', 'cert')
        )

        # enforce the certificate expected from the client
        ssl_context.verify_mode = ssl.CERT_REQUIRED
    else:
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

    # set the key and certificate used by the server
    ssl_context.load_cert_chain(
        config.certificates.get_cert_path('server', 'cert'),
        config.certificates.get_cert_path('server', 'key'),
    )

    return httpserver.HTTPServer(Application(debug=config.server.debug), ssl_options=ssl_context)


def main():
    config = get_config()
    set_logger(config)

    db_controller.setup_database_sync()

    create_server(config).listen(port=config.server.port, address=config.server.host)

    logging.info('Starting server: {}'.format(config.server.name))

    ioloop.IOLoop.current().start()

if __name__ == '__main__':
    main()
