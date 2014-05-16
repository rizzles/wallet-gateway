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
import tornado.gen
import tornado.httpclient

from variables import *

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/new_address/(\w+)", AddressHandler),
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
        
        self.mongodb = mongodb

        self.btcwallet = btcwallet
        self.maxwallet = maxwallet
        self.ltcwallet = ltcwallet
        self.dogewallet = dogewallet
        

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return None

    @property
    def mongodb(self):
        return self.application.mongodb

    @property
    def maxwallet(self):
        return self.application.maxwallet

    @property
    def btcwallet(self):
        return self.application.btcwallet

    @property
    def dogewallet(self):
        return self.application.dogewallet

    @property
    def ltcwallet(self):
        return self.application.ltcwallet


class MainHandler(BaseHandler):
    def get(self):
        text = self.maxwallet.getinfo()
        self.write(text)


class AddressHandler(BaseHandler):
    def get(self, coin):
        if coin == 'btc':
            #address = self.btcwallet.getnewaddress()
            address = "1DogUco8GeDDGCkXb2R4GXWZPxfjDFov3g"
        elif coin == 'ltc':
            #address = self.ltcwallet.getnewaddress()
            address = "LdUrUvSo8wQsuAaUj4H2BGW7UumjeZ3gXG"
        elif coin == 'doge':
            #address = self.dogewallet.getnewaddress()
            address = "D9SPWsfm8GfLCFf4JoQsEfRRNJwBDAxoEx"
        elif coin == 'max':
            #address = self.maxwallet.getnewaddress()
            address = "mdAtks9Cgthoj2MmQ5zGw3DdJjHEKjFN1U"
        self.write(address)


class MaxTransactionHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.engine
    def get(self, txid):
        trans = maxwallet.gettransaction(txid)
        print trans
        trans['address'] = trans['details'][0]['address']
        trans['currency'] = 'max'
        mongodb.transactions.insert(trans)
        
        client = tornado.httpclient.AsyncHTTPClient()
        response = yield tornado.gen.Task(client.fetch, 'http://ec2-54-221-32-214.compute-1.amazonaws.com:8000/transaction?address=%s&currency=max'%address)
        self.finish()


def main():
    http_server = tornado.httpserver.HTTPServer(Application(), xheaders=True)
    http_server.listen(8000)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    tornado.options.parse_command_line()
    logging.info("Starting web server on port 8000")

    main()
