from tornado import web

from core.libs.config_controller import get_config
from views import MainHandler, SocketHandler


class Application(web.Application):
    def __init__(self, *args, **kwargs):
        self.config = get_config()
        handlers = [
            (r'/', MainHandler),
            (r'/ws', SocketHandler),
        ]

        super(Application, self).__init__(*args, handlers=handlers, **kwargs)

        # todo: create tables here and for acccess in handlers, append db object to Application
