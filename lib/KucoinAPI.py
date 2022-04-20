#!/usr/bin/python3
import requests
import json
import time
import hashlib
import hmac
import base64

class KucoinAPI:
    def __init__(self, key, secret, passphrase):
        self.api_key = key
        self.api_secret = secret
        self.api_passphrase = passphrase
        self.kc_host = "https://api.kucoin.com"

    '''
    Public APIs
    '''
    def paramURL(self, params):
        items = params.items()
        t = ["%s=%s" % (k, v) for k, v in items]
        return "&".join(t)

    def getPublic(self, endpoint, params):
        parmurl = self.paramURL(params)
        if len(parmurl) > 0:
            parmurl = "?" + parmurl
        url = "%s%s%s" % (self.kc_host, endpoint, parmurl)
        return requests.get(url, timeout=5).json()

    # get list of trading symbols
    def getTradeSymbols(self):
        endpoint = "/api/v1/symbols"
        symbols = self.getPublic(endpoint, {})
        return symbols

    # get orderbook
    def getOrderbook(self, symbol, depth=20):
        endpoint = "/api/v1/market/orderbook/level2_%d" % depth
        param = {
            "symbol": symbol 
        }
        orderbook = self.getPublic(endpoint, param)
        return orderbook

    # get trade history
    def getTradeHistory(self, symbol):
        endpoint = "/api/v1/market/histories"
        param = {
            "symbol": symbol 
        }
        trades = self.getPublic(endpoint, param)
        return trades

    # get klines
    def getKlines(self, candleType, symbol, stime=0, etime=0):
        endpoint = "/api/v1/market/candles"
        param = {
            "type": candleType,
            "symbol": symbol,
            "startAt": stime,
            "endAt": etime
        }
        klines = self.getPublic(endpoint, param)
        return klines

    '''
    Private APIs
    '''
    def authenticate(self, endpoint, method, bodyStr=""):
        now = int(time.time() * 1000)
        str_to_sign = str(now) + method.upper() + endpoint + bodyStr
        signature = base64.b64encode(
            hmac.new(self.api_secret.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest())
        passphrase = base64.b64encode(hmac.new(self.api_secret.encode('utf-8'), \
            self.api_passphrase.encode('utf-8'), hashlib.sha256).digest())
        headers = {
            "KC-API-SIGN": signature,
            "KC-API-TIMESTAMP": str(now),
            "KC-API-KEY": self.api_key,
            "KC-API-PASSPHRASE": passphrase,
            "KC-API-KEY-VERSION": "2",
            "Content-Type": "application/json"
        }
        return headers

    def getPrivate(self, endpoint, params):
        parmurl = self.paramURL(params)
        if len(parmurl) > 0:
            parmurl = "?" + parmurl
        endpoint += parmurl
        headers = self.authenticate(endpoint, "get")
        url = "%s%s" % (self.kc_host, endpoint)
        return requests.get(url, headers=headers, timeout=5).json()

    def postPrivate(self, endpoint, body):
        bodyStr = json.dumps(body)
        headers = self.authenticate(endpoint, "post", bodyStr)
        url = "%s%s" % (self.kc_host, endpoint)
        return requests.post(url, headers=headers, data=bodyStr, timeout=5).json()

    def delPrivate(self, endpoint, params):
        parmurl = self.paramURL(params)
        if len(parmurl) > 0:
            parmurl = "?" + parmurl
        endpoint += parmurl
        headers = self.authenticate(endpoint, "delete")
        url = "%s%s" % (self.kc_host, endpoint)
        return requests.delete(url, headers=headers, timeout=5).json()

    # get account info
    def getAccountInfo(self, accountType=None):
        endpoint = "/api/v1/accounts"
        if accountType is None:
            return self.getPrivate(endpoint, {})
        else:
            return self.getPrivate(endpoint, {"type": accountType})

    # internal transfer
    def internalTransfer(self, currency, from_, to_, amount):
        endpoint = "/api/v2/accounts/inner-transfer"
        body = {
            "clientOid": str(int(time.time() * 1000)),
            "currency": currency,
            "from": from_,
            "to": to_,
            "amount": amount 
        }
        self.postPrivate(endpoint, body)

    # place order
    def placeOrder(self, side, symbol, order_type, price, size):
        endpoint = "/api/v1/orders"
        body = {
            "clientOid": str(int(time.time() * 1000)),
            "side": side,
            "symbol": symbol,
            "type": order_type,
            "price": price,
            "size": size 
        }
        ret = self.postPrivate(endpoint, body)
        orderid = ret['data']['orderId']
        return orderid

    # place stop order
    def placeStopOrder(self, side, symbol, stop_price, price, size, order_type="limit", stop_type="loss"):
        endpoint = "/api/v1/stop-order"
        body = {
            "clientOid": str(int(time.time() * 1000)),
            "side": side,
            "symbol": symbol,
            "type": order_type,
            "stop": stop_type,
            "stopPrice": stop_price,
            "price": price,
            "size": size 
        }
        ret = self.postPrivate(endpoint, body)
        orderid = ret['data']['orderId']
        return orderid

    # get order
    def getOrder(self, orderid):
        endpoint = "/api/v1/orders/%s" % orderid
        return self.getPrivate(endpoint, {})

    # cancel order
    def cancelOrder(self, orderid):
        endpoint = "/api/v1/orders/%s" % orderid 
        self.delPrivate(endpoint, {})

    # cancel all orders on a market
    def cancelAllOrders(self, symbol):
        endpoint = "/api/v1/orders"
        param = {
            "symbol": symbol 
        }
        self.delPrivate(endpoint, param)
