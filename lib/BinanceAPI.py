#!/usr/bin/python3
import requests
import json
import time
import hashlib
import hmac
import base64
from collections import OrderedDict
from urllib.parse import urlencode

class BinanceAPI:
    def __init__(self, key, secret):
        self.api_key = key
        self.api_secret = secret
        self.host = "https://api.binance.com/api/v3"

    '''
    Public APIs
    '''
    def getPublic(self, endpoint, params=OrderedDict()):
        query = urlencode(params)
        url = "%s%s?%s" % (self.host, endpoint, query)
        return requests.get(url, timeout=5).json()

    # get list of tickers
    def getTicker(self):
        endpoint = "/ticker/24hr"
        return self.getPublic(endpoint)

    # get exchange info
    def getExchangeInfo(self):
        endpoint = "/exchangeInfo"
        return self.getPublic(endpoint)

    # get orderbook
    def getOrderbook(self, symbol, depth=20):
        endpoint = "/depth"
        param = OrderedDict({
            "symbol": symbol,
            "limit": depth
        })
        orderbook = self.getPublic(endpoint, param)
        return orderbook

    # get klines
    def getKlines(self, symbol, interval, stime=None, etime=None, limit=50):
        endpoint = "/klines"
        if stime is None or etime is None:
            param = OrderedDict({
                "symbol": symbol,
                "interval": interval,
                "limit": limit
            })
        else:
            param = OrderedDict({
                "symbol": symbol,
                "interval": interval,
                "startTime": stime,
                "endTime": etime,
                "limit": limit
            })
        klines = self.getPublic(endpoint, param)
        return klines

    '''
    Private APIs
    '''
    def signParam(self, params=OrderedDict()):
        data = params.copy()
        ts = str(int(1000 * time.time()))
        data.update({"timestamp": ts})
        h = hmac.new(str(self.api_secret).encode(), \
                str(urlencode(data)).encode(), \
                hashlib.sha256)
        signature = h.hexdigest()
        data.update({"signature": signature})
        return data

    def authenticate(self, endpoint, param=OrderedDict()):
        params.update({"recvWindow": 50000})
        query = urlencode(self.signParam(params))
        url = "%s%s?%s" % (self.host, endpoint, query)
        header = {"X-MBX-APIKEY": self.api_key}
        return header, url

    def getPrivate(self, endpoint, params):
        headers, url = self.authenticate(endpoint, params)
        return requests.get(url, headers=headers, timeout=5).json()

    def postPrivate(self, endpoint, body):
        headers, url = self.authenticate(endpoint, params)
        return requests.post(url, headers=headers, timeout=5).json()

    def delPrivate(self, endpoint, params):
        headers, url = self.authenticate(endpoint, params)
        return requests.delete(url, headers=headers, timeout=5).json()

    # get account info
    def getAccountInfo(self):
        endpoint = "/account"
        return self.getPrivate(endpoint, OrderedDict())

    # place order
    def placeOrder(self, side, symbol, order_type, price, size):
        endpoint = "/order"
        quantity = self._str(quantity)
        rate = self._str(rate)
        params = OrderedDict()
        params.update({"symbol": symbol, "side": side, \
            "type": order_type, "timeInForce": "GTC", \
            "quantity": quantity, "price": rate})
        return self.postPrivate(endpoint, params)

    # get order
    def getOrder(self, symbol, orderid):
        endpoint = "/order"
        params = OrderedDict()
        params.update({"symbol": symbol, "orderId": orderId})
        return self.getPrivate(endpoint, params)

    # cancel order
    def cancelOrder(self, symbol, orderid):
        endpoint = "/order"
        params = OrderedDict()
        params.update({"symbol": symbol, "orderId": orderid})
        self.delPrivate(endpoint, params)

    # cancel all orders on a market
    def cancelAllOrders(self, symbol):
        endpoint = "/openOrders"
        params = OrderedDict()
        params.update({"symbol": symbol})
        self.delPrivate(endpoint, params)
