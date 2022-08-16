from pprint import pprint

import numpy
import pandas as pd
import pymongo

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
pd.options.display.float_format = '{:,.8f}'.format
pd.options.mode.chained_assignment = None

# myclient = pymongo.MongoClient("mongodb://yashMongo:ChachaMongo$123@198.211.110.141:2727/")
myclient = pymongo.MongoClient("mongodb://localhost:27017/")

mydb = myclient["livebot"]
mycol = mydb["global_settings"]

##Copy One Collection to another
# pipeline = [ {"$match": {}},
#              {"$out": "global_settings_copy"},
# ]
# mydb.pairs.aggregate(pipeline)

xls = pd.ExcelFile('data/livebotDefaults.xlsx')
data = {}


def addGlobalSettings(name):
    df = pd.read_excel(xls, name)
    df = df[["Setting", "Global Default", "Global or Per Coin"]]
    df = df.dropna()

    for index, row in df.iterrows():
        try:
            if row["Global or Per Coin"] == "Global":
                data[row["Setting"]] = row["Global Default"]

        except Exception as e:
            pass
            print(f"Got ERROR -: {e}")


addGlobalSettings("HTF Defaults")
addGlobalSettings("DTF Settings")
addGlobalSettings("Post Close and ReEntry")
addGlobalSettings("Other Settings")

# mycol.insert_one(data)
pprint(data)
