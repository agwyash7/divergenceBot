import datetime
import json
import pandas as pd
import websocket
from pymongo import MongoClient

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

websocket._logging._logger.level = -999

client = MongoClient("mongodb://yashMongo:ChachaMongo$123@198.211.110.141:2727/")
db = client["livebot"]


def get_stream_string():
    symbolsCollection = db["htfPairs"]
    result = symbolsCollection.find({})
    res = ''

    for r in result:
        res = res + f"{r['symbol'].lower()}@kline_1M/"

    res = res[:-1]
    return res


streams = get_stream_string()
SOCKET = f"wss://stream.binance.com:9443/stream?streams={streams}"

print(streams)


def on_open(ws):
    print('Connection Opened')


def on_close(ws):
    print('Connection Closed')


def on_message(ws, message):
    json_message = json.loads(message)

    candle = json_message['data']['k']
    is_candle_closed = candle['x']

    if is_candle_closed:
        symbol = candle['s']
        collection = db[f"{symbol}_1M"]

        new_candle = {"_id": candle["t"],
                      "Open_time": candle["t"],
                      "Close_time": (candle["T"] + 1),
                      "Open_time_datetime": datetime.datetime.utcfromtimestamp(candle['t'] / 1000.0).strftime(
                          "%Y-%m-%d %H:%M:%S"),
                      "Close_time_datetime": datetime.datetime.utcfromtimestamp((candle['T'] + 1) / 1000.0).strftime(
                          "%Y-%m-%d %H:%M:%S"),
                      "Open": float(candle['o']),
                      "Close": float(candle["c"]),
                      "High": float(candle["h"]),
                      "Low": float(candle["l"]),
                      "Volume": float(candle["v"])}

        print(f"Updating {symbol} with close price {str(candle['c'])}")

        collection.replace_one({"_id": new_candle["_id"]}, new_candle, upsert=True)


def on_error(ws, error):
    print(error)


ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message, on_error=on_error)
ws.run_forever()
