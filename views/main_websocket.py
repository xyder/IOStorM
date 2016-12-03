import json
import logging
from urllib.parse import urlparse

from tornado import websocket


class SocketHandler(websocket.WebSocketHandler):
    @property
    def app_config(self):
        return self.application.config

    @property
    def db(self):
        return self.application.db

    def __init__(self, *args, **kwargs):
        super(SocketHandler, self).__init__(*args, **kwargs)

    def prepare(self):
        self.set_header(
            'Strict-Transport-Security',
            'max-age={}; includeSubdomains'.format(self.app_config.web_sockets.ws_sts_max_age)
        )
        super(SocketHandler, self).prepare()

    def check_origin(self, origin):
        """
        Checks if the origin of the client is allowed
        :param origin: the origin of the client
        :return: True if the origin is allowed
        """

        logging.info('Client connection attempt: {}'.format(origin))

        # parse the origin url
        parsed_origin = urlparse(origin)

        # extract hostname from urls. accepted formats:
        #   'http://example.com:2000'
        #   'example.com:2000'
        #   'example.com'
        hostname = parsed_origin.hostname or parsed_origin.path.split(':')[0]
        return hostname in self.app_config.web_sockets.cors_origins

    def data_received(self, chunk):
        super(SocketHandler, self).data_received(chunk)

    def open(self):
        logging.info('WebSocket opened.')

    def on_message(self, message):
        message = json.loads(message)
        print(message)
        self.write_message(json.dumps({
            'data': 'OK',
            'status': 'OK'
        }))

    def on_close(self):
        logging.info('WebSocket closed.')
