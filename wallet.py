import logging
import os
import time
from jsonrpc import ServiceProxy

import tornado.ioloop
import tornado.web
import tornado.options
import tornado.httpserver
import tornado.escape
import tornado.websocket

from variables import *

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/max_address", MaxAddressHandler),
            (r"/max_transaction/(\w+)", MaxTransactionHandler),
        ]
        settings = dict(
            cookie_secret="43oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
            login_url="/login",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            site_name='wallet gateway',
            xsrf_cookies=False,
            debug=True,
            gzip=True
        )
        tornado.web.Application.__init__(self, handlers, **settings)
        
        self.btcdb = btcdb
        self.maxdb = maxdb

        self.btcwallet = btcwallet
        self.maxwallet = maxwallet
        

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return None

    @property
    def btcdb(self):
        return self.application.btcdb

    @property
    def maxdb(self):
        return self.application.maxdb

    @property
    def maxwallet(self):
        return self.application.maxwallet

    @property
    def btcdb(self):
        return self.application.btcdb


class MainHandler(BaseHandler):
    def get(self):
        text = self.maxwallet.getinfo()
        self.write(text)


class MaxAddressHandler(BaseHandler):
    def get(self):
        address = self.maxwallet.getnewaddress()
        self.write(address)


class MaxTransactionHandler(BaseHandler):
    def get(self, txid):
        print txid
        trans = maxwallet.gettransaction(txid)
        trans['address'] = x['address']
        maxdb.transactions.insert(trans)


def main():
    http_server = tornado.httpserver.HTTPServer(Application(), xheaders=True)
    http_server.listen(8000)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    tornado.options.parse_command_line()
    logging.info("Starting web server on port 8000")

    main()
