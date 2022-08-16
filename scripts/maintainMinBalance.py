import datetime
import json
import math
from pprint import pprint
from pymongo import MongoClient
from binance import Client
from binance.enums import SIDE_BUY, ORDER_TYPE_MARKET
from binance.exceptions import BinanceAPIException

apiKey = "rN58tKBfaXISf8wXzScVxHe2wSu7jxIw45kjLX7bSSiEFlf0DYk0yPa3puqL4LOF"
apiSecret = "rmJwaoxzMQY7naQfAUQSDV4sKgb3uXTdIjZBvAjVEUxafhwuTQgsEJBh8PNCxNuz"

client = Client(apiKey, apiSecret)

mongoclient = MongoClient("mongodb://yashMongo:ChachaMongo$123@198.211.110.141:2727/")
# client = MongoClient("mongodb://localhost:27017/")

db = mongoclient["livebot"]


def round_down(symbol, number):
    info = client.get_symbol_info('%s' % symbol)
    step_size = [float(_['stepSize']) for _ in info['filters'] if _['filterType'] == 'LOT_SIZE'][0]
    step_size = '%.8f' % step_size
    step_size = step_size.rstrip('0')
    decimals = len(step_size.split('.')[1])
    return math.floor(number * 10 ** decimals) / 10 ** decimals


info = client.get_account()
marginInfo = client.get_margin_account()

tickerPrices = client.get_all_tickers()


def maintainBalance(asset, onlyISO):
    minBalance = 0.00023
    minBalanceThreshold = 0.00011
    coin = asset

    if onlyISO:
        balance = next((item for item in info["balances"] if item["asset"] == coin), None)
    else:
        balance = next((item for item in marginInfo["userAssets"] if item["asset"] == coin), None)

    balance = float(balance["free"])

    currentPrice = next((item for item in tickerPrices if item["symbol"] == f"{coin}BTC"), None)
    currentPrice = float(currentPrice["price"])

    balanceRequired = minBalance / currentPrice
    thresholdBalanceRequired = minBalanceThreshold / currentPrice

    # print(f"{coin} -: Available Balance - {balance}, Balance Required - {balanceRequired}, Threshold Balance Required - {thresholdBalanceRequired}")

    if balance < thresholdBalanceRequired:
        toBuy = balanceRequired - balance
        toBuy = round_down(f"{coin}BTC", toBuy)
        try:
            if onlyISO:
                client.create_order(symbol=f"{coin}BTC",
                                    side=SIDE_BUY,
                                    type=ORDER_TYPE_MARKET,
                                    quantity=toBuy)
            else:
                client.create_margin_order(symbol=f"{coin}BTC",
                                           side=SIDE_BUY,
                                           type=ORDER_TYPE_MARKET,
                                           quantity=toBuy)

            print(f"{coin} -: bought {toBuy} to reach minimum balance requirement")
        except BinanceAPIException as e:
            print(f"---- {coin} -: cannot buy the required amount ({toBuy}) due to this error '{e}'")
    # else:
    # print(f"{coin} -: already enough balance")


def main():
    symbolsCollection = db["pairs"]
    result = symbolsCollection.find({})

    # print("*"*32)
    print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Running Min Balance Maintenance Script")
    # print("*" * 32)

    symbols = []
    len = 0
    for r in result:
        if r['baseAsset'] not in symbols:
            len = len + 1
            maintainBalance(r['baseAsset'], r['onlyISO'])
            symbols.append(r['baseAsset'])


main()
