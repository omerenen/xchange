from os import sync
import time
from tkinter.tix import Tree
from binance.websocket.spot.websocket_client import SpotWebsocketClient as WebsocketClient
from binance.spot import Spot as SpotClient
from cgi import print_form
import hmac
from importlib.resources import path
import json
from datetime import datetime
import urllib.parse
from requests import Session
import threading
from pathlib import Path
from flask import jsonify

class BinanceClient():
    def __init__(self, access_key="",  secret_key="", **kwargs):
        self.access_key = access_key
        self.secret_key = secret_key
        self.API_base_url = "https://fapi.binance.com"
        self.websocket_client = WebsocketClient(stream_url="wss://stream.binance.com:9443")
        self.websocket_client.start()
        self.spot_client = SpotClient(access_key,secret_key)
        self.ticker_data_pool = []
        self.trade_data_pool = []
        self.session = Session()
        self.all_tickers_data = {}
        self.all_symbols_info = {}
        self.get_symbols_info()

    
    def subscribe_to_all_tickers(self):
        with open('stream_log.txt', 'w') as f:
            f.write("")

        symbols_list = self.create_symbols_list()
        subscription_list = []
        for symbol in symbols_list:
            self.all_tickers_data[str(symbol).upper()] = []
            subscription_list.append(f"{str(symbol).lower()}@bookTicker")
            subscription_list.append(f"{str(symbol).lower()}@aggTrade")
        self.websocket_client.instant_subscribe(subscription_list, callback=self.ticker_listener)

    def get_exchange_info(self):
        base_url = 'https://api.binance.com'
        endpoint = '/api/v3/exchangeInfo'
        self.session.cookies.clear()
        return self.session.get(url = base_url + endpoint).json()

    def create_symbols_list(self,filter='USDT'):
        rows = []
        info = self.get_exchange_info()
        pairs_data = info['symbols']
        full_data_dic = {s['symbol']: s for s in pairs_data if filter in s['symbol']}
        return full_data_dic.keys()
        
    def ticker_listener(self,message): 
        """ with open('stream_log.txt', 'a') as f:
            f.write(f"{message}\n***********************************************\n") """

        if str(message).find("@bookTicker") != -1:
            symbol = message['data']['s']
            data = message['data']
            self.all_tickers_data[symbol].append(data)

    def get_all_coins_info(self):
        return self.spot_client.coin_info()

    def get_ticker_data(self,symbol):
        search_str = f"{str(symbol).upper()}USDT"
        ret_data = self.all_tickers_data[search_str][-1]
        return ret_data

    def get_account_info(self):
        return self.spot_client.account()

    def buy(self,symbol,found,test=True):
        last_ticker = self.get_ticker_data(symbol=symbol)
        symbol = "{}USDT".format(symbol)        
        last_min_ask = float(last_ticker['a'])
        offer_bid = last_min_ask
        bid_quantity = found/offer_bid

        bid_quantity = self.adjust_decimals(symbol,bid_quantity)
        params = {
            "symbol": symbol,
            "side": "BUY",
            "type": "MARKET",
            "quantity": bid_quantity,
        }
        if test:
            resp = self.spot_client.new_order_test(**params)
        else:
            resp = self.spot_client.new_order(**params)
        resp.update({"bid_quantity" : bid_quantity})
        return resp

    def sell(self,symbol,quantity,test=True):
        last_ticker = self.get_ticker_data(symbol=symbol)
        symbol = "{}USDT".format(symbol)        
        ask_quantity = quantity
        ask_quantity = self.adjust_decimals(symbol,ask_quantity)
        params = {
            "symbol": symbol,
            "side": "SELL",
            "type": "MARKET",
            "quantity": ask_quantity,
        }
        if test:
            resp = self.spot_client.new_order_test(**params)
        else:
            resp = self.spot_client.new_order(**params)
        return resp

    def get_symbols_info(self):
        symbols_info = self.session.get(url="https://www.binance.com/api/v1/exchangeInfo").json()
        for i in range(0,len(symbols_info['symbols'])):
            self.all_symbols_info[symbols_info['symbols'][i]['symbol']] = symbols_info['symbols'][i]
        return symbols_info

    def adjust_decimals(self,symbol,decimal):
        quote_pre = int(self.all_symbols_info[symbol]['quotePrecision'])
        
        step_size = float(self.all_symbols_info[symbol]['filters'][2]['stepSize'])
        adjusted_decimal = 0
        while True:
            if adjusted_decimal + step_size < decimal:
                adjusted_decimal += step_size
            else:
                break
        
        adjusted_decimal = float(round(adjusted_decimal,quote_pre))   
        return adjusted_decimal

    def buy_sell_imidiate(self,symbol,found,sleep = 0.0,test = True):
        t0 = time.time()
        buy_resp = self.buy(symbol,found,test)
        time.sleep(sleep)
        sell_resp = self.sell(symbol,float(buy_resp["bid_quantity"]),test)
        resp = {"buy_resp":buy_resp,"sell_resp":sell_resp,"delta":time.time()-t0}
        return resp

       
    def __del__(self):
        self.websocket_client.stop()


""" binance_client = BinanceClient("WnfOo7T7IFzJFMtH7Ku19wLB1YKU29JU6ZgQ94SJppz1yslpPBReHfffnxt5jGOi","DgayaNCns9oB2gzD7Jmo61L6doWZFIcNuKwo1aglfvyAkzRwr4AsyQJxmmFe7xZp")
binance_client.subscribe_to_all_tickers()
time.sleep(3)



while True:
    input("buysell:")
    resp = binance_client.buy_sell_imidiate("ETH",25,0,True)
    print(resp)
    time.sleep(0.1) """