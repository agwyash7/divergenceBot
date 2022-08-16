import datetime

import requests
from pymongo import MongoClient

dbclient = MongoClient("mongodb://yashMongo:ChachaMongo$123@198.211.110.141:2727/")
db = dbclient["livebot"]
disablePairsCol = db["disablePairs"]

COOLDOWN_LOGS_URL = "https://discord.com/api/webhooks/898326514276368384/HeK0W_z1GDtYU1DCR8jEfVOCQ-59ux2g9C-iBJi-kk6N_95osnLL3Bmr0jKzqCxfXwZw"

pairs = disablePairsCol.find()

for pair in pairs:
    timer = pair["timer"]
    now = datetime.datetime.utcnow()

    if now > timer:
        payload = {
            "username": f"Cooldown V3 Script-:",
            "content": f"Turning off cooldown on {pair['asset']}"
        }

        requests.post(COOLDOWN_LOGS_URL, json=payload)

        disablePairsCol.delete_one({"asset": pair['asset']})
