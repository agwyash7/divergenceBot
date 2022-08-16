import datetime
import time

import requests
from pymongo import MongoClient

from binanceRawClient import BinanceRawClient

dbclient = MongoClient("mongodb://yashMongo:ChachaMongo$123@198.211.110.141:2727/")
db = dbclient["livebot"]
disableTradeCol = db["activatedPairs"]

results = disableTradeCol.find({})

ACTIVEPAIR_LOGS_URL = "https://discord.com/api/webhooks/923312210015563827/jMOp3r9yyCSzN-fj6YQi1A-7OQu1Pr0VZhT2m1kPrrSry4XQMAZ1o57G1flLuwvMWlEE"

apiKey = "rN58tKBfaXISf8wXzScVxHe2wSu7jxIw45kjLX7bSSiEFlf0DYk0yPa3puqL4LOF"
apiSecret = "rmJwaoxzMQY7naQfAUQSDV4sKgb3uXTdIjZBvAjVEUxafhwuTQgsEJBh8PNCxNuz"
rawClient = BinanceRawClient(key=apiKey, secret=apiSecret)

for r in results:
    symbol = r['symbol']
    print(f"Checking {symbol} offTime")

    timer = r["offTime"]
    now = datetime.datetime.utcnow()

    if now > timer:
        print(f"Disabling the wallet of {symbol}")
        rawClient.disableIsolatedWallet(symbol=symbol)

        payload = {
            "username": f"Active Pair Manage Script",
            "content": f"{symbol} iso wallet turned off"
        }

        requests.post(ACTIVEPAIR_LOGS_URL, json=payload)

        disableTradeCol.delete_one({"symbol": symbol})

        time.sleep(1)
