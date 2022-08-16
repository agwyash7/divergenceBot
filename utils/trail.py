import datetime
import math
import time
from pprint import pprint

import ccxt
import requests
from binance import Client
from binance.enums import *
from pymongo import MongoClient

from binanceRawClient import BinanceRawClient

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


def placeLongOrder(symbol, isolated, price, amount):
    prices = client.get_all_tickers()
    assetInfo = next((item for item in prices if item["symbol"] == symbol), None)
    currentPrice = float(assetInfo["price"])

    if currentPrice <= price:
        buy_order_result = client.create_margin_order(
            symbol=symbol,
            isIsolated=isolated,
            side=SIDE_BUY,
            type=ORDER_TYPE_STOP_LOSS_LIMIT,
            timeInForce=TIME_IN_FORCE_GTC,
            sideEffectType="MARGIN_BUY",
            price=price,
            stopPrice=price,
            quantity=amount
        )
    else:
        buy_order_result = client.create_margin_order(
            symbol=symbol,
            isIsolated=isolated,
            side=SIDE_BUY,
            type=ORDER_TYPE_LIMIT,
            timeInForce=TIME_IN_FORCE_GTC,
            sideEffectType="MARGIN_BUY",
            price=price,
            quantity=amount
        )

    pprint(buy_order_result)


def placeShortOrder(symbol, isolated, price, amount):
    prices = client.get_all_tickers()
    assetInfo = next((item for item in prices if item["symbol"] == symbol), None)
    currentPrice = float(assetInfo["price"])

    if currentPrice >= price:
        buy_order_result = client.create_margin_order(
            symbol=symbol,
            isIsolated=isolated,
            side=SIDE_SELL,
            type=ORDER_TYPE_STOP_LOSS_LIMIT,
            timeInForce=TIME_IN_FORCE_GTC,
            sideEffectType="MARGIN_BUY",
            price=price,
            stopPrice=price,
            quantity=amount
        )
    else:
        buy_order_result = client.create_margin_order(
            symbol=symbol,
            isIsolated=isolated,
            side=SIDE_SELL,
            type=ORDER_TYPE_LIMIT,
            timeInForce=TIME_IN_FORCE_GTC,
            sideEffectType="MARGIN_BUY",
            price=price,
            quantity=amount
        )

    pprint(buy_order_result)


def placeLongStopLoss(symbol, isolated, price, amount):
    prices = client.get_all_tickers()
    assetInfo = next((item for item in prices if item["symbol"] == symbol), None)
    currentPrice = float(assetInfo["price"])

    if price <= currentPrice:
        stop_order_result = client.create_margin_order(
            symbol=symbol,
            isIsolated=isolated,
            side=SIDE_SELL,
            type=ORDER_TYPE_STOP_LOSS,
            timeInForce=TIME_IN_FORCE_GTC,
            sideEffectType="AUTO_REPAY",
            # price=price,
            stopPrice=price,
            quantity=amount
        )
    else:
        stop_order_result = client.create_margin_order(
            symbol=symbol,
            isIsolated=isolated,
            side=SIDE_SELL,
            type=ORDER_TYPE_TAKE_PROFIT,
            timeInForce=TIME_IN_FORCE_GTC,
            sideEffectType="AUTO_REPAY",
            # price=price,
            stopPrice=price,
            quantity=amount
        )

    pprint(stop_order_result)


def placeShortStopLoss(symbol, isolated, price, amount):
    prices = client.get_all_tickers()
    assetInfo = next((item for item in prices if item["symbol"] == symbol), None)
    currentPrice = float(assetInfo["price"])

    if price >= currentPrice:
        stop_order_result = client.create_margin_order(
            symbol=symbol,
            isIsolated=isolated,
            side=SIDE_BUY,
            type=ORDER_TYPE_STOP_LOSS,
            timeInForce=TIME_IN_FORCE_GTC,
            sideEffectType="AUTO_REPAY",
            # price=price,
            stopPrice=price,
            quantity=amount
        )
    else:
        stop_order_result = client.create_margin_order(
            symbol=symbol,
            isIsolated=isolated,
            side=SIDE_BUY,
            type=ORDER_TYPE_TAKE_PROFIT,
            timeInForce=TIME_IN_FORCE_GTC,
            sideEffectType="AUTO_REPAY",
            # price=price,
            stopPrice=price,
            quantity=amount
        )

    pprint(stop_order_result)


def closeLongMarket(symbol, isolated, amount):
    closePosition_result = client.create_margin_order(symbol=symbol,
                                                      isIsolated=isolated,
                                                      side=SIDE_SELL,
                                                      type=ORDER_TYPE_MARKET,
                                                      sideEffectType="AUTO_REPAY",
                                                      quantity=amount)

    pprint(closePosition_result)

    avgClosePrice = 0

    for fill in closePosition_result["fills"]:
        avgClosePrice = avgClosePrice + (float(fill["price"]) * float(fill["qty"]))

    pprint(avgClosePrice)


