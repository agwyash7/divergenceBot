import time

import pygsheets
import pandas as pd
from datetime import datetime, timezone, timedelta

gc = pygsheets.authorize(service_file='/home/yash/livebot/googleKeys.json')
# gc = pygsheets.authorize(service_file='../googleKeys.json')

def dailyUpdate(sheetName):
    sh = gc.open(sheetName)

    wk1 = sh[0]
    df = pd.DataFrame(wk1.get_all_records())

    totalTrades = df.loc[0, "Value"]
    totalLongTrades = df.loc[1, "Value"]
    totalShortTrades = df.loc[2, "Value"]

    winTrades = df.loc[4, "Value"]
    winLongTrades = df.loc[5, "Value"]
    winShortTrades = df.loc[6, "Value"]

    lossTrades = df.loc[8, "Value"]
    lossLongTrades = df.loc[9, "Value"]
    lossShortTrades = df.loc[10, "Value"]

    btcTrades = df.loc[12, "Value"]
    btcLongTrades = df.loc[13, "Value"]
    btcShortTrades = df.loc[14, "Value"]

    usdtTrades = df.loc[16, "Value"]
    usdtLongTrades = df.loc[17, "Value"]
    usdtShortTrades = df.loc[18, "Value"]

    ethTrades = df.loc[20, "Value"]
    ethLongTrades = df.loc[21, "Value"]
    ethShortTrades = df.loc[22, "Value"]

    btcWinTrades = df.loc[24, "Value"]
    btcLongWinTrades = df.loc[25, "Value"]
    btcShortWinTrades = df.loc[26, "Value"]

    usdtWinTrades = df.loc[28, "Value"]
    usdtLongWinTrades = df.loc[29, "Value"]
    usdtShortWinTrades = df.loc[30, "Value"]

    ethWinTrades = df.loc[32, "Value"]
    ethLongWinTrades = df.loc[33, "Value"]
    ethShortWinTrades = df.loc[34, "Value"]

    currentROISheet = df.loc[36, "Value"]
    currentLongROISheet = df.loc[37, "Value"]
    currentShortROISheet = df.loc[38, "Value"]

    statsDate = datetime.now(timezone.utc) - timedelta(days=1)

    newRow = [
        statsDate.strftime("%Y-%m-%d"),
        totalTrades,
        totalLongTrades,
        totalShortTrades,
        btcTrades,
        btcLongTrades,
        btcShortTrades,
        usdtTrades,
        usdtLongTrades,
        usdtShortTrades,
        ethTrades,
        ethLongTrades,
        ethShortTrades,
        btcWinTrades,
        btcLongWinTrades,
        btcShortWinTrades,
        usdtWinTrades,
        usdtLongWinTrades,
        usdtShortWinTrades,
        ethWinTrades,
        ethLongWinTrades,
        ethShortWinTrades,
        currentROISheet,
        currentLongROISheet,
        currentShortROISheet
    ]

    dailyLog = sh[1]
    cells = dailyLog.get_all_values(include_tailing_empty_rows=False, include_tailing_empty=False, returnas='matrix')
    last_row = len(cells)
    dailyLog.insert_rows(last_row, number=1, values=newRow)

    wk1.update_value(f'B2', 0)
    wk1.update_value(f'B3', 0)
    wk1.update_value(f'B4', 0)

    wk1.update_value(f'B6', 0)
    wk1.update_value(f'B7', 0)
    wk1.update_value(f'B8', 0)

    wk1.update_value(f'B10', 0)
    wk1.update_value(f'B11', 0)
    wk1.update_value(f'B12', 0)

    wk1.update_value(f'B14', 0)
    wk1.update_value(f'B15', 0)
    wk1.update_value(f'B16', 0)

    wk1.update_value(f'B18', 0)
    wk1.update_value(f'B19', 0)
    wk1.update_value(f'B20', 0)

    wk1.update_value(f'B22', 0)
    wk1.update_value(f'B23', 0)
    wk1.update_value(f'B24', 0)

    wk1.update_value(f'B26', 0)
    wk1.update_value(f'B27', 0)
    wk1.update_value(f'B28', 0)

    wk1.update_value(f'B30', 0)
    wk1.update_value(f'B31', 0)
    wk1.update_value(f'B32', 0)

    wk1.update_value(f'B34', 0)
    wk1.update_value(f'B35', 0)
    wk1.update_value(f'B36', 0)

    wk1.update_value(f'B38', 0)
    wk1.update_value(f'B39', 0)
    wk1.update_value(f'B40', 0)


dailyUpdate("Live Bot Log (G1)")
time.sleep(2)
dailyUpdate("Live Bot Log (G2)")
time.sleep(2)
dailyUpdate("Live Bot Log (G3)")
time.sleep(2)
dailyUpdate("Live Bot Log (G4)")
time.sleep(2)
dailyUpdate("Live Bot Log (G5)")
time.sleep(2)
dailyUpdate("Live Bot Log (G6)")

print(f"{datetime.now().date()} - Daily Logs Updated")
