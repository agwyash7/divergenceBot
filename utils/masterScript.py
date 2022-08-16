import datetime
import math
import sys
import time
from pprint import pprint

import pandas as pd
import requests
from binance import Client
from binance.enums import SIDE_SELL, ORDER_TYPE_MARKET
from pymongo import MongoClient

dbClient = MongoClient("mongodb://yashMongo:ChachaMongo$123@198.211.110.141:2727/")
# dbClient = MongoClient("mongodb://localhost:27017/")

db = dbClient["livebot"]

apiKey = "rN58tKBfaXISf8wXzScVxHe2wSu7jxIw45kjLX7bSSiEFlf0DYk0yPa3puqL4LOF"
apiSecret = "rmJwaoxzMQY7naQfAUQSDV4sKgb3uXTdIjZBvAjVEUxafhwuTQgsEJBh8PNCxNuz"

client = Client(apiKey, apiSecret)


def transferSPOTtoCROSS(asset, amount):
    transaction = client.transfer_spot_to_margin(asset=asset, amount=f'{amount}')
    return transaction


def transferCROSStoSPOT(asset, amount):
    transaction = client.transfer_margin_to_spot(asset=asset, amount=f'{amount}')
    return transaction


def transferSPOTtoISOLATEDMARGIN(asset, symbol, amount):
    transaction = client.transfer_spot_to_isolated_margin(asset=asset, symbol=symbol, amount=f'{amount}')
    return transaction


def transferISOLATEDMARGINtoSPOT(asset, symbol, amount):
    transaction = client.transfer_isolated_margin_to_spot(asset=asset, symbol=symbol, amount=f'{amount}')
    return transaction


def transferCROSStoISOLATEDMARGIN(asset, symbol, amount):
    transferCROSStoSPOT(asset=asset, amount=amount)
    transferSPOTtoISOLATEDMARGIN(asset=asset, symbol=symbol, amount=amount)


def transferISOLOATEDMARGINtoCROSS(asset, symbol, amount):
    transferISOLATEDMARGINtoSPOT(asset=asset, symbol=symbol, amount=amount)
    transferSPOTtoCROSS(asset=asset, amount=amount)


def emptyISOWallets():
    len = 0

    info = client.get_isolated_margin_account()

    for assetInfo in info["assets"]:
        print("*" * 100)
        len = len + 1

        symbol = assetInfo["symbol"]
        baseAsset = assetInfo["baseAsset"]["asset"]
        coinPair = assetInfo["quoteAsset"]["asset"]

        baseAssetFree = float((assetInfo["baseAsset"])["free"])
        quoteAssetFree = float((assetInfo["quoteAsset"])["free"])

        baseAssetFees = float((assetInfo["baseAsset"])["borrowed"])
        quoteAssetFees = float((assetInfo["quoteAsset"])["borrowed"])

        if baseAssetFree > 0 and baseAssetFees > 0:
            if baseAssetFees > baseAssetFree:
                client.repay_margin_loan(asset=baseAsset, amount=f'{baseAssetFree}', isIsolated=True, symbol=symbol)
                baseAssetFees = baseAssetFees - baseAssetFree
            elif baseAssetFees <= baseAssetFree:
                client.repay_margin_loan(asset=baseAsset, amount=f'{baseAssetFees}', isIsolated=True, symbol=symbol)
                baseAssetFees = 0

        if quoteAssetFree > 0 and quoteAssetFees > 0:
            if quoteAssetFees > quoteAssetFree:
                client.repay_margin_loan(asset=coinPair, amount=f'{quoteAssetFree}', isIsolated=True, symbol=symbol)
                quoteAssetFees = quoteAssetFees - quoteAssetFree
            elif quoteAssetFees <= quoteAssetFree:
                client.repay_margin_loan(asset=coinPair, amount=f'{quoteAssetFree}', isIsolated=True, symbol=symbol)
                quoteAssetFees = 0

        print(f"{baseAsset} Borrowed -: {baseAssetFees}")
        print(f"{coinPair} Borrowed -: {quoteAssetFees}")

        if baseAssetFees > 0:
            print(f"Paying {baseAsset} fees")

            try:
                transferSPOTtoISOLATEDMARGIN(asset=baseAsset, symbol=symbol, amount=baseAssetFees)
            except Exception as e:
                transferCROSStoISOLATEDMARGIN(asset=baseAsset, symbol=symbol, amount=baseAssetFees)

            client.repay_margin_loan(asset=baseAsset, amount=f'{baseAssetFees}', isIsolated=True,
                                     symbol=symbol)

        if quoteAssetFees > 0:
            print(f"Paying {coinPair} fees")

            transferCROSStoISOLATEDMARGIN(asset=coinPair, symbol=symbol, amount=quoteAssetFees)
            client.repay_margin_loan(asset=coinPair, amount=f'{quoteAssetFees}', isIsolated=True, symbol=symbol)

        coinPairMaxTransfer = client.get_max_margin_transfer(asset=coinPair, isolatedSymbol=symbol)
        coinPairMaxTransfer = float(coinPairMaxTransfer['amount'])

        print(f"{coinPair} Max Transfer Allowed -: {coinPairMaxTransfer}")

        baseAssetMaxTransfer = client.get_max_margin_transfer(asset=baseAsset, isolatedSymbol=symbol)
        baseAssetMaxTransfer = float(baseAssetMaxTransfer['amount'])

        print(f"{baseAsset} Max Transfer Allowed -: {baseAssetMaxTransfer}")

        if coinPairMaxTransfer > 0:
            transferISOLOATEDMARGINtoCROSS(asset=coinPair, symbol=symbol, amount=coinPairMaxTransfer)

        if baseAssetMaxTransfer > 0:
            try:
                transferISOLATEDMARGINtoSPOT(asset=baseAsset, symbol=symbol, amount=baseAssetMaxTransfer)
            except Exception as e:
                transferISOLOATEDMARGINtoCROSS(asset=baseAsset, symbol=symbol, amount=baseAssetMaxTransfer)


