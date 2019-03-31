import tornado.autoreload
import tornado.httpserver
import tornado.ioloop
import tornado.web

import service.handlers
from service.redis import clear_redis


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/service", service.handlers.TestHandler),
            (r"/service/auth", service.handlers.AuthHandler),
            (r"/service/comp", service.handlers.CompetitionHandler),
            (r"/service/user", service.handlers.UserHandler)
        ]
        settings = dict(debug=True, cookie_secret='66o0TzKaPOGtYdkL7xEmGepeuuYi7EPnp2XdTP1o&Vo=')
        tornado.web.Application.__init__(self, handlers, **settings)


if __name__ == "__main__":
    clear_redis()
    app = tornado.httpserver.HTTPServer(Application())
    app.listen(8888)
    instance = tornado.ioloop.IOLoop.instance()
    tornado.autoreload.start(instance)
    instance.start()