def closeShortMarket(symbol, isolated, amount):
    closePosition_result = client.create_margin_order(symbol=symbol,
                                                      isIsolated=isolated,
                                                      side=SIDE_BUY,
                                                      type=ORDER_TYPE_MARKET,
                                                      sideEffectType="AUTO_REPAY",
                                                      quantity=amount)

    pprint(closePosition_result)


def entryLongMarket(symbol, isolated, amount):
    entryPosition_result = client.create_margin_order(symbol=symbol,
                                                      isIsolated=isolated,
                                                      side=SIDE_BUY,
                                                      type=ORDER_TYPE_MARKET,
                                                      sideEffectType="MARGIN_BUY",
                                                      quantity=amount)

    pprint(entryPosition_result)

    avgEntryPrice = 0

    for fill in entryPosition_result["fills"]:
        avgEntryPrice = avgEntryPrice + (float(fill["price"]) * float(fill["qty"]))

    pprint(avgEntryPrice)


def entryShortMarket(symbol, isolated, amount):
    entryPosition_result = client.create_margin_order(symbol=symbol,
                                                      isIsolated=isolated,
                                                      side=SIDE_SELL,
                                                      type=ORDER_TYPE_MARKET,
                                                      sideEffectType="MARGIN_BUY",
                                                      quantity=amount)

    pprint(entryPosition_result)

    avgEntryPrice = 0

    for fill in entryPosition_result["fills"]:
        avgEntryPrice = avgEntryPrice + (float(fill["price"]) * float(fill["qty"]))

    pprint(avgEntryPrice)


def orderDetail(symbol, isolated, id):
    order = client.get_margin_order(symbol=symbol, isIsolated=isolated, orderId=id)
    pprint(order)


def round_down(symbol, number):
    info = client.get_symbol_info('%s' % symbol)
    step_size = [float(_['stepSize']) for _ in info['filters'] if _['filterType'] == 'LOT_SIZE'][0]
    step_size = '%.8f' % step_size
    step_size = step_size.rstrip('0')
    decimals = len(step_size.split('.')[1])
    return math.floor(number * 10 ** decimals) / 10 ** decimals


def transferAvailableMoneyOutOfISO(symbol, coinPair, asset):
    info = client.get_isolated_margin_account()
    assetInfo = next((item for item in info['assets'] if item["symbol"] == symbol), None)
    # pprint(assetInfo)

    baseAssetFree = float((assetInfo["baseAsset"])["free"])
    quoteAssetFree = float((assetInfo["quoteAsset"])["free"])

    baseAssetFees = float((assetInfo["baseAsset"])["borrowed"])
    quoteAssetFees = float((assetInfo["quoteAsset"])["borrowed"])

    print("Base Asset Free -:", baseAssetFree)
    print("Quote Asset Free -:", quoteAssetFree)

    if baseAssetFree > 0 and baseAssetFees > 0:
        if baseAssetFees > baseAssetFree:
            client.repay_margin_loan(asset=asset, amount=f'{baseAssetFree}', isIsolated=True, symbol=symbol)
            baseAssetFees = baseAssetFees - baseAssetFree
        elif baseAssetFees <= baseAssetFree:
            client.repay_margin_loan(asset=asset, amount=f'{baseAssetFees}', isIsolated=True, symbol=symbol)
            baseAssetFees = 0

    if quoteAssetFree > 0 and quoteAssetFees > 0:
        if quoteAssetFees > quoteAssetFree:
            client.repay_margin_loan(asset=coinPair, amount=f'{quoteAssetFree}', isIsolated=True, symbol=symbol)
            quoteAssetFees = quoteAssetFees - quoteAssetFree
        elif quoteAssetFees <= quoteAssetFree:
            client.repay_margin_loan(asset=coinPair, amount=f'{quoteAssetFree}', isIsolated=True, symbol=symbol)
            quoteAssetFees = 0

    print("Base Asset Fees -:", quoteAssetFees)
    print("Quote Asset Fees -:", quoteAssetFees)

    if baseAssetFees > 0:
        if onlyISO:
            transferSPOTtoISOLATEDMARGIN(asset=asset, symbol=symbol, amount=baseAssetFees)
        else:
            transferCROSStoISOLATEDMARGIN(asset=asset, symbol=symbol, amount=baseAssetFees)

        client.repay_margin_loan(asset=asset, amount=f'{baseAssetFees}', isIsolated=True, symbol=symbol)

    if quoteAssetFees > 0:
        transferCROSStoISOLATEDMARGIN(asset=coinPair, symbol=symbol, amount=quoteAssetFees)
        client.repay_margin_loan(asset=coinPair, amount=f'{quoteAssetFees}', isIsolated=True,
                                 symbol=symbol)

    coinPairMaxTransfer = client.get_max_margin_transfer(asset=coinPair, isolatedSymbol=symbol)
    coinPairMaxTransfer = float(coinPairMaxTransfer['amount'])
    pprint(coinPairMaxTransfer)

    baseAssetMaxTransfer = client.get_max_margin_transfer(asset=asset, isolatedSymbol=symbol)
    baseAssetMaxTransfer = float(baseAssetMaxTransfer['amount'])
    pprint(baseAssetMaxTransfer)

    if coinPairMaxTransfer > 0:
        transferISOLOATEDMARGINtoCROSS(asset=coinPair, symbol=symbol, amount=coinPairMaxTransfer)

    if baseAssetMaxTransfer > 0:
        if onlyISO:
            transferISOLATEDMARGINtoSPOT(asset=asset, symbol=symbol, amount=baseAssetMaxTransfer)
        else:
            transferISOLOATEDMARGINtoCROSS(asset=asset, symbol=symbol, amount=baseAssetMaxTransfer)


