import datetime

import requests
from pymongo import MongoClient

dbclient = MongoClient("mongodb://yashMongo:ChachaMongo$123@198.211.110.141:2727/")
db = dbclient["livebot"]
disableTradeCol = db["disableTrades"]

COOLDOWN_LOGS_URL = "https://discord.com/api/webhooks/898326514276368384/HeK0W_z1GDtYU1DCR8jEfVOCQ-59ux2g9C-iBJi-kk6N_95osnLL3Bmr0jKzqCxfXwZw"

timerOn = disableTradeCol.find_one()["timerRunning"]

if timerOn == "On":
    timer = disableTradeCol.find_one()["timer"]
    now = datetime.datetime.utcnow()

    if now > timer:
        payload = {
            "username": f"Cooldown Script-:",
            "content": "Turning off cooldown"
        }

        requests.post(COOLDOWN_LOGS_URL, json=payload)

        colfilter = {
                        'settingName': "disabledTrades",
                    }

        newvalues = {"$set":
                         {
                             'timerRunning': "Off",
                             'startBar-Disable': False,
                             'postCloseDivEntry-Disable': False,
                             'postCloseReEntry-Disable': False
                         }
                     }

        disableTradeCol.update_one(colfilter, newvalues)
