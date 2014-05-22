import logging
import os
import time
import datetime
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
        
        self.mongo = mongo

        self.btcwallet = btcwallet
        self.maxwallet = maxwallet
        self.ltcwallet = ltcwallet
        self.dogewallet = dogewallet
        

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return None

    @property
    def mongo(self):
        return self.application.mongo

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

    # return user from database for whichever site
    def find_user(self, trans, site):
        address = trans['details'][0]['address']
        return self.mongo['bitusenet'].users.find_one({'address':address})

    # add all transactions received from wallets into transaction database
    def add_transactions(self, trans):
        address = trans['details'][0]['address']
        self.mongo['transactions'].transactions.update({"_id":address},{"$set":{"transactions.%s"%trans['txid']:trans}}, True)        

    # add the transaction from the wallet to the users account
    def add_transactions_user(self, trans, user, site):
        address = trans['details'][0]['address']
        amount = trans['details'][0]['amount']
        usertrans = {'txid':trans['txid'], 'confirmations': trans['confirmations'], 'amount':amount, 'time':trans['time'], 'timestamp':datetime.datetime.utcnow()}
        user['price'][address][-1]['transactions'][trans['txid']] = usertrans
        if trans['confirmations'] == 0:        
            user['price'][address][-1]['sent'] += amount
        self.mongo[site].users.update({'address':address}, {"$set":{"price":user['price']}})
        return user

    # if price quote was too old, get a new one.
    def calculate_newcharge(self, trans, user, currency, site):
        if trans['confirmations'] > 0:        
            return user
        address = trans['details'][0]['address']
        diff = trans['time'] - user['price'][address][-1]['created']
        #if diff > 1:
        if diff > 3600:
            print "Charge is too old. Calculating new price"
            price = self.mongo[site].currencies.find_one()[currency][site]
            newcharge = {'price':price, 'created':int(time.time()), 'currency':currency, 'sent':0, 'transactions':{}, 'timestamp': datetime.datetime.utcnow(), 'site':site }
            self.mongo[site].users.update({'address':address}, {"$addToSet": {'price.%s'%address: newcharge}})
            user['price'][address].append(newcharge)
        return user
                                                           
    # all activation feature specific to bitusenet
    def activate_bitusenet(self, trans, user, currency):
        if trans['confirmations'] == 0:
            return
        address = trans['details'][0]['address']
        site = 'bitusenet'
        price = self.mongo[site].currencies.find_one()[currency]['bitusenet']

        # adjusts billing date appropriately and starts new charge in users db to close old one
        if user['price'][address][-1]['sent'] >= user['price'][address][-1]['price']['twelvemonth']:
            billdate = user['billing'] + datetime.timedelta(days=365)
            newcharge = {'price':price, 'created':int(time.time()), 'currency':currency, 'sent':0, 'transactions':{}, 'timestamp': datetime.datetime.utcnow(), 'site':'bitusenet'}
            self.mongo[site].users.update({'address':address}, {"$set": {'billing':billdate}}, True)
            self.mongo[site].users.update({'address':address}, {"$addToSet": {'price.%s'%address: newcharge}})
            print "twelve month account activated"

        elif user['price'][address][-1]['sent'] >= user['price'][address][-1]['price']['sixmonth']:
            billdate = user['billing'] + datetime.timedelta(days=182)
            newcharge = {'price':price, 'created':int(time.time()), 'currency':currency, 'sent':0, 'transactions':{}, 'timestamp': datetime.datetime.utcnow(), 'site':'bitusenet'}
            self.mongo[site].users.update({'address':address}, {"$set": {'billing':billdate}}, True)
            self.mongo[site].users.update({'address':address}, {"$addToSet": {'price.%s'%address: newcharge}})
            print "activate six month account"

        elif user['price'][address][-1]['sent'] >= user['price'][address][-1]['price']['threemonth']:
            billdate = user['billing'] + datetime.timedelta(days=92)
            newcharge = {'price':price, 'created':int(time.time()), 'currency':currency, 'sent':0, 'transactions':{}, 'timestamp': datetime.datetime.utcnow(), 'site':'bitusenet'}
            self.mongo[site].users.update({'address':address}, {"$set": {'billing':billdate}}, True)
            self.mongo[site].users.update({'address':address}, {"$addToSet": {'price.%s'%address: newcharge}})
            print "activate three month account"

        elif user['price'][address][-1]['sent'] >= user['price'][address][-1]['price']['onemonth']:
            billdate = user['billing'] + datetime.timedelta(days=30)
            newcharge = {'price':price, 'created':int(time.time()), 'currency':currency, 'sent':0, 'transactions':{}, 'timestamp': datetime.datetime.utcnow(), 'site':'bitusenet'}
            self.mongo[site].users.update({'address':address}, {"$set": {'billing':billdate}}, True)
            self.mongo[site].users.update({'address':address}, {"$addToSet": {'price.%s'%address: newcharge}})
            print "activate one month account"
        else:
            print "not enough sent. Need to handle here", user['price'][address][-1]['sent']

    def webserver_socket_callback(self, trans):
        address = trans['details'][0]['address']
        amount = trans['details'][0]['amount']
        client = tornado.httpclient.AsyncHTTPClient()
        response = yield tornado.gen.Task(client.fetch, 'http://ec2-54-221-32-214.compute-1.amazonaws.com/transaction?address=%s&currency=max&amount=%s'%(address, amount))

                                                   
class MainHandler(BaseHandler):
    def get(self):
        text = self.maxwallet.getinfo()
        self.write(text)


class AddressHandler(BaseHandler):
    def get(self, coin):
        logging.info('Request for new address for %s'%coin)
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
        logging.info('Sending address %s'%address)
        self.write(address)
        self.finish()


class MaxTransactionHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.engine
    def get(self, txid):
        trans = maxwallet.gettransaction(txid)

        # stuff all transactions in database
        self.add_transactions(trans)

        # find user with attached address from transaction
        user = self.find_user(trans, 'bitusenet')

        # This is to see if we should recalculate for a new charge price
        user = self.calculate_newcharge(trans, user, 'max', 'bitusenet')

        # function specific to bitusenet
        self.activate_bitusenet(trans, user, 'max')

        # add transaction from the bitcoin network to the users personal transaction
        user = self.add_transactions_user(trans, user, 'bitusenet')

        # make call to bitusenet server to update websocket interface
        self.webserver_socket_callback(trans)

        self.finish()


def main():
    http_server = tornado.httpserver.HTTPServer(Application(), xheaders=True)
    http_server.listen(8000)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    tornado.options.parse_command_line()
    logging.info("Starting web server on port 8000")

    main()
