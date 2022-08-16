import datetime
import json
import time
from pprint import pprint

import pandas as pd
import requests
from pymongo import MongoClient

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
pd.options.display.float_format = '{:,.8f}'.format
pd.options.mode.chained_assignment = None

client = MongoClient("mongodb://yashMongo:ChachaMongo$123@198.211.110.141:2727/")
# client = MongoClient("mongodb://localhost:27017/")

db = client["livebot"]


def createHTFDataframe(data):
    columns = ['Open_time', 'Open', 'High', 'Low', 'Close', 'Volume',
               'Close_time', 'quote_asset_volume', 'no_of_trades',
               'taker_base_vol', 'taker_quote_vol', 'ignore']

    df = pd.DataFrame(data, columns=columns)

    df.drop(columns=['quote_asset_volume', 'no_of_trades', 'taker_base_vol', 'taker_quote_vol', 'ignore'], inplace=True)

    df["_id"] = [x for x in df.Open_time]
    df["Close_time"] = [x + 1 for x in df.Close_time]
    df["Open_time_datetime"] = [datetime.datetime.utcfromtimestamp(x / 1000.0).strftime("%Y-%m-%d %H:%M:%S") for x in df.Open_time]
    df["Close_time_datetime"] = [datetime.datetime.utcfromtimestamp(x / 1000.0).strftime("%Y-%m-%d %H:%M:%S") for x in df.Close_time]

    df.High = df.High.astype(float)
    df.Close = df.Close.astype(float)
    df.Low = df.Low.astype(float)
    df.Open = df.Open.astype(float)
    df.Volume = df.Volume.astype(float)

    df.drop(df.tail(1).index, inplace=True)

    return df


def download_1h_data(symbol):
    try:
        t = datetime.datetime.utcnow()

        rounded = (t - (t - datetime.datetime.min) % datetime.timedelta(hours=1)) - datetime.timedelta(hours=1)
        rounded = rounded.replace(tzinfo=datetime.timezone.utc)
        rounded_add = rounded + datetime.timedelta(minutes=100)
        rounded_add = rounded_add.replace(tzinfo=datetime.timezone.utc)
        rounded_add_timestamp = int(rounded_add.timestamp() * 1000)

        r = requests.get('https://api.binance.com/api/v3/klines',
                         params={
                             "symbol": symbol,
                             "interval": "1h",
                             "endTime": int(rounded_add_timestamp),
                             "limit": 1000
                         })

        data = json.loads(r.text)
        df = createHTFDataframe(data)

        collection = db[f"{symbol}_1h"]
        datadict = df.to_dict('records')
        collection.insert_many(datadict)
    except Exception as e:
        print(f"Error -: {symbol}, {e}")


def download_1d_data(symbol):
    try:
        t = datetime.datetime.utcnow()

        rounded = (t - (t - datetime.datetime.min) % datetime.timedelta(days=1)) - datetime.timedelta(days=1)
        rounded = rounded.replace(tzinfo=datetime.timezone.utc)
        rounded_add = rounded + datetime.timedelta(hours=27)
        rounded_add = rounded_add.replace(tzinfo=datetime.timezone.utc)
        rounded_add_timestamp = int(rounded_add.timestamp() * 1000)

        r = requests.get('https://api.binance.com/api/v3/klines',
                         params={
                             "symbol": symbol,
                             "interval": "1d",
                             "endTime": int(rounded_add_timestamp),
                             "limit": 1000
                         })

        data = json.loads(r.text)
        df = createHTFDataframe(data)

        collection = db[f"{symbol}_1d"]
        datadict = df.to_dict('records')
        collection.insert_many(datadict)
    except Exception as e:
        print(f"Error -: {symbol}, {e}")


def download_2h_data(symbol):
    try:
        t = datetime.datetime.utcnow()

        rounded = (t - (t - datetime.datetime.min) % datetime.timedelta(hours=2)) - datetime.timedelta(hours=2)
        rounded = rounded.replace(tzinfo=datetime.timezone.utc)
        rounded_add = rounded + datetime.timedelta(minutes=180)
        rounded_add = rounded_add.replace(tzinfo=datetime.timezone.utc)
        rounded_add_timestamp = int(rounded_add.timestamp() * 1000)

        r = requests.get('https://api.binance.com/api/v3/klines',
                         params={
                             "symbol": symbol,
                             "interval": "2h",
                             "endTime": int(rounded_add_timestamp),
                             "limit": 1000
                         })

        data = json.loads(r.text)
        df = createHTFDataframe(data)

        collection = db[f"{symbol}_2h"]
        datadict = df.to_dict('records')
        collection.insert_many(datadict)
    except Exception as e:
        print(f"Error -: {symbol}, {e}")