def findWallet(symbol):
    if coinPair == "ETH":
        wallet = "CROSS 3X"
    else:
        marginInfo = client.get_all_isolated_margin_symbols()
        marginAllowed = next((item for item in marginInfo if item["symbol"] == symbol), None)

        if marginAllowed:
            transferSPOTtoISOLATEDMARGIN(coinPair, symbol, 0.00001)
            info = client.get_isolated_margin_account()
            marginPair = next((item for item in info['assets'] if item["symbol"] == symbol), None)
            wallet = int(marginPair['marginRatio'])
            transferISOLATEDMARGINtoSPOT(asset=coinPair, symbol=symbol, amount=0.00001)
        else:
            wallet = "CROSS 3X"

    return wallet


symbol = "ADAUSDT"
coinPair = "USDT"
asset = "ADA"
walletRatio = 10
isolated = True
transfer = True

price = 1.315
amount = 11/price
onlyISO = True

# transferSPOTtoISOLATEDMARGIN(coinPair, symbol, 0.0000001)
# transferISOLATEDMARGINtoSPOT(asset=coinPair, symbol=symbol, amount=0.0000001)

# rawClient = BinanceRawClient(key=apiKey, secret=apiSecret)
# print(rawClient.enableIsolatedWallet(symbol=symbol))

# print(findWallet(symbol))

print(amount)
amount = round_down(symbol, amount)
print(amount)

# transferSPOTtoISOLATEDMARGIN(asset=coinPair, symbol=symbol, amount=0.0001)

# info = client.get_symbol_info('%s' % symbol)
# minQty = [float(_['minQty']) for _ in info['filters'] if _['filterType'] == 'LOT_SIZE'][0]
# minNotional = [float(_['minNotional']) for _ in info['filters'] if _['filterType'] == 'MIN_NOTIONAL'][0]
#
# if coinPair == "USDT":
#     if amount * price < 10.5:
#         amount = 10.5 / price
#         amount = round_down(symbol=symbol, number=amount)
#
# if coinPair == "BTC" or coinPair == "ETH":
#     if amount < minQty:
#         amount = minQty + (0.05 * minQty)
#         amount = round_down(symbol=symbol, number=amount)
#
#     if (amount * price) < minNotional:
#         amount = (minNotional + (0.1 * minNotional)) / price
#         amount = round_down(symbol=symbol, number=amount)
#
# print("Min Quantity -: ", minQty)
# print("Min Notional -: ", minNotional)
# print("Amount -: ", amount)
# print("Price -: ", price)
# print("Cost -: {0:.10f}".format(amount*price))

# entryLongMarket(symbol=symbol, isolated=isolated, amount=amount)
# closeLongMarket(symbol=symbol, isolated=isolated, amount=amount)
# pprint(info)
# transferAvailableMoneyOutOfISO(symbol, coinPair, asset)

# tickerPrices = client.get_all_tickers()
#
# btcusdtPrice = next((float(item['price']) for item in tickerPrices if item["symbol"] == "BTCUSDT"), None)
# btcethPrice = next((float(item['price']) for item in tickerPrices if item["symbol"] == "ETHBTC"), None)
# btcethPrice = 1.00/btcethPrice
#
# isoAccountDetails = client.get_isolated_margin_account()
# isoBalanceBTC = float(isoAccountDetails["totalAssetOfBtc"])
# isoBalanceUSDT = float(isoBalanceBTC * btcusdtPrice)
# isoBalanceETH = float(isoBalanceBTC * btcethPrice)
#
# crossAccountDetails = client.get_margin_account()
# crossBalanceBTC = float(crossAccountDetails["totalAssetOfBtc"])
# crossBalanceUSDT = float(crossBalanceBTC * btcusdtPrice)
# crossBalanceETH = float(crossBalanceBTC * btcethPrice)
#
# pprint(crossBalanceBTC)
# pprint(isoBalanceBTC)
#
# pprint(crossBalanceUSDT)
# pprint(isoBalanceUSDT)
#
# pprint(crossBalanceETH)
# pprint(isoBalanceETH)

