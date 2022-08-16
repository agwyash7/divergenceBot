import datetime
import json
import numpy as np
import pandas as pd
import requests
from pymongo import MongoClient

import websocket

websocket._logging._logger.level = -999

TRINITY_APIKEY = "rN58tKBfaXISf8wXzScVxHe2wSu7jxIw45kjLX7bSSiEFlf0DYk0yPa3puqL4LOF"
TRINITY_SECRETKEY = "rmJwaoxzMQY7naQfAUQSDV4sKgb3uXTdIjZBvAjVEUxafhwuTQgsEJBh8PNCxNuz"

api_key = TRINITY_APIKEY
api_secret = TRINITY_SECRETKEY

symbol = "btcusdt"
timeframe = "5m"

SOCKET = f"wss://stream.binance.com:9443/ws/{symbol}@kline_{timeframe}"
closes = []

RSI_PERIOD = 5
RSI_OVERBOUGHT = 85
RSI_OVERSOLD = 15

dbclient = MongoClient("mongodb://yashMongo:ChachaMongo$123@198.211.110.141:2727/")
db = dbclient["livebot"]

COOLDOWN_LOGS_URL = "https://discord.com/api/webhooks/898326514276368384/HeK0W_z1GDtYU1DCR8jEfVOCQ-59ux2g9C-iBJi-kk6N_95osnLL3Bmr0jKzqCxfXwZw"

disableStartbarTrades = True
disablePostCloseDivEntryTrades = False
disablePostCloseReEntryTrades = False


def rsi_tradingview(src, period=5, round_rsi=False):
    delta = src.diff()

    up = delta.copy()
    up[up < 0] = 0
    up = pd.Series.ewm(up, alpha=1 / period).mean()

    down = delta.copy()
    down[down > 0] = 0
    down *= -1
    down = pd.Series.ewm(down, alpha=1 / period).mean()

    rsi = np.where(up == 0, 0, np.where(down == 0, 100, 100 - (100 / (1 + up / down))))

    return np.round(rsi, 2) if round_rsi else rsi


def runStream():
    try:
        def on_open(ws):
            print('Connection Opened')

        def on_close(ws):
            print('Connection Closed')

        def on_message(ws, message):
            json_message = json.loads(message)

            candle = json_message['k']
            is_candle_closed = candle['x']

            high = candle['h']
            low = candle['l']
            close = candle['c']

            if is_candle_closed:
                hcl3 = (float(high) + float(low) + float(close)) / 3

                closes.append(float(close))
                # print(closes)

                if len(closes) > RSI_PERIOD:
                    my_closes = pd.Series(closes)
                    # rsi = RSIIndicator(my_closes, window=RSI_PERIOD)
                    timeNow = datetime.datetime.utcnow()
                    rsi_cal = rsi_tradingview(my_closes, period=5)
                    rsi_cal = rsi_cal.tolist()
                    last_rsi = rsi_cal[-1]
                    print(f"{timeNow} Current rsi is {last_rsi}")

                    if last_rsi > RSI_OVERBOUGHT or last_rsi < RSI_OVERSOLD:
                        disableTradeCol = db["disableTrades"]
                        colfilter = {
                            'settingName': "disabledTrades",
                        }

                        if disableStartbarTrades:
                            newvalues = {"$set":
                                {
                                    'startBar-Disable': True,
                                }
                            }

                            disableTradeCol.update_one(colfilter, newvalues)

                        if disablePostCloseDivEntryTrades:
                            newvalues = {"$set":
                                {
                                    'postCloseDivEntry-Disable': True,
                                }
                            }

                            disableTradeCol.update_one(colfilter, newvalues)

                        if disablePostCloseReEntryTrades:
                            newvalues = {"$set":
                                {
                                    'postCloseReEntry-Disable': True,
                                }
                            }

                            disableTradeCol.update_one(colfilter, newvalues)

                        cooldownTill = datetime.datetime.utcnow() + datetime.timedelta(minutes=45)

                        newvalues = {"$set":
                            {
                                'timerRunning': 'On',
                                'type': 'rsi',
                                'timer': cooldownTill
                            }
                        }

                        disableTradeCol.update_one(colfilter, newvalues)

                        payload = {
                            "username": f"Cooldown Script-:",
                            "content": f"Turning on cooldown due to btcusdt rsi ({last_rsi}) till {cooldownTill}"
                        }

                        requests.post(COOLDOWN_LOGS_URL, json=payload)

        def on_error(ws, error):
            print(error)

        ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message, on_error=on_error)
        ws.run_forever()
    except Exception as e:
        runStream()


runStream()