def download_3d_data(symbol):
    try:
        t = datetime.datetime.utcnow()

        rounded = (t - (t - datetime.datetime.min) % datetime.timedelta(days=3)) - datetime.timedelta(days=3)
        rounded = rounded.replace(tzinfo=datetime.timezone.utc)
        rounded_add = rounded + datetime.timedelta(hours=10)
        rounded_add = rounded_add.replace(tzinfo=datetime.timezone.utc)
        rounded_add_timestamp = int(rounded_add.timestamp() * 1000)

        r = requests.get('https://api.binance.com/api/v3/klines',
                         params={
                             "symbol": symbol,
                             "interval": "3d",
                             "endTime": int(rounded_add_timestamp),
                             "limit": 1000
                         })

        data = json.loads(r.text)
        df = createHTFDataframe(data)

        collection = db[f"{symbol}_3d"]
        datadict = df.to_dict('records')
        collection.insert_many(datadict)
    except Exception as e:
        print(f"Error -: {symbol}, {e}")


def download_4h_data(symbol):
    try:
        t = datetime.datetime.utcnow()

        rounded = (t - (t - datetime.datetime.min) % datetime.timedelta(hours=4)) - datetime.timedelta(hours=4)
        rounded = rounded.replace(tzinfo=datetime.timezone.utc)
        rounded_add = rounded + datetime.timedelta(hours=6)
        rounded_add = rounded_add.replace(tzinfo=datetime.timezone.utc)
        rounded_add_timestamp = int(rounded_add.timestamp() * 1000)

        r = requests.get('https://api.binance.com/api/v3/klines',
                         params={
                             "symbol": symbol,
                             "interval": "4h",
                             "endTime": int(rounded_add_timestamp),
                             "limit": 1000
                         })

        data = json.loads(r.text)
        df = createHTFDataframe(data)

        collection = db[f"{symbol}_4h"]
        datadict = df.to_dict('records')
        collection.insert_many(datadict)
    except Exception as e:
        print(f"Error -: {symbol}, {e}")


def download_8h_data(symbol):
    try:
        t = datetime.datetime.utcnow()

        rounded = (t - (t - datetime.datetime.min) % datetime.timedelta(hours=8)) - datetime.timedelta(hours=8)
        rounded = rounded.replace(tzinfo=datetime.timezone.utc)
        rounded_add = rounded + datetime.timedelta(hours=10)
        rounded_add = rounded_add.replace(tzinfo=datetime.timezone.utc)
        rounded_add_timestamp = int(rounded_add.timestamp() * 1000)

        r = requests.get('https://api.binance.com/api/v3/klines',
                         params={
                             "symbol": symbol,
                             "interval": "8h",
                             "endTime": int(rounded_add_timestamp),
                             "limit": 1000
                         })

        data = json.loads(r.text)
        df = createHTFDataframe(data)

        collection = db[f"{symbol}_8h"]
        datadict = df.to_dict('records')
        collection.insert_many(datadict)
    except Exception as e:
        print(f"Error -: {symbol}, {e}")


def download_12h_data(symbol):
    try:
        t = datetime.datetime.utcnow()

        rounded = (t - (t - datetime.datetime.min) % datetime.timedelta(hours=12)) - datetime.timedelta(hours=12)
        rounded = rounded.replace(tzinfo=datetime.timezone.utc)
        rounded_add = rounded + datetime.timedelta(hours=10)
        rounded_add = rounded_add.replace(tzinfo=datetime.timezone.utc)
        rounded_add_timestamp = int(rounded_add.timestamp() * 1000)

        r = requests.get('https://api.binance.com/api/v3/klines',
                         params={
                             "symbol": symbol,
                             "interval": "12h",
                             "endTime": int(rounded_add_timestamp),
                             "limit": 1000
                         })

        data = json.loads(r.text)
        df = createHTFDataframe(data)

        collection = db[f"{symbol}_12h"]
        datadict = df.to_dict('records')
        collection.insert_many(datadict)
    except Exception as e:
        print(f"Error -: {symbol}, {e}")


