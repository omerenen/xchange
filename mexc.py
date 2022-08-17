from cgi import print_form
import hmac
from importlib.resources import path
import json
import time
from datetime import datetime
import pytz
import urllib.parse
from requests import Session
import threading
from pathlib import Path
from flask import jsonify

class MEXCCLIENT():
    def __init__(self, access_key="",  secret_key="", api_base="", **kwargs):
        self.session = Session()
        self.access_key = access_key
        self.secret_key = secret_key
        self.api_base = api_base

        self.ticker_workers = []
        self.ticker_workers_controller_thread = threading.Thread(target=self.ticker_workers_controller,daemon=True)
        self.ticker_data_pool = []
        self.all_tickers_data = []
        self.latest_worker_start_time = 0
        self.lastest_worker_id = 0
        self.to_be_ignored_worker_ids = [] 
        
        self.logs_x_sync = []
        self.logs_last_sync = []
        self.logs_ask_sync = []
        self.logs_bid_sync = []
        self.log_sync_ticker = False
        self.log_worker_ticks = False
        self.log_sync_foler_path = ""
        self.log_workers_folders_path = []

    def sign(self, to_be_sign):
        return hmac.new(self.secret_key.encode('utf-8'), to_be_sign.encode('utf-8'), 'sha256').hexdigest()

    def mexc_get(self, endpoint, payload=None, is_private=False):
        payload = dict() if payload is None else payload
        url = f'{self.api_base}{endpoint}'
        p_str = urllib.parse.urlencode(sorted(payload.items()))
        ts = int(time.time() * 1000)
        headers = {
            'Content-Type': 'application/json',
            'ApiKey': self.access_key,
            'Request-Time': str(ts)
        }
        if is_private is True:
            headers.update({'Signature': self.sign(f'{self.access_key}{ts}{p_str}')})
        url = f'{url}?{p_str}' if p_str else url
        self.session.cookies.clear()
        resp = self.session.request('GET', url, headers=headers, timeout=5)
        return resp.json()

    def mexc_post(self, endpoint, payload, is_private=False):
        url = f'{self.api_base}{endpoint}'
        data = json.dumps(payload)
        ts = int(time.time() * 1000)
        headers = {
            'Content-Type': 'application/json',
            'ApiKey': self.access_key,
            'Request-Time': str(ts)
        }
        if is_private is True:
            headers.update({'Signature': self.sign(f'{self.access_key}{ts}{data}')})
        self.session.cookies.clear()
        resp = self.session.request('POST', url, data=data, headers=headers, timeout=5)
        return resp.json()

    def get_system_time(self):
        return self.mexc_get(endpoint="/open/api/v2/common/timestamp")

    def get_ticker(self,symbol):
        symbol = "{}{}".format(symbol,"_USDT")
        payload = {"symbol":symbol}
        return self.mexc_get("/open/api/v2/market/ticker",payload=payload)

    def get_all_tickers(self):
        return self.mexc_get("/open/api/v2/market/ticker")
    
    def start_ticker_workers(self,worker_count):
        self.ticker_data_pool = []
        start_time = datetime.now(tz=pytz.UTC)
        self.ticker_workers = [GetTickerWorker(self,i,10) for i in range(worker_count)]
        self.ticker_workers_controller_thread.start()
    
    def ticker_workers_controller(self):
        t0 = time.time()
        while True:
            aveliable_workers = []
            for worker in self.ticker_workers:
                if worker.isWorking == False:
                    aveliable_workers.append(worker)

            for aveliable_worker in aveliable_workers:
                if time.time()  > self.latest_worker_start_time + 1/13:
                    t1 = time.time()
                    hz = 1/(t1-t0)
                    t0 = t1
                    
                    self.latest_worker_start_time = time.time()
                    follower_worker = self.find_worker_with_id(self.lastest_worker_id)
                    follower_worker.follower_id = aveliable_worker.id
                    aveliable_worker.pioneer_id = self.lastest_worker_id
                    self.lastest_worker_id = aveliable_worker.id
                    aveliable_worker.work()              
                    continue  

    def sell(self,symbol,quantity):        
        sym = symbol
        ticker_data = self.get_ticker_with_symbol(symbol)
        last_max_bid = float(ticker_data['bid'])

        offer_ask = last_max_bid * 0.999
        ask_quantity = quantity

        ret = {
            "last_max_bid" : last_max_bid,
            "offer_ask" : offer_ask,
            "ask_quantity" : ask_quantity
        }

        payload = {
            "symbol" : "{}_USDT".format(sym),
            "price" : str(offer_ask),
            "quantity" : str(quantity),
            "trade_type" : "ASK",
            "order_type" : "IMMEDIATE_OR_CANCEL"
        }
        order_stat = []
        time_start = time.time()
        order_stat = self.mexc_post('/open/api/v2/order/place',payload,True)
        ret.update({"delta" : time.time() - time_start})
        ret.update(order_stat)
        time.sleep(1/17)
        self.buysell_pause = False
        return ret

    def buy(self,symbol,found):
        sym = symbol
        ticker_data = self.get_ticker_with_symbol(symbol)
        last_min_ask = float(ticker_data['ask'])

        offer_bid = last_min_ask * 1.001
        bid_quantity = found/offer_bid

        ret = {
            "last_min_ask" : last_min_ask,
            "offer_bid" : offer_bid,
            "bid_quantity" : bid_quantity
        }

        payload = {
            "symbol" : "{}_USDT".format(sym),
            "price" : str(offer_bid),
            "quantity" : str(bid_quantity),
            "trade_type" : "BID",
            "order_type" : "IMMEDIATE_OR_CANCEL"
        }
        order_stat = []
        time_start = time.time()
        order_stat = self.mexc_post('/open/api/v2/order/place',payload,True)
        ret.update({"delta" : time.time() - time_start,})
        ret.update(order_stat)
        time.sleep(1/17)
        return ret
    
    def get_order(self,order_id):
        endpoint = '/open/api/v2/order/deal_detail'
        payload = {
            "order_id" : str(order_id)
        }
        return self.mexc_get(endpoint,payload,is_private=True)

    def find_worker_with_id(self,id):
        for worker in self.ticker_workers:
            if worker.id == id:
                return worker

    def get_ticker_with_symbol(self,symbol):
        for i in range(0,len(self.all_tickers_data[-1]['data'])):
            if self.all_tickers_data[-1]['data'][i]['symbol'] == f"{symbol}_USDT":
                return self.all_tickers_data[-1]['data'][i]

    def buy_sell_imidiate(self,symbol,found,sleep = 0.0):
        t0 = time.time()
        buy_resp = self.buy(symbol,found)
        time.sleep(sleep)
        sell_resp = self.sell(symbol,float(buy_resp["bid_quantity"]))
        resp = {"buy_resp":buy_resp,"sell_resp":sell_resp,"delta":time.time()-t0}
        return resp

    def buy_sell_persent(self,symbol,found,persentage = 1.0,timeout=30):
        t0 = time.time()
        buy_resp = self.buy(symbol,found)
        print(buy_resp)
        buy_price = buy_resp['offer_bid']
        target_sell_price = buy_price * persentage
        t1=time.time()
        while time.time() - t1 < timeout:
            ticker_data = self.get_ticker_with_symbol(symbol)
            last_max_bid = float(ticker_data['bid'])
            if last_max_bid * 0.999 > target_sell_price:
                sell_resp = self.sell(symbol,float(buy_resp["bid_quantity"]))
                print(sell_resp)
                resp = {"buy_resp":buy_resp,"sell_resp":sell_resp,"delta":time.time()-t0,"timeout":"false"}

                return resp
        sell_resp = self.sell(symbol,float(buy_resp["bid_quantity"]))
        print(sell_resp)
        resp = {"buy_resp":buy_resp,"sell_resp":sell_resp,"delta":time.time()-t0,"timeout":"yes"}
        
        
    
    def __del__(self):
        if self.session:
            self.session.close()