def printCoins():
    symbolsCollection = db["tests"]
    result = symbolsCollection.find({"logSheet": "G3.5 Latest"})

    res = {}
    for r in result:
        res[r['historicalSymbol']] = str(r['_id'])

    pprint(res)
    pprint(len(res))


def turnOffParticularCoin():
    symbolsCollection = db["pairs"]
    result = symbolsCollection.find({"logSheet": "Live Bot Log (G1)", "symbol": "avaxusdt"})

    res = {}
    for r in result:
        print(f"{len}) Turning off {r['marginSymbol']}")

        requests.post(f"http://198.211.110.141:7777/pair/{r['_id']}/stop", auth=("YashSecretUsername", "YashSecretPasswordOcean123"))
        time.sleep(1)
        # res[r['historicalSymbol']] = str(r['_id'])

    # pprint(res)
    # pprint(len(res))


def findWallet(coinPair, marginSymbol, onlyISO):
    if coinPair == "ETH":
        wallet = "CROSS 3X"
    else:
        marginInfo = client.get_all_isolated_margin_symbols()
        symbolInfo = next((item for item in marginInfo if item["symbol"] == marginSymbol), None)

        if symbolInfo:
            if onlyISO:
                transferSPOTtoISOLATEDMARGIN(coinPair, marginSymbol, 0.00001)
            else:
                transferCROSStoISOLATEDMARGIN(coinPair, marginSymbol, 0.00001)

            wallet = int(symbolInfo['marginRatio'])

            transferISOLATEDMARGINtoSPOT(asset=coinPair, symbol=marginSymbol, amount=0.00001)
        else:
            wallet = "CROSS 3X"

    return wallet


def accountBalance():
    spotBalance = client.get_account()
    usdtSPOTBalance = next((item for item in spotBalance['balances'] if item["asset"] == "USDT"), None)
    btcSPOTBalance = next((item for item in spotBalance['balances'] if item["asset"] == "BTC"), None)
    ethSPOTBalance = next((item for item in spotBalance['balances'] if item["asset"] == "ETH"), None)

    crossBalance = client.get_margin_account()
    usdtCROSSBalance = next((item for item in crossBalance['userAssets'] if item["asset"] == "USDT"), None)
    btcCROSSBalance = next((item for item in crossBalance['userAssets'] if item["asset"] == "BTC"), None)
    ethCROSSBalance = next((item for item in crossBalance['userAssets'] if item["asset"] == "ETH"), None)

    return usdtSPOTBalance["free"], usdtCROSSBalance["free"], btcSPOTBalance["free"], btcCROSSBalance["free"], ethSPOTBalance["free"], ethCROSSBalance["free"]


def printAccountBalances():
    usdtSPOTBalance, usdtCROSSBalance, btcSPOTBalance, btcCROSSBalance, ethSPOTBalance, ethCROSSBalance = accountBalance()
    print("*" * 32 + "Account Balances" + "*" * 32)
    print(f"USDT SPOT BALANCE -: {usdtSPOTBalance}")
    print(f"USDT CROSS BALANCE -: {usdtCROSSBalance}")
    print(f"BTC SPOT BALANCE -: {btcSPOTBalance}")
    print(f"BTC CROSS BALANCE -: {btcCROSSBalance}")
    print(f"ETH SPOT BALANCE -: {ethSPOTBalance}")
    print(f"ETH CROSS BALANCE -: {ethCROSSBalance}")
    print("*" * 80)