def download_6d_data(symbol):
    agg_dict = {'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'}

    try:
        t = datetime.datetime.utcnow()

        rounded = (t - (t - datetime.datetime.min) % datetime.timedelta(days=3)) - datetime.timedelta(days=3)
        rounded = rounded.replace(tzinfo=datetime.timezone.utc)
        rounded_add = rounded + datetime.timedelta(hours=8)
        rounded_add = rounded_add.replace(tzinfo=datetime.timezone.utc)
        rounded_add_timestamp = int(rounded_add.timestamp() * 1000)

        r = requests.get('https://api.binance.com/api/v3/klines',
                         params={
                             "symbol": symbol,
                             "interval": "3d",
                             "endTime": int(rounded_add_timestamp),
                             "limit": 1000
                         })

        data = json.loads(r.text)
        columns = ['Open_time', 'Open', 'High', 'Low', 'Close', 'Volume',
                   'Close_time', 'quote_asset_volume', 'no_of_trades',
                   'taker_base_vol', 'taker_quote_vol', 'ignore']

        df = pd.DataFrame(data, columns=columns)
        df['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in df['Open_time']]

        df.High = df.High.astype(float)
        df.Close = df.Close.astype(float)
        df.Low = df.Low.astype(float)
        df.Open = df.Open.astype(float)
        df.Volume = df.Volume.astype(float)

        df.set_index('Datetime', inplace=True)

        df.drop(columns=['quote_asset_volume', 'no_of_trades', 'taker_base_vol', 'taker_quote_vol', 'ignore', 'Close_time'], inplace=True)

        newDf = df.resample(f'8640min', origin='start_day').agg(agg_dict)
        newDf["Open_time_datetime"] = newDf.index
        newDf["Close_time_datetime"] = newDf.index.shift(1)
        newDf["_id"] = newDf.index.astype('int64') // 10 ** 9
        newDf["Open_time"] = newDf.Open_time_datetime.astype('int64') // 10 ** 9
        newDf["Close_time"] = newDf.Close_time_datetime.astype('int64') // 10 ** 9

        timeNow = datetime.datetime.now()
        newDf_completed_candle = newDf[newDf["Close_time_datetime"] < timeNow]

        newDf_completed_candle["Open_time_datetime"] = newDf_completed_candle.Open_time_datetime.dt.strftime('%Y-%m-%d %H:%M:%S')
        newDf_completed_candle["Close_time_datetime"] = newDf_completed_candle.Close_time_datetime.dt.strftime('%Y-%m-%d %H:%M:%S')

        collection = db[f"{symbol}_6d"]
        datadict = newDf_completed_candle.to_dict('records')
        if len(datadict) > 0:
            collection.insert_many(datadict)
    except Exception as e:
        print(f"Error -: {symbol}, {e}")


def download_1M_data(symbol):
    try:
        t = datetime.datetime.utcnow()

        rounded = (t - (t - datetime.datetime.min) % datetime.timedelta(weeks=4)) - datetime.timedelta(weeks=4)
        rounded = rounded.replace(tzinfo=datetime.timezone.utc)
        rounded_add = rounded + datetime.timedelta(weeks=5)
        rounded_add = rounded_add.replace(tzinfo=datetime.timezone.utc)
        rounded_add_timestamp = int(rounded_add.timestamp() * 1000)

        r = requests.get('https://api.binance.com/api/v3/klines',
                         params={
                             "symbol": symbol,
                             "interval": "1M",
                             "endTime": int(rounded_add_timestamp),
                             "limit": 1000
                         })

        data = json.loads(r.text)
        df = createHTFDataframe(data)

        collection = db[f"{symbol}_1M"]
        datadict = df.to_dict('records')
        collection.insert_many(datadict)
    except Exception as e:
        print(f"Error -: {symbol}, {e}")


def download_data(symbol, waitTime, drop):
    if drop:
        print("[!] Dropping old database")
        db.drop_collection(f"{symbol}_1h")
        db.drop_collection(f"{symbol}_2h")
        db.drop_collection(f"{symbol}_4h")
        db.drop_collection(f"{symbol}_8h")
        db.drop_collection(f"{symbol}_12h")
        db.drop_collection(f"{symbol}_1d")
        db.drop_collection(f"{symbol}_3d")
        db.drop_collection(f"{symbol}_6d")
        db.drop_collection(f"{symbol}_1M")

    print("[!] Downloading 1h data")
    download_1h_data(symbol)
    time.sleep(waitTime)

    print("[!] Downloading 2h data")
    download_2h_data(symbol)
    time.sleep(waitTime)

    print("[!] Downloading 4h data")
    download_4h_data(symbol)
    time.sleep(waitTime)

    print("[!] Downloading 8h data")
    download_8h_data(symbol)
    time.sleep(waitTime)

    print("[!] Downloading 12h data")
    download_12h_data(symbol)
    time.sleep(waitTime)

    print("[!] Downloading 1d data")
    download_1d_data(symbol)
    time.sleep(waitTime)

    print("[!] Downloading 3d data")
    download_3d_data(symbol)
    time.sleep(waitTime)

    print("[!] Downloading 6d data")
    download_6d_data(symbol)
    time.sleep(waitTime)

    print("[!] Downloading 1M data")
    download_1M_data(symbol)
    time.sleep(waitTime)


def displayLastHTFData(symbol):
    current_utc = datetime.datetime.utcnow()
    print("Current UTC Time -:", current_utc.strftime("%Y-%m-%d %H:%M:%S"))

    timeframes = ["1h", "2h", "4h", "8h", "12h", "1d", "3d", "6d", "1M"]

    for timeframe in timeframes:
        collection = db[f"{symbol}_{timeframe}"]

        past_candles = collection.find().sort([('_id', -1)]).limit(5)
        df = pd.DataFrame(past_candles)

        if timeframe != "6d":
            df['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in df['Open_time']]
        else:
            df['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time)) for time in df['Open_time']]

        df.set_index('Datetime', inplace=True)
        df.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

        df["Till"] = df.index.shift(1, freq=timeframe)

        df = df.dropna()
        df = df.iloc[::-1]

        lastCandleData = df.iloc[-1]

        print(f"Last {timeframe} candle: Open Time - {lastCandleData.name}, Close Time - {lastCandleData['Till']}, Open - {lastCandleData['Open']}, High - {lastCandleData['High']}, Low - {lastCandleData['Low']}, Close - {lastCandleData['Close']}")

        if lastCandleData["Till"] > current_utc:
            print("[!]Error - This Candle should not exists")


def verifyHTFData():
    symbolsCollection = db["pairs"]
    result = symbolsCollection.find({})

    symbols = []
    len = 0
    for r in result:
        if r['marginSymbol'] not in symbols:
            len = len + 1

            symbol = r['marginSymbol']
            print(f"{len})Checking HTF Data of {symbol}")

            displayLastHTFData(symbol)

            symbols.append(symbol)
            time.sleep(1)


def reDownloadHTFData():
    symbolsCollection = db["pairs"]
    result = symbolsCollection.find({})

    symbols = []
    len = 0
    for r in result:
        if r['marginSymbol'] not in symbols:
            len = len + 1

            symbol = r['marginSymbol']
            print(f"{len}){symbol}")

            download_data(symbol, waitTime=0.5, drop=True)

            symbols.append(symbol)


def findNewPairs(createEntry):
    ##Find Symbol that does not exists in HTFPAIR Collection
    symbolsCollection = db["pairs"]
    htfPairCollection = db["htfPairs"]

    htfResult = htfPairCollection.find({})
    symbolResult = symbolsCollection.find({})

    htfPairs = []
    symbols = []

    for r in htfResult:
        htfPairs.append(r['symbol'])

    for r in symbolResult:
        if r['symbol'] not in htfPairs:
            symbols.append(r['marginSymbol'])

            if createEntry:
                data = {
                    "symbol": r['symbol']
                }

                htfPairCollection.insert_one(data)

    print(symbols)


def main():
    symbols = ["BNBUSDT"]
    len = 0
    for symbol in symbols:
        len = len + 1
        print(f"{len}) Downloading {symbol}")

        download_data(symbol=symbol, waitTime=0.5, drop=True)

# download_data(symbol="ADAETH", waitTime=0.5, drop=True)
displayLastHTFData(symbol="PNTBTC")
# verifyHTFData()
# findNewPairs(createEntry=True)

# main()
# reDownloadHTFData()