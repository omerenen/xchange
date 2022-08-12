import re
import json
from telethon import TelegramClient, events, sync
from time import sleep
import datetime
import threading
import asyncio

#-------------------------------
# DEFINITIONS
#-------------------------------

api_id = 18960937
api_hash = "3501490d2f8009f8c3de0d2dc322b80c"
coins = []
target_coin = ""


from telethon import TelegramClient, events

client = TelegramClient("name", api_id, api_hash)

@client.on(events.NewMessage())
async def newMessageListener(event):
    newMessage = event.message.message
    print(newMessage)

with client:
    client.run_until_disconnected()