# info = client.get_symbol_info("frontbtc")
# pprint(info)
# transferAvailableMoneyOutOfISO(symbol, coinPair)

# walletInfo = findWallet(symbol)
# print(walletInfo)

# maxBorrow = client.get_max_margin_loan(asset="BTC", isolatedSymbol="OGNBTC")
# maxTransfer = client.get_max_margin_transfer(asset="BTC", isolatedSymbol="OGNBTC")
#
# maxBorrow = float(maxBorrow["amount"])
# maxTransfer = float(maxTransfer["amount"])
#
# borrowAllowed = maxBorrow + maxTransfer
#
# print(borrowAllowed)

# if isolated and transfer:
#     # usdtSPOTBalance, usdtCROSSBalance, btcSPOTBalance, btcCROSSBalance, ethSPOTBalance, ethCROSSBalance = accountBalance()
#     prices = client.get_all_tickers()
#     assetInfo = next((item for item in prices if item["symbol"] == symbol), None)
#     currentPrice = float(assetInfo["price"])
#
#     if coinPair == "BTC":
#         toTransfer = (amount * currentPrice) / walletRatio
#         transferCROSStoISOLATEDMARGIN(asset="BTC", symbol=symbol, amount=toTransfer)
#
#     if coinPair == "USDT":
#         toTransfer = (amount * currentPrice) / walletRatio
#         transferCROSStoISOLATEDMARGIN(asset="USDT", symbol=symbol, amount=toTransfer)

# if isolated:
#     info = client.get_isolated_margin_account()
#     assetInfo = next((item for item in info['assets'] if item["symbol"] == symbol), None)
#     pprint(assetInfo)
#
#     amount = float(assetInfo["baseAsset"]["free"])
# orderDetail(symbol, isolated, 831645910)
# orderDetail(symbol, isolated, 353663101)

# placeLongOrder(symbol, isolated, price, amount)
# placeLongStopLoss(symbol, isolated, price, amount)
# entryLongMarket(symbol, isolated, amount)
# closeLongMarket(symbol, isolated, amount)

# placeShortOrder(symbol, isolated, price, amount)
# placeShortStopLoss(symbol, isolated, price, amount)
# entryShortMarket(symbol, isolated, amount)
# closeShortMarket(symbol, isolated, amount)

# if isolated:
#     info = client.get_isolated_margin_account()
#     assetInfo = next((item for item in info['assets'] if item["symbol"] == symbol), None)
#
#     pprint(assetInfo)

# self.setupBarNo = 0
# self.orderAlreadyOpenFor = 0
# self.trailSTL = self.TSLBars
# self.dcSetupBarLeft = self.dcSetupBarRechecks

# self.entryFilled = False
# self.checkEntryOrderPrice = False
#
# self.stoplossFilled = False
# self.checkStoplossOrderPrice = False
#
# self.reEntryBarsCheckTillNow = 0
# self.reEntryCyclesCheckTillNow = 0
#
# self.postCloseCheckTillNow = 0
# self.postCloseDivCountTillNow = 0
# self.postCloseSuccessfulDivCount = 0

# self.current_order.clear()


# dbclient = MongoClient("mongodb://yashMongo:ChachaMongo$123@198.211.110.141:2727/")
# dbclient = MongoClient("mongodb://localhost:27017")
# db = dbclient["livebot"]
#
# disableTradeCol = db["disableTrades"]
#
# now = datetime.datetime.utcnow() + datetime.timedelta(minutes=1)
#
# colfilter = {
#                 'settingName': "disabledTrades",
#             }
#
# newvalues = {"$set":
#                  {
#                      'timer': now,
#                  }
#              }
#
# disableTradeCol.update_one(colfilter, newvalues)

# cooldownTill = datetime.datetime.utcnow() + datetime.timedelta(minutes=45)
# payload = {
#             "username": f"Cooldown Script-:",
#             "content": f"Turning on cooldown due to till ({cooldownTill.strftime('%Y-%m-%d %H:%M:00')})"
#         }
# COOLDOWN_LOGS_URL = "https://discord.com/api/webhooks/898326514276368384/HeK0W_z1GDtYU1DCR8jEfVOCQ-59ux2g9C-iBJi-kk6N_95osnLL3Bmr0jKzqCxfXwZw"
#
# requests.post(COOLDOWN_LOGS_URL, json=payload)
