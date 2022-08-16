import datetime
import json
import multiprocessing
import os
import threading
from pathlib import Path
from pprint import pprint

import requests
import websocket
from flask import Flask, jsonify, request, abort
from flask_basicauth import BasicAuth
from flask_mongoengine import MongoEngine

from models.pairs import Pairs

websocket._logging._logger.level = -999

from bot import TradingBot

TRINITY_APIKEY = "rN58tKBfaXISf8wXzScVxHe2wSu7jxIw45kjLX7bSSiEFlf0DYk0yPa3puqL4LOF"
TRINITY_SECRETKEY = "rmJwaoxzMQY7naQfAUQSDV4sKgb3uXTdIjZBvAjVEUxafhwuTQgsEJBh8PNCxNuz"

api_key = TRINITY_APIKEY
api_secret = TRINITY_SECRETKEY

greq = requests.get("http://127.0.0.1:5000/globalSetting/61b3b04c4f714554508bc849", auth=("YashSecretUsername", "YashSecretPasswordOcean123"))
gParams = (greq.json())["result"]


def newBotInstances(symbol, pair_id):
    lreq = requests.get(f"http://127.0.0.1:5000/pair/{pair_id}", auth=("YashSecretUsername", "YashSecretPasswordOcean123"))
    lParams = (lreq.json())["result"]

    bot = TradingBot(api_key, api_secret, pair_id, "/home/yash/livebot/data/", gParams, lParams)

    SOCKET = f"wss://stream.binance.com:9443/stream?streams={symbol}@kline_5m" \
             f"/{symbol}@kline_15m" \
             f"/{symbol}@kline_30m" \
             f"/{symbol}@kline_1h" \
             f"/{symbol}@kline_2h" \
             f"/{symbol}@kline_4h" \
             f"/{symbol}@kline_8h" \
             f"/{symbol}@kline_12h" \
             f"/{symbol}@kline_1d"

    def on_open(ws):
        bot.preloadLTFData()
        bot.preloadDTFData()
        bot.preloadSwingData()
        print(f'Connection Opened  -: {symbol}')

    def on_close(ws):
        print('Connection Closed')

    def on_message(ws, message):
        json_message = json.loads(message)

        candle = json_message['data']['k']
        is_candle_closed = candle['x']

        openPrice = candle['o']
        high = candle['h']
        low = candle['l']
        close = candle['c']

        if bot.checkEntryOrderPrice and not is_candle_closed:
            bot.placeMarketEntryOrder(float(close))

        if bot.checkStoplossOrderPrice:
            if bot.slPlaceOrder == "Touch" and not is_candle_closed:
                    bot.placeStoplossMarketEntryOrder(float(close))

            if bot.slPlaceOrder == "Close" and is_candle_closed:
                streamName = json_message["stream"].replace(f"{symbol}@kline_", "")

                if streamName == bot.slTimeframe:
                    bot.placeStoplossMarketEntryOrder(float(close))

        if is_candle_closed:
            utcTime = datetime.datetime.utcnow()
            streamName = json_message["stream"].replace(f"{symbol}@kline_", "")

            if streamName == lParams["ltfTimeFrame"]:
                bot.addCandle(utcTime, openPrice, high, low, close)
                bot.run()

            if streamName == lParams["dtf1Timeframe"]:
                bot.addDTF1Candle(utcTime, openPrice, high, low, close)

            if streamName == lParams["dtf2Timeframe"]:
                bot.addDTF2Candle(utcTime, openPrice, high, low, close)

            if streamName == lParams["dtf3Timeframe"]:
                bot.addDTF3Candle(utcTime, openPrice, high, low, close)

            if streamName == lParams["dtf4Timeframe"]:
                bot.addDTF4Candle(utcTime, openPrice, high, low, close)

            if streamName == lParams["dtf5Timeframe"]:
                bot.addDTF5Candle(utcTime, openPrice, high, low, close)

            if streamName == lParams["dtf6Timeframe"]:
                bot.addDTF6Candle(utcTime, openPrice, high, low, close)

            if streamName == lParams["dtf7Timeframe"]:
                bot.addDTF7Candle(utcTime, openPrice, high, low, close)

            if streamName == lParams["dtf8Timeframe"]:
                bot.addDTF8Candle(utcTime, openPrice, high, low, close)

    def on_error(ws, error):
        print(error)

    ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message, on_error=on_error)
    ws.run_forever()


default_config = {
    'MONGODB_SETTINGS': {
        'db': 'livebot',
        'host': '198.211.110.141',
        'port': 2727,
        'username': 'yashLiveBot',
        'password': 'MongoChachaLiveBot$123'
    }
}

threads = {}

app = Flask(__name__)
app.config.update(default_config)

app.config['BASIC_AUTH_USERNAME'] = 'YashSecretUsername'
app.config['BASIC_AUTH_PASSWORD'] = 'YashSecretPasswordOcean123'
app.config['BASIC_AUTH_FORCE'] = True

basic_auth = BasicAuth(app)


@app.before_request
def limit_remote_addr():
    trusted_ip = ('198.211.110.141', '103.42.89.204', '127.0.0.1')
    remote = request.remote_addr

    if remote not in trusted_ip:
        abort(403)


db = MongoEngine(app=app)


@app.route("/pair/<pair_id>/start", methods=['POST'])
def startNewBot(pair_id):
    global threads

    data = request.json

    thread = multiprocessing.Process(target=newBotInstances, args=(data["symbol"], pair_id))
    threads[pair_id] = thread
    thread.start()

    pair = Pairs.objects.get(id=pair_id)
    pair.isActive = True
    pair.save()

    return jsonify({'result': "Successfully Started"})


@app.route("/pair/<pair_id>/stop", methods=['POST'])
def stopNewBot(pair_id):
    global threads

    threads[pair_id].terminate()

    del threads[pair_id]

    pair = Pairs.objects.get(id=pair_id)
    pair.isActive = False
    pair.save()

    return jsonify({'result': "Successfully Stopped"})


if __name__ == '__main__':
    app.run(port=7777, host="0.0.0.0")
