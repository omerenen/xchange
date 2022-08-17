from sre_parse import GLOBAL_FLAGS
from flask import Flask, jsonify, request
from flask_restful import Api, Resource, reqparse
import json
import pandas as pd
import requests
import time
import hmac
import hashlib
import urllib.parse
from mexc import MEXCCLIENT
from binance_api import BinanceClient
import matplotlib.pyplot as plt
import numpy as np


#mexc = MEXCCLIENT(access_key="mx0UnHXPg1SSmAl5Aq",secret_key="a100ee1055fa46bbba879fad92ea7c79", api_base="https://www.mexc.com")
#mexc.start_ticker_workers(15)

working_parity = "BTC"
binance_cli = BinanceClient(access_key="WnfOo7T7IFzJFMtH7Ku19wLB1YKU29JU6ZgQ94SJppz1yslpPBReHfffnxt5jGOi",secret_key="DgayaNCns9oB2gzD7Jmo61L6doWZFIcNuKwo1aglfvyAkzRwr4AsyQJxmmFe7xZp",parity=working_parity)
binance_cli.subscribe_to_all_tickers()
time.sleep(3)

app = Flask(__name__)

@app.route("/wallet")
def wallet():
    resp = binance_cli.get_account_info()

    balances = resp['balances']
    countables = []
    for coin in balances:
        if float(coin['free']) > 0.00001:
            symbol = coin['asset']
            quantity_free = float(coin['free'])
            dict_form = {
                "symbol" : symbol,
                "info" : {
                    "quantity" : quantity_free,
                    "price" : {'ask' : binance_cli.get_ticker_data(symbol)['a'], 'bid' : binance_cli.get_ticker_data(symbol)['b'] }
                }
            }
            countables.append(dict_form)
    countables.append({"parity":working_parity})
    return jsonify(countables)

@app.route('/get_price')
def get_price():
    args=request.args
    resp = ""
    parity = args.get('parity')
    symbol = args.get('symbol')
    btc_price = binance_cli.get_ticker_data(symbol=symbol,parity=parity)
    return jsonify(btc_price)


@app.route('/buy')
def buy():
    args=request.args
    resp = ""
    symbol = args.get('symbol')
    quantity = float(args.get('quantity'))
    resp = {"parity":working_parity,"symbol":symbol,"quantity":quantity}

    buy_sell_resp = binance_cli.buy(symbol,quantity,False)
    resp.update(buy_sell_resp)
    return jsonify(resp)

@app.route('/sell')
def sell():
    args=request.args
    resp = ""
    symbol = args.get('symbol')
    quantity = float(args.get('quantity'))
    resp = {"parity":working_parity,"symbol":symbol,"quantity":quantity}

    sell_resp = binance_cli.sell(symbol,quantity,-1,False)
    resp.update(sell_resp)
    return jsonify(resp)

@app.route('/buy_sell_imidate')
def buy_sell_imidate():
    args=request.args
    resp = ""
    parity = args.get('parity')
    symbol = args.get('symbol')
    quantity = float(args.get('quantity'))
    resp = {"parity":parity,"symbol":symbol,"quantity":quantity}

    buy_sell_resp = binance_cli.buy_sell_imidiate(symbol,quantity,parity,1,False)
    resp.update(buy_sell_resp)
    return jsonify(resp)

@app.route('/persent')
def present():
    args=request.args
    resp = ""
    parity = args.get('parity')
    symbol = args.get('symbol')
    quantity = float(args.get('quantity'))
    persent = float(args.get('persent'))
    resp = {"parity":parity,"symbol":symbol,"quantity":quantity,"persent":persent}

    buy_sell_resp = binance_cli.buy_sell_presentage(symbol,quantity,parity,persent,30,False)
    resp.update(buy_sell_resp)
    return jsonify(resp)

app.run()
# endregion


