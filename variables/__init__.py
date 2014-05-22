import pymongo
from jsonrpc import ServiceProxy


mongoconn = pymongo.Connection('ec2-50-17-28-132.compute-1.amazonaws.com', 27017)
mongo = {'bitusenet':mongoconn.maxusenet, 'transactions':mongoconn.transactions}

maxwallet = ServiceProxy("http://maxcoinrpc:GcbiFLHeeG8kgR6NSKzzUGHvejum9NPkR8sKHY2HWJVp@127.0.0.1:8334")
btcwallet = ServiceProxy("http://bitcoinrpc:GcbiFLHeeG8kgR6NSKzzUGHvejum9NPkR8sKHY2HWJVp@127.0.0.1:8332")
ltcwallet = ServiceProxy("http://litecoinrpc:GcbiFLHeeG8kgR6NSKzzUGHvejum9NPkR8sKHY2HWJVp@127.0.0.1:8336")
dogewallet = ServiceProxy("http://dogerpc:GcbiFLHeeG8kgR6NSKzzUGHvejum9NPkR8sKHY2HWJVp@127.0.0.1:8339")
