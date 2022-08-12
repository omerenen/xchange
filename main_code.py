import re
import json
from telethon import TelegramClient, events, sync
from time import sleep
import datetime
from threading import Thread
from mexc import MEXCCLIENT
import time
#-------------------------------
# DEFINITIONS
#-------------------------------


access_key = "mx0UnHXPg1SSmAl5Aq"
secret_key = "a100ee1055fa46bbba879fad92ea7c79"

baseURL = "https://www.mexc.com"
mexc = MEXCCLIENT(access_key=access_key,
                  secret_key=secret_key, api_base=baseURL)

mexc.log_sync_ticker = True
mexc.log_worker_ticks = True

# 10.99291214

mexc.start_ticker_workers(15)

api_id = 18960937
api_hash = "3501490d2f8009f8c3de0d2dc322b80c"
coins = []
target_coin = ""


#-------------------------------


#-------------------------------
# MARKET COIN FETCHS
#-------------------------------


def coin_for_mxc():
    f = open('mxc_coins.json')
  
    data = json.load(f)
    
    coin_array = []
    for i in data['data']:
        temp = i['symbol'].split("_")[0]
        coin_array.append(temp)
    f.close()
    return coin_array



#-------------------------------

#-------------------------------
# MARKET SELECTION
#-------------------------------
coins = coin_for_mxc()


# COIN SELECTION
#-------------------------------

client = TelegramClient('session_name', api_id, api_hash)


channel_username = 'test_crypto_chn'# your channel
client.start()


splitted_message = []

def target_finder(splitted_message):
    target_coin = ""
    

    for it in splitted_message:
        if(it in coins):
            target_coin = it
            break
    if(target_coin !=""):
        print(target_coin)
        resp = mexc.buy_sell_imidiate(symbol=target_coin,found=15,sleep=0) #omer bunu kullan daha sexy
        print(resp)



@client.on(events.NewMessage())
async def newMessageListener(event):
    newMessage = event.message.message
    newMessage = newMessage.replace("$","")
    newMessage = newMessage.replace("#", "")
    newMessage = newMessage.replace("/", " ")

    #print(newMessage)
    splitted_message = newMessage.split()
    target_finder(splitted_message)

with client:
    client.run_until_disconnected()

