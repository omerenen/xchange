from telegram import *
from telegram.ext import *
from requests import *
from telegram.ext import Updater
import json
import random



updater = Updater(token="5526962804:AAF6X5LDmzH3z9sCEEWWC4YoxAq-Z2M0M-8")
dispatcher = updater.dispatcher

MARKETS = ['binance', 'mxc', 'gateio']
VALUE1 = ['10$','20$','30$','40$','50$']
PERCENTAGES = ['10', '15', '20', '25']

MIKTAR = 0
PERCENTAGE = 0
values = []


def start_trading(values, update: Update, context: CallbackContext):
    #print(f"{values[1]} borsasında  {values[2]}'lık %{values[3]}artışta emri alındı")


    with open("users.json", 'r') as f:
        data = json.loads(f.read())  # data becomes a dictionary
    test_dict = {
        "order_id": random.randint(0,1000),
        "market": values[1],
        "money": values[2][0:(len(values[2])-1)],
        "percentage_value": values[3],
        "order_complete": ""
    }
    data['members'][values[0]]['orders'].append(test_dict)

    context.bot.send_message(
        chat_id=update.effective_chat.id, text="Order completed successfully\n")

    with open("users.json", 'w') as f:
        f.write(json.dumps(data, sort_keys=True, indent=4, separators=(',', ': ')))



def startCommand(update: Update, context: CallbackContext):



    buttons = [[InlineKeyboardButton("Pump Detect", callback_data="pumpdetect")], [
        InlineKeyboardButton("Public Offering", callback_data="publicoffering")]]
    context.bot.send_message(chat_id=update.effective_chat.id, reply_markup=InlineKeyboardMarkup(
        buttons), text="What do you want to do?")
    username = update.message.chat.username
    values.append(username)


def clearList(update: Update, context: CallbackContext):
    with open("users.json", 'r') as f:
        data = json.loads(f.read())

    username = update.message.chat.username

    data['members'][username]['orders'].clear()
    with open("users.json", 'w') as f:
        f.write(json.dumps(data, sort_keys=True,
                           indent=4, separators=(',', ': ')))
    context.bot.send_message(chat_id=update.effective_chat.id, text="All orders deleted.\n")


def listOrder(update: Update, context: CallbackContext):
    with open("users.json", 'r') as f:
        data = json.loads(f.read())

    username = update.message.chat.username

    orders = data['members'][username]['orders']
    
    for i in range(0,2):
        context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"Order ID: {orders[i]['order_id']}\nMarket: {orders[i]['market']}\nMoney: {orders[i]['money']}$\nPercentage: %{orders[i]['percentage_value']}\n")
    print(len(orders),type(orders),orders[0])
    """ context.bot.send_message(
        chat_id=update.effective_chat.id, text=orders) """



def pump_detect(update: Update, context: CallbackContext):
    buttons = [[InlineKeyboardButton("Mega Signals Group", callback_data="mega_pump_group")], [
        InlineKeyboardButton("Test Group", callback_data="test_crypto_chn")]]
    context.bot.send_message(chat_id=update.effective_chat.id, reply_markup=InlineKeyboardMarkup(
        buttons), text="Which group?")
        


def market_selection(update: Update, context: CallbackContext):
    buttons = [[InlineKeyboardButton("Binance", callback_data="binance")], [
        InlineKeyboardButton("MXC", callback_data="mxc")], [
        InlineKeyboardButton("GATEIO", callback_data="gateio")]]

    context.bot.send_message(chat_id=update.effective_chat.id, reply_markup=InlineKeyboardMarkup(
        buttons), text="Market?\n")


def value_func(update: Update, context: CallbackContext):
   
    buttons = [[InlineKeyboardButton("10$", callback_data="10$")], [
        InlineKeyboardButton("20$", callback_data="20$")],
        [InlineKeyboardButton("30$", callback_data="30$")],
        [InlineKeyboardButton("40$", callback_data="40$")],
        [InlineKeyboardButton("50$", callback_data="50$")]]
        
    context.bot.send_message(chat_id=update.effective_chat.id, reply_markup=InlineKeyboardMarkup(
        buttons), text="How many?\n")



def percentage_func(update: Update, context: CallbackContext):

    buttons = [[InlineKeyboardButton("10%", callback_data="10")], [
        InlineKeyboardButton("15%", callback_data="15")],
        [InlineKeyboardButton("20%", callback_data="20")],
        [InlineKeyboardButton("25%", callback_data="25")],]

    context.bot.send_message(chat_id=update.effective_chat.id, reply_markup=InlineKeyboardMarkup(
        buttons), text="Percentage?\n")


def queryHandler(update: Update, context: CallbackContext):
    
    query = update.callback_query.data
    update.callback_query.answer()

    if query == "pumpdetect":
        dispatcher.add_handler(CallbackQueryHandler(
            pump_detect(update, context)))

    elif query == "publicoffering":
        
        dispatcher.add_handler(CallbackQueryHandler(
            public_offering(update, context)))

    elif query == "mega_pump_group":
        dispatcher.add_handler(CallbackQueryHandler(
            market_selection(update, context)))

    elif query in MARKETS:
        values.append(query)

        dispatcher.add_handler(CallbackQueryHandler(
            value_func(update, context)))

    elif query in VALUE1:

        values.append(query)

        dispatcher.add_handler(CallbackQueryHandler(
            percentage_func(update, context)))
        

    elif query in PERCENTAGES:
        values.append(query)

        print(values)

        start_trading(values, update,context)

        values.clear()






dispatcher.add_handler(CommandHandler("start", startCommand))
dispatcher.add_handler(CommandHandler("clearall", clearList))
dispatcher.add_handler(CommandHandler("list", listOrder))
#dispatcher.add_handler(CommandHandler("delete", deleteOrder))

#dispatcher.add_handler(MessageHandler(Filters.text, messageHandler))
dispatcher.add_handler(CallbackQueryHandler(queryHandler))

updater.start_polling()