class GetTickerWorker():
    def __init__(self,mexc,id,worker_count):
        self.id = id
        self.follower_id = 0
        self.pioneer_id = 0
        self.isWorking = False
        self.mexc = mexc
        self.worker_count = worker_count
        self.tickers_data = []

    def getTicker(self):
        self.isWorking = True
        timer_start = time.time()
        self.tickers_data = self.mexc.get_all_tickers()
        timer_end = time.time()
        self.tickers_data.update({"self_time":timer_end})            
        self.syncData()
        self.isWorking = False      
    
    def work(self):
        if self.isWorking == False:
            self.isWorking = True
            thread = threading.Thread(target=self.getTicker,daemon=True).start()

    def syncData(self):
        if len(self.mexc.all_tickers_data) <= 0:
                self.mexc.all_tickers_data.append(self.tickers_data)
                return
        for to_be_ignored_worker_id in self.mexc.to_be_ignored_worker_ids:
            if to_be_ignored_worker_id == self.id:
                self.mexc.to_be_ignored_worker_ids.remove(to_be_ignored_worker_id)
                return

        change_detected = False
        change_id = 99999
        for i in range(0,len(self.tickers_data['data'])):
            last_i = self.mexc.all_tickers_data[-1]['data'][i]
            to_check = self.tickers_data['data'][i]

            if self.tickers_data['data'][i]["ask"] != self.mexc.all_tickers_data[-1]['data'][i]['ask']:
                change_detected = True
                change_id = i
                break
            if self.tickers_data['data'][i]["bid"] != self.mexc.all_tickers_data[-1]['data'][i]['bid']: 
                change_detected = True
                change_id=i
                break
        if change_detected == False:
            return

        self.mexc.to_be_ignored_worker_ids = []
        self.mexc.to_be_ignored_worker_ids.append(self.follower_id)
        worker_to_check = self.pioneer_id
        for i in range(len(self.mexc.ticker_workers)):                
            if self.find_worker_with_id(worker_to_check).isWorking == True:
                self.mexc.to_be_ignored_worker_ids.append(worker_to_check)
                worker_to_check = self.find_worker_with_id(worker_to_check).pioneer_id
            else:
                break

        self.mexc.all_tickers_data.append(self.tickers_data)
        if len(self.mexc.all_tickers_data) >= 100:
            self.mexc.all_tickers_data.pop(len(self.mexc.all_tickers_data)-1)

    def find_worker_with_id(self,id):
        for worker in self.mexc.ticker_workers:
            if worker.id == id:
                return worker

def log_data(path,data):
    with open(path, 'a') as f:
        log_y = str(data)
        line = "{}\n".format(log_y)
        f.write(line)


access_key = "mx0wV7gCa1pIVFw8yv"
secret_key = "ca93136ba13444a2b58e4f6bf5065c51"

baseURL = "https://www.mexc.com"
mexc = MEXCCLIENT(access_key=access_key,
                  secret_key=secret_key, api_base=baseURL)

mexc.start_ticker_workers(15)
time.sleep(5)
resp = mexc.buy_sell_persent("BTC",15,1.15,5)
print(resp)
        