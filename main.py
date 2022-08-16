import datetime
import json
from pprint import pprint

import requests
import websocket

websocket._logging._logger.level = -999

from bot import TradingBot

TRINITY_APIKEY = "rN58tKBfaXISf8wXzScVxHe2wSu7jxIw45kjLX7bSSiEFlf0DYk0yPa3puqL4LOF"
TRINITY_SECRETKEY = "rmJwaoxzMQY7naQfAUQSDV4sKgb3uXTdIjZBvAjVEUxafhwuTQgsEJBh8PNCxNuz"

api_key = TRINITY_APIKEY
api_secret = TRINITY_SECRETKEY

# symbol = "blzbtc"
# localID = "61d0aac8eaf5c4ea877d956f"

# symbol = "icxbtc"
# localID = "61d0aacaeaf5c4ea877d9575"

# symbol = "ardrbtc"
# localID = "61d0aac7eaf5c4ea877d956e"

# symbol = "oceanbtc"
# localID = "61d0aacceaf5c4ea877d957b"

symbol = "fttbtc"
localID = "61d2ce2a872bb9eea23506c1"

SOCKET = f"wss://stream.binance.com:9443/stream?streams={symbol}@kline_5m/{symbol}@kline_15m"

lreq = requests.get(f"http://127.0.0.1:5000/pair/{localID}", auth=("YashSecretUsername", "YashSecretPasswordOcean123"))
lParams = (lreq.json())["result"]

greq = requests.get("http://127.0.0.1:5000/globalSetting/61b3b04c4f714554508bc849", auth=("YashSecretUsername", "YashSecretPasswordOcean123"))
gParams = (greq.json())["result"]

# print(lParams)
# print(gParams)

bot = TradingBot(api_key, api_secret, localID, "data/", gParams, lParams)


def on_open(ws):
    # bot.preloadLTFData()
    # bot.preloadSwingData()
    # bot.preloadDTFData()
    bot.test()
    print('Connection Opened')


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

    # pprint(json_message)
    # pprint(float(close))

    if bot.checkEntryOrderPrice and not is_candle_closed:
        bot.placeMarketEntryOrder(float(close))

    if bot.checkStoplossOrderPrice and not is_candle_closed:
        bot.placeStoplossMarketEntryOrder(float(close))

    if is_candle_closed:
        utcTime = datetime.datetime.utcnow()
        streamName = json_message["stream"].replace(f"{symbol}@kline_", "")

        if streamName == lParams["ltfTimeFrame"]:
            bot.addCandle(utcTime, openPrice, high, low, close)
            # bot.run()

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
