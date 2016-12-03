from tornado import web


class MainHandler(web.RequestHandler):
    def data_received(self, chunk):
        super(MainHandler, self).data_received(chunk)

    def get(self):
        self.write('Hello, world!')
