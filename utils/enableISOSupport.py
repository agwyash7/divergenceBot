import time

from binance import Client

from binanceRawClient import BinanceRawClient

apiKey = "rN58tKBfaXISf8wXzScVxHe2wSu7jxIw45kjLX7bSSiEFlf0DYk0yPa3puqL4LOF"
apiSecret = "rmJwaoxzMQY7naQfAUQSDV4sKgb3uXTdIjZBvAjVEUxafhwuTQgsEJBh8PNCxNuz"

client = Client(apiKey, apiSecret)
rawClient = BinanceRawClient(key=apiKey, secret=apiSecret)


def transferSPOTtoISOLATEDMARGIN(asset, symbol, amount):
    transaction = client.transfer_spot_to_isolated_margin(asset=asset, symbol=symbol, amount=f'{amount}')
    return transaction


def transferISOLATEDMARGINtoSPOT(asset, symbol, amount):
    transaction = client.transfer_isolated_margin_to_spot(asset=asset, symbol=symbol, amount=f'{amount}')
    return transaction


coins = [
    "ardrbtc",
    "blzbtc",
    "ctxcbtc",
    "gtobtc",
    "gxsbtc",
    "icxbtc",
    "kncbtc",
    "nulsbtc",
    "oceanbtc",
    "oxtbtc",
    "perlbtc",
    "pntbtc",
    "renbtc",
    "rlcbtc",
    "runebtc",
    "storjbtc",
    "sysbtc",
    "zenbtc",
    "arpabtc",
    "bandbtc",
    "belbtc",
    "cvcbtc",
    "duskbtc",
    "fetbtc",
    "flmbtc",
    "fttbtc",
    "irisbtc",
    "ltobtc",
    "paxgbtc",
    "wrxbtc"
]

info = client.get_isolated_margin_account()

for coin in coins:
    marginSymbol = coin.upper()
    if "BTC" in marginSymbol:
        coinPair = "BTC"
    elif "USDT" in marginSymbol:
        coinPair = "USDT"
    else:
        coinPair = "ETH"

    symbolInfo = [_ for _ in info['assets'] if _['symbol'] == marginSymbol]

    if len(symbolInfo) == 0:
        print(f"Symbol({marginSymbol} do not exists in Iso Account, Transferring from spot to activate it")
        transferSPOTtoISOLATEDMARGIN(coinPair, marginSymbol, 0.000001)
        transferISOLATEDMARGINtoSPOT(asset=coinPair, symbol=marginSymbol, amount=0.000001)
        rawClient.disableIsolatedWallet(symbol=marginSymbol)

        time.sleep(1)





    
    