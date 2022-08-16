import sys
from pprint import pprint

import numpy
import pandas as pd
import pymongo

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

myclient = pymongo.MongoClient("mongodb://yashMongo:ChachaMongo$123@198.211.110.141:2727/")
# myclient = pymongo.MongoClient("mongodb://localhost:27017/")

mydb = myclient["livebot"]
mycol = mydb["tests"]

xls = pd.ExcelFile('../bin/livebotDefaults.xlsx')
df = pd.read_excel(xls, 'G3.5')
# df = df.drop(['Total ROI', 'Total Trades', 'Winning Percentage', 'Total ROI / Total no of Trades'], axis=1)
# df = df.drop(['Total ROI', 'Trades', 'Win %', 'Avg ROI/Trade', 'Updated'], axis=1)
df.index = df.index + 2

isActive = False
onlyISO = False

# pprint(df)

for index, row in df.iterrows():
    try:
        if type(row["COIN"]) == str:
            coin = row["COIN"]
            marginSymbol = coin
            symbol = coin.lower()

            if "USDT" in coin:
                coinPair = "USDT"
                baseAsset = coin.replace("USDT", "")
            elif "BTC" in coin:
                coinPair = "BTC"
                baseAsset = coin.replace("BTC", "")
            else:
                coinPair = "ETH"
                baseAsset = coin.replace("ETH", "")

            historicalSymbol = baseAsset + "/" + coinPair

            data = {
                "sheetNo": index,
                "symbol": symbol,
                "historicalSymbol": historicalSymbol,
                "marginSymbol": marginSymbol,
                "coinPair": coinPair,
                "baseAsset": baseAsset,
                "isActive": isActive,
                "onlyISO": onlyISO,
                "logSheet": "G3.5 Latest"
            }

            for col in df.columns:
                data[col] = row[col]

            del data["COIN"]
            # del data["Unnamed: 95"]
            # del data["Unnamed: 96"]

            pprint(len(data))
            # pprint(data)

            mycol.insert_one(data)

            # Updating the data
            # data = {
            #     "isActive": isActive
            # }
            #
            #
            # colfilter = {
            #     'marginSymbol': marginSymbol
            # }
            #
            # newvalues = {"$set": data}
            #
            # mycol.update_one(colfilter, newvalues)

    except Exception as e:
        pass
        print(f"Got ERROR in {row['COIN']} -: {e}")