def turnOffAllCoins(wait):
    symbolsCollection = db["pairs"]
    result = symbolsCollection.find({})

    symbols = []
    len = 0
    for r in result:
        if r['marginSymbol'] not in symbols:
            len = len + 1
            print(f"{len}) Turning off {r['marginSymbol']}")

            requests.post(f"http://198.211.110.141:7777/pair/{r['_id']}/stop", auth=("YashSecretUsername", "YashSecretPasswordOcean123"))
            time.sleep(wait)

            # if len == 45:
            #     sys.exit()


def turnOnAllCoins(wait, startPoint):
    symbolsCollection = db["pairs"]
    result = list(symbolsCollection.find({}))

    print(len(result))

    l = 0
    for r in result:
        if r['logSheet'] != 'Live Bot Log (G4)':
            l = l + 1
            print(f"{l}) Turning on {r['marginSymbol']} - {r['logSheet']}")

            data = {
                "symbol": r['symbol']
            }

            if l >= startPoint:
                requests.post(f"http://198.211.110.141:7777/pair/{r['_id']}/start", auth=("YashSecretUsername", "YashSecretPasswordOcean123"), json=data)
                time.sleep(wait)


def dbTurnActiveOff():
    symbolsCollection = db["pairs"]
    result = symbolsCollection.find({})

    len = 0
    for r in result:
        len = len + 1
        print(f"Turning off {r['marginSymbol']}")

        data = {
            "isActive": False
        }

        symbolsCollection.update_one({"_id": r['_id']}, {"$set": data})


def collectionCopy(name):
    mycol = db[name]

    # Copy One Collection to another
    pipeline = [{"$match": {}},
                {"$out": f"{name}_copy"},
                ]

    mycol.aggregate(pipeline)


def dbUpdate():
    symbolsCollection = db["pairs"]
    result = symbolsCollection.find({"logSheet": "Live Bot Log (V1)"})
    len = 0
    for r in result:
        len = len + 1
        print(f"{len}) Updating {r['marginSymbol']}")

        data = {
            "logSheet": "Live Bot Log (G2)"
        }

        symbolsCollection.update_one({"_id": r['_id']}, {"$set": data})


def insertActivePairs(symbol, wallet):
    activatedPairsCollection = db["activatedPairs"]

    offTime = datetime.datetime.utcnow() + datetime.timedelta(minutes=1)

    data = {
        'symbol': symbol,
        'wallet': wallet,
        'offTime': offTime
    }

    activatedPairsCollection.insert_one(data)


def isSymbolActive(symbol):
    activatedPairsCollection = db["activatedPairs"]
    result = list(activatedPairsCollection.find({"symbol": symbol}))

    if len(result) > 0:
        return True, result[0]
    else:
        return False, {}


def round_down(symbol, number):
    info = client.get_symbol_info('%s' % symbol)
    step_size = [float(_['stepSize']) for _ in info['filters'] if _['filterType'] == 'LOT_SIZE'][0]
    step_size = '%.8f' % step_size
    step_size = step_size.rstrip('0')
    decimals = len(step_size.split('.')[1])
    return math.floor(number * 10 ** decimals) / 10 ** decimals


account = client.get_account()
# pprint(account)

for asset in account["balances"]:
    if asset["free"] != '0':
        try:
            amount = round_down(f"{asset['asset']}BTC", float(asset["free"]))
            # amount = float(asset['free'])
            # print(amount)

            client.create_order(
                symbol=f"{asset['asset']}BTC",
                side=SIDE_SELL,
                quantity=amount,
                type=ORDER_TYPE_MARKET
            )

            print(f"Sold {asset['asset']}")
            time.sleep(0.1)
        except Exception as e:
            print(f"Got exception in {asset['asset']} - {e}")




# db.Pairs.aggregate({"name.additional": {$exists: true}}, {$rename:{"name.additional":"name.last"}}, false, true);
# db["Pairs"].aggregate([{"onlyIso": {$exists: true}}])

# printCoins()
# printAccountBalances()
# emptyISOWallets()
# turnOnAllCoins(wait=30, startPoint=1)
# turnOffAllCoins(wait=0.2)
# turnOffParticularCoin()

# dbTurnActiveOff()
# collectionCopy("pairs")
# dbUpdate()

# insertActivePairs(symbol="ADAUSDT", wallet=10)
# isSymbolActive(symbol="ADAETH")
