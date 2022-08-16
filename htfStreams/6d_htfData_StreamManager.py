import datetime
import json

import requests
from pymongo import MongoClient
import pandas as pd

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
pd.options.display.float_format = '{:,.8f}'.format
pd.options.mode.chained_assignment = None

client = MongoClient("mongodb://yashMongo:ChachaMongo$123@198.211.110.141:2727/")
# client = MongoClient("mongodb://localhost:27017/")
db = client["livebot"]

agg_dict = {'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'}


def update_one(symbol):
    collection = db[f"{symbol}_6d"]
    past_candles = collection.find().sort([('_id', -1)]).limit(1)
    df = pd.DataFrame(past_candles)

    lastCloseTime = (df.iloc[0].Close_time) - 10
    # print(lastCloseTime)

    r = requests.get('https://api.binance.com/api/v3/klines',
                     params={
                         "symbol": symbol,
                         "interval": "3d",
                         "startTime": int(lastCloseTime) * 1000,
                         # "limit": 2
                     })
    data = json.loads(r.text)

    columns = ['Open_time',
               'Open', 'High', 'Low', 'Close', 'Volume',
               'Close_time', 'quote_asset_volume', 'no_of_trades',
               'taker_base_vol', 'taker_quote_vol', 'ignore']

    df = pd.DataFrame(data, columns=columns)

    df['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in df['Open_time']]
    df["Close_time"] = [x + 1 for x in df.Close_time]
    df["Open_time_datetime"] = [datetime.datetime.utcfromtimestamp(x / 1000.0).strftime("%Y-%m-%d %H:%M:%S") for x in
                                df.Open_time]
    df["Close_time_datetime"] = [datetime.datetime.utcfromtimestamp(x / 1000.0).strftime("%Y-%m-%d %H:%M:%S") for x in
                                 df.Close_time]

    df.High = df.High.astype(float)
    df.Close = df.Close.astype(float)
    df.Low = df.Low.astype(float)
    df.Open = df.Open.astype(float)
    df.Volume = df.Volume.astype(float)

    df.set_index('Datetime', inplace=True)

    df.drop(columns=['quote_asset_volume', 'no_of_trades', 'taker_base_vol', 'taker_quote_vol', 'ignore', 'Close_time'],
            inplace=True)

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

    # print(newDf_completed_candle)

    datadict = newDf_completed_candle.to_dict('records')
    if len(datadict) > 0:
        print(f"- Updating {symbol}")
        collection.insert_many(datadict)


def main():
    symbolsCollection = db["htfPairs"]
    result = symbolsCollection.find({})

    symbols = []
    len = 0
    for r in result:
        if r['symbol'] not in symbols:
            len = len + 1
            print(f"{len}) Checking {r['symbol']}")
            update_one(r['symbol'].upper())


main()
