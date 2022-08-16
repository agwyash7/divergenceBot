import calendar
import datetime
import json
import os
import math
import sys
from pprint import pprint

import pandas as pd
import numpy as np

import ccxt
import pygsheets
import requests
from binance import Client
from pymongo import MongoClient
from ta.momentum import StochasticOscillator
from ta.trend import CCIIndicator, MACD, EMAIndicator
from ta.volatility import AverageTrueRange

# from config import mainParams as params
from binance.enums import *

from binanceRawClient import BinanceRawClient

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
pd.options.display.float_format = '{:,.8f}'.format
pd.options.mode.chained_assignment = None


def get_change(current, previous):
    if current == previous:
        return 0
    try:
        return (abs(current - previous) / previous) * 100.0
    except ZeroDivisionError:
        return float('inf')


def round_down(decimals, amount):
    return math.floor(amount * 10 ** decimals) / 10 ** decimals


class TradingBot:
    def __init__(self, apiKey, apiSecret, localID, mainFolder_location, gParams, lParams):
        self.gParams = gParams
        self.lParams = lParams

        ###################################
        ##########Binance Client###########
        ###################################

        self.client = Client(apiKey, apiSecret)
        self.rawClient = BinanceRawClient(key=apiKey, secret=apiSecret)

        exchange_id = 'binance'
        exchange_class = getattr(ccxt, exchange_id)
        self.exchange = exchange_class({
            'timeout': 30000,
            'enableRateLimit': False,
        })

        ###################################
        ##########Symbol Info###########
        ###################################
        self.symbol = lParams.get('symbol')
        self.marginSymbol = lParams.get('marginSymbol')
        self.historicalSymbol = lParams.get('historicalSymbol')
        self.coinPair = lParams.get('coinPair')
        self.baseAsset = lParams.get('baseAsset')

        self.tradeType = gParams.get('tradeType')
        self.onlyISO = lParams.get('onlyISO')

        self.symbolInfo = self.client.get_symbol_info(self.marginSymbol)
        self.minQty = [float(_['minQty']) for _ in self.symbolInfo['filters'] if _['filterType'] == 'LOT_SIZE'][0]
        self.minNotional = [float(_['minNotional']) for _ in self.symbolInfo['filters'] if _['filterType'] == 'MIN_NOTIONAL'][0]

        self.step_size = [float(_['stepSize']) for _ in self.symbolInfo['filters'] if _['filterType'] == 'LOT_SIZE'][0]
        self.step_size = '%.8f' % self.step_size
        self.step_size = self.step_size.rstrip('0')
        self.decimals = len(self.step_size.split('.')[1])

        ###################################
        ###########HTF Settings############
        ###################################

        self.minHTFConfirm = gParams.get('minHTFConfirmedRequired')

        self.htf1TimeFrame = lParams.get('htf1TimeFrame')
        self.htf1Method = gParams.get('htf1Method')
        self.htf1MACDfastLength = gParams.get('htf1MACDfastLength')
        self.htf1MACDslowLength = gParams.get('htf1MACDslowLength')
        self.htf1MACDSmoothing = gParams.get('htf1MACDSmoothing')
        self.htf1EMA = gParams.get('htf1EMA')

        self.htf2TimeFrame = lParams.get('htf2TimeFrame')
        self.htf2Method = gParams.get('htf2Method')
        self.htf2MACDfastLength = gParams.get('htf2MACDfastLength')
        self.htf2MACDslowLength = gParams.get('htf2MACDslowLength')
        self.htf2MACDSmoothing = gParams.get('htf2MACDSmoothing')
        self.htf2EMA = gParams.get('htf2EMA')

        self.htf3TimeFrame = lParams.get('htf3TimeFrame')
        self.htf3Method = gParams.get('htf3Method')
        self.htf3MACDfastLength = gParams.get('htf3MACDfastLength')
        self.htf3MACDslowLength = gParams.get('htf3MACDslowLength')
        self.htf3MACDSmoothing = gParams.get('htf3MACDSmoothing')
        self.htf3EMA = gParams.get('htf3EMA')

        self.htf4Button = gParams.get('htf4Button')
        self.htf4TimeFrame = gParams.get('htf4TimeFrame')
        self.htf4Method = "StochK"
        self.htf4StochKOB = lParams.get('htf4StochKOB')
        self.htf4StochKOS = lParams.get('htf4StochKOS')

        self.htf5Button = gParams.get('htf5Button')
        self.htf5TimeFrame = gParams.get('htf5TimeFrame')
        self.htf5Method = "StochK"
        self.htf5StochKOB = lParams.get('htf5StochKOB')
        self.htf5StochKOS = lParams.get('htf5StochKOS')

        self.htf6Button = gParams.get('htf6Button')
        self.htf6TimeFrame = gParams.get('htf6TimeFrame')
        self.htf6Method = "StochK"
        self.htf6StochKOB = lParams.get('htf6StochKOB')
        self.htf6StochKOS = lParams.get('htf6StochKOS')

        self.htf7Button = gParams.get('htf7Button')
        self.htf7TimeFrame = gParams.get('htf7TimeFrame')
        self.htf7Method = "StochK"
        self.htf7StochKOB = lParams.get('htf7StochKOB')
        self.htf7StochKOS = lParams.get('htf7StochKOS')

        self.htf8Button = gParams.get('htf8Button')
        self.htf8TimeFrame = gParams.get('htf8TimeFrame')
        self.htf8Method = "StochK"
        self.htf8StochKOB = lParams.get('htf8StochKOB')
        self.htf8StochKOS = lParams.get('htf8StochKOS')

        self.htf9Button = gParams.get('htf9Button')
        self.htf9TimeFrame = gParams.get('htf9TimeFrame')
        self.htf9Method = "StochK"
        self.htf9StochKOB = lParams.get('htf9StochKOB')
        self.htf9StochKOS = lParams.get('htf9StochKOS')

        ###################################
        ###########LTF Settings############
        ###################################

        self.ltfStochKLength = gParams.get('ltfStochKLength')
        self.ltfCCILength = gParams.get('ltfCCILength')

        self.ltfTimeFrame = lParams.get('ltfTimeFrame')
        self.ltfStochKOB = lParams.get('ltfStochKOB')
        self.ltfStochKOS = lParams.get('ltfStochKOS')
        self.ltfCCILongLimit = lParams.get('ltfCCILongLimit')
        self.ltfCCIShortLimit = lParams.get('ltfCCIShortLimit')

        ###################################
        ###########DTF Settings############
        ###################################

        self.checkDTF = gParams.get('checkDTF')
        self.dtfMinPass = gParams.get('dtfMinPass')

        self.dtfStochKOB = lParams.get('dtfStochKOB')
        self.dtfStochKOS = lParams.get('dtfStochKOS')
        self.dtfCCILongLimit = lParams.get('dtfCCILongLimit')
        self.dtfCCIShortLimit = lParams.get('dtfCCIShortLimit')

        self.checkDTF1 = gParams.get('checkDTF1')
        self.dtf1Timeframe = lParams.get('dtf1Timeframe')
        self.dtf1DivWindow = lParams.get('dtf1DivWindow')
        self.dtf1DivRequired = lParams.get('dtf1DivRequired')
        self.dtf1LastDivStochKOB = lParams.get('dtf1LastDivStochKOB')
        self.dtf1LastDivStochKOS = lParams.get('dtf1LastDivStochKOS')

        self.checkDTF2 = gParams.get('checkDTF2')
        self.dtf2Timeframe = lParams.get('dtf2Timeframe')
        self.dtf2DivWindow = lParams.get('dtf2DivWindow')
        self.dtf2DivRequired = lParams.get('dtf2DivRequired')
        self.dtf2LastDivStochKOB = lParams.get('dtf2LastDivStochKOB')
        self.dtf2LastDivStochKOS = lParams.get('dtf2LastDivStochKOS')

        self.checkDTF3 = gParams.get('checkDTF3')
        self.dtf3Timeframe = lParams.get('dtf3Timeframe')
        self.dtf3DivWindow = lParams.get('dtf3DivWindow')
        self.dtf3DivRequired = lParams.get('dtf3DivRequired')
        self.dtf3LastDivStochKOB = lParams.get('dtf3LastDivStochKOB')
        self.dtf3LastDivStochKOS = lParams.get('dtf3LastDivStochKOS')

        self.checkDTF4 = gParams.get('checkDTF4')
        self.dtf4Timeframe = lParams.get('dtf4Timeframe')
        self.dtf4DivWindow = lParams.get('dtf4DivWindow')
        self.dtf4DivRequired = lParams.get('dtf4DivRequired')
        self.dtf4LastDivStochKOB = lParams.get('dtf4LastDivStochKOB')
        self.dtf4LastDivStochKOS = lParams.get('dtf4LastDivStochKOS')

        self.checkDTF5 = gParams.get('checkDTF5')
        self.dtf5Timeframe = lParams.get('dtf5Timeframe')
        self.dtf5DivWindow = lParams.get('dtf5DivWindow')
        self.dtf5DivRequired = lParams.get('dtf5DivRequired')
        self.dtf5LastDivStochKOB = lParams.get('dtf5LastDivStochKOB')
        self.dtf5LastDivStochKOS = lParams.get('dtf5LastDivStochKOS')

        self.checkDTF6 = gParams.get('checkDTF6')
        self.dtf6Timeframe = lParams.get('dtf6Timeframe')
        self.dtf6DivWindow = lParams.get('dtf6DivWindow')
        self.dtf6DivRequired = lParams.get('dtf6DivRequired')
        self.dtf6LastDivStochKOB = lParams.get('dtf6LastDivStochKOB')
        self.dtf6LastDivStochKOS = lParams.get('dtf6LastDivStochKOS')

        self.checkDTF7 = gParams.get('checkDTF7')
        self.dtf7Timeframe = lParams.get('dtf7Timeframe')
        self.dtf7DivWindow = lParams.get('dtf7DivWindow')
        self.dtf7DivRequired = lParams.get('dtf7DivRequired')
        self.dtf7LastDivStochKOB = lParams.get('dtf7LastDivStochKOB')
        self.dtf7LastDivStochKOS = lParams.get('dtf7LastDivStochKOS')

        self.checkDTF8 = lParams.get('checkDTF8')
        self.dtf8Timeframe = lParams.get('dtf8Timeframe')
        self.dtf8DivWindow = lParams.get('dtf8DivWindow')
        self.dtf8DivRequired = lParams.get('dtf8DivRequired')
        self.dtf8LastDivStochKOB = lParams.get('dtf8LastDivStochKOB')
        self.dtf8LastDivStochKOS = lParams.get('dtf8LastDivStochKOS')

        ###################################
        ############Div Settings###########
        ###################################

        self.divBarWindow = lParams.get('divBarWindow')
        self.divBarRequired = lParams.get('divBarRequired')
        self.searchDivOnly = lParams.get('searchDivOnly')
        self.startBarRecheck = lParams.get('startBarRecheck')
        self.countSameAsDiv = gParams.get('countSameAsDiv')
        self.lastDivStochKOB = lParams.get('lastDivStochKOB')
        self.lastDivStochKOS = lParams.get('lastDivStochKOS')
        self.cancelFailedDivOnLastDivCandle = gParams.get('cancelFailedDivOnLastDivCandle')

        ###################################
        ###########TR Settings#############
        ###################################

        self.dcLevelMultiplier = gParams.get('dcLevelMultiplier')
        self.swingStrength = lParams.get('swingStrength')
        self.targetRecognitionAllowance = lParams.get('targetRecognitionAllowance')
        self.dcLookbackPeriod = gParams.get('dcLookbackPeriod')
        self.dcSwingRedraws = gParams.get('dcSwingRedraws')
        self.dcSetupBarRechecks = lParams.get('dcSetupBarRechecks')
        self.dcCheckTROnLastDivBar = gParams.get('dcCheckTROnLastDivBar')
        self.checkTRIfInside = gParams.get('checkTRIfInside')
        self.checkTRIfDivBarBoth = gParams.get('checkTRIfDivBarBoth')
        self.checkTRIfKeyReversal = gParams.get('checkTRIfKeyReversal')

        ###################################
        #######Entry & Exit Settings#######
        ###################################

        self.entryTickOffset = lParams.get('entryTickOffset')
        self.TSLOffset = gParams.get("TSLOffset")
        self.initialSLOffset = lParams.get("initialSLOffset")
        self.maxSL = 18 ##lParams.get("maxSL")
        self.mainTrailSL = "DTF2" ##lParams.get('trailSL') ##LTF

        self.keepOrderOpen = lParams.get('keepOrderOpen')
        self.alwaysMoveForward = gParams.get('alwaysMoveForward')
        self.forwardIfInside = gParams.get('forwardIfInside')
        self.forwardIfDivBar1BarBack = gParams.get('forwardIfDivBar1BarBack')
        self.forwardIfDivBarBoth = gParams.get('forwardIfDivBarBoth')
        self.forwardIfKeyReversal = gParams.get('forwardIfKeyReversal')
        self.forwardIfLowerHigher = gParams.get('forwardIfLowerHigher')

        self.TSLBars = gParams.get('STLbars')
        self.STLstochKOB = lParams.get('STLstochKOB')
        self.STLstochKOS = lParams.get('STLstochKOS')

        self.slPlaceOrder = "Close"  ##Touch -: If the price is touched, Close -: If Closed above/below it
        self.slTimeframe = "15m"

        self.osl = "LTF" ##LTF -: uses LTF candles for finding osl, ALL -: uses the first dtf passed for osl

        if lParams.get("logSheet") != "Live Bot Log (G1)" \
                and lParams.get("logSheet") != "Live Bot Log (G2)" \
                and lParams.get("logSheet") != "Live Bot Log (G3)" \
                and lParams.get("logSheet") != "Live Bot Log (G4)":
            self.tsl = "ATR" ##ATR -: use ATR for calculating tsl, STOP -: uses 1/2 bar stop for calculating tsl
        else:
            self.tsl = "STOP"

        self.tslAtrPerc = 50

        print(self.tsl)

        ###################################
        ##Post Close ReEntry And DivEntry##
        ###################################

        self.reEntryActive = lParams.get("reEntryActive")
        self.reEntryBars = lParams.get("reEntryBars")
        self.reEntryCycles = gParams.get("reEntryCycles")
        self.reEntryCheckTR = gParams.get("reEntryCheckTR")
        self.reEntryStochFilterShort = lParams.get("reEntryStochFilterShort")
        self.reEntryStochFilterLong = lParams.get("reEntryStochFilterLong")

        self.postCloseActive = lParams.get("postCloseActive")
        self.postCloseCylces = 2
        self.postCloseDivBarWindow = lParams.get("postCloseDivBarWindow")
        self.postCloseDivBarRequired = lParams.get("postCloseDivBarRequired")
        self.postCloseSearchDivOnly = gParams.get('postCloseSearchDivOnly')
        self.postCloseLastDivStochKOB = lParams.get('postCloseLastDivStochKOB')
        self.postCloseLastDivStochKOS = lParams.get('postCloseLastDivStochKOS')

        self.reEntryDCA = 0
        self.postCloseDCA = 2

        ###################################
        #####Position Sizing Settings######
        ###################################

        self.tier1_cross3x = gParams.get('tier1_cross3x')
        self.tier1_3x = gParams.get('tier1_3x')
        self.tier1_5x = gParams.get('tier1_5x')
        self.tier1_10x = gParams.get('tier1_10x')

        self.tier2_cross3x = gParams.get('tier2_cross3x')
        self.tier2_3x = gParams.get('tier2_3x')
        self.tier2_5x = gParams.get('tier2_5x')
        self.tier2_10x = gParams.get('tier2_10x')

        self.tier3_cross3x = gParams.get('tier3_cross3x')
        self.tier3_3x = gParams.get('tier3_3x')
        self.tier3_5x = gParams.get('tier3_5x')
        self.tier3_10x = gParams.get('tier3_10x')

        self.tier4_cross3x = gParams.get('tier4_cross3x')
        self.tier4_3x = gParams.get('tier4_3x')
        self.tier4_5x = gParams.get('tier4_5x')
        self.tier4_10x = gParams.get('tier4_10x')

        self.tier5_cross3x = gParams.get('tier5_cross3x')
        self.tier5_3x = gParams.get('tier5_3x')
        self.tier5_5x = gParams.get('tier5_5x')
        self.tier5_10x = gParams.get('tier5_10x')

        self.wallet_iso10 = gParams.get('wallet_iso10')
        self.wallet_iso5 = gParams.get('wallet_iso5')
        self.wallet_iso3 = gParams.get('wallet_iso3')
        self.wallet_cross3x = gParams.get('wallet_cross3x')
        self.wallet_spot = gParams.get('wallet_spot')

        ###################################
        ###########Other Settings##########
        ###################################

        self.quantityPercentageDown = gParams.get('quantityPercentageDown')
        self.quantityPercentageDownTimes = gParams.get('quantityPercentageDownTimes')
        self.usdtPairWallet = gParams.get('usdtPair')
        self.atrParameter = gParams.get('atrParameter')

        self.mainFolder = mainFolder_location
        self.logSheetName = lParams.get("logSheet")
        self.sheetNo = lParams.get('sheetNo')

        self.disableStartbarTrades = True
        self.disablePostCloseDivEntryTrades = False
        self.disablePostCloseReEntryTrades = False

        ###################################
        #######Current Trade Setting#######
        ###################################

        self.currentStatus = 0
        self.current_order = {}

        self.checkEntryOrderPrice = False
        self.entryFilled = False

        self.checkStoplossOrderPrice = False
        self.stoplossFilled = False

        self.setupBarNo = 0
        self.divCountTillNow = 0
        self.successfulDivCount = 0
        self.orderAlreadyOpenFor = 0
        self.trailSTL = self.TSLBars

        self.dcSetupBarLeft = self.dcSetupBarRechecks

        self.trailSL = lParams.get('trailSL')

        self.reEntryBarsCheckTillNow = 0
        self.reEntryCyclesCheckTillNow = 0

        self.postCloseCheckTillNow = 0
        self.postCloseDivCountTillNow = 0
        self.postCloseSuccessfulDivCount = 0

        self.fakeOrder = False

        ###################################
        #########Database Instance#########
        ###################################

        self.dbclient = MongoClient("mongodb://yashMongo:ChachaMongo$123@198.211.110.141:2727/")
        self.db = self.dbclient["livebot"]

        ###################################
        #############Dataframes############
        ###################################

        self.ltfData = pd.DataFrame(columns=['timestamp', 'Open', 'High', 'Low', 'Close'])

        self.htf1Data = pd.DataFrame(columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
        self.htf2Data = pd.DataFrame(columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
        self.htf3Data = pd.DataFrame(columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
        self.htf4Data = pd.DataFrame(columns=['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume'])
        self.htf5Data = pd.DataFrame(columns=['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume'])
        self.htf6Data = pd.DataFrame(columns=['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume'])
        self.htf7Data = pd.DataFrame(columns=['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume'])
        self.htf8Data = pd.DataFrame(columns=['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume'])
        self.htf9Data = pd.DataFrame(columns=['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume'])

        self.dtf1Data = pd.DataFrame(columns=['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume'])
        self.dtf2Data = pd.DataFrame(columns=['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume'])
        self.dtf3Data = pd.DataFrame(columns=['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume'])
        self.dtf4Data = pd.DataFrame(columns=['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume'])
        self.dtf5Data = pd.DataFrame(columns=['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume'])
        self.dtf6Data = pd.DataFrame(columns=['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume'])
        self.dtf7Data = pd.DataFrame(columns=['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume'])
        self.dtf8Data = pd.DataFrame(columns=['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume'])

        self.swingLow = []
        self.swingHigh = []

        self.swingLowData = []
        self.swingHighData = []

        ###################################
        #######Discord Variables########
        ###################################

        self.BINANCE_LOGS_URL = "https://discord.com/api/webhooks/877113982127857714/cCBKHo_4STpT4mcPp04-LQWMziPyfD-e5xnKacSNXc9F2TpIL7cZnkNdLKDRDZEHmdm1"
        self.SWING_FOUND_LOGS_URL = "https://discord.com/api/webhooks/877144075223068682/tYaZ7u8_8dR19FjasmiefgUPuIjfSDzwXJvhaq8k5YHi_jyYS3kWpc2l857Gbr64liBT"
        self.DIVERGENCE_FAILED_URL = "https://discord.com/api/webhooks/877207043113623623/_p7Fn9ICDSB5eHuKnZtcDKcN6m1_56SN-OeBEtVSv_6O-ZGnXkRMEh_v-ZcJWkONfXkZ"
        self.DIVERGENCE_PASSED_URL = "https://discord.com/api/webhooks/877206861441552384/OxISe3j7IOd7tJ0_ofIKstWlBtrpryadPeERHWHNFC7mfaeV0V9h-edXjZ4oDy2ydJ1p"
        self.TARGET_RECOGNITION_PASSED_URL = "https://discord.com/api/webhooks/877207323280572477/hpA7IJl4Bg3uClUFSAVVQnFT5HuycZ3y2zaFyoxijCkaBMZlpDPn5DaKm11fd2xVzPGj"
        self.TARGET_RECOGNITION_FAILED_URL = "https://discord.com/api/webhooks/877207212823560203/tZ1kgJZq0qIIddnd6KDqB1SL9zLGh15MovwBh9QBBaIearx3BTJgmzEg_fg4_mEdGTl4"
        self.DTF_PASSED_URL = "https://discord.com/api/webhooks/918629356719472652/7YTn_-qKMMitfUiiMiPEMVUp219sqBstJWHYdpGduI5kdszzfOmpfVIoJEJg_LeP5ee4"
        self.DTF_FAILED_URL = "https://discord.com/api/webhooks/918629548071985172/dSO_UwpbuOepy6Ygkz4f1g3XMukqMvixOs_LPBRBl6rHLgO-F-qwPtl9wTeqXgGV1wKz"
        self.ORDER_LOGS_URL = "https://discord.com/api/webhooks/877222079664099350/Ez3MjQrnQwdJvdzuhhk3JONOVIAt21J3qiiMrwveBhaxrM1tNyZt74EBozYsf64BuLWx"
        self.CLEAR_POSITION_URL = "https://discord.com/api/webhooks/877243906268487701/Uv76VGcXu7QkRgTFOwrQ9AgDQ7tnIkeap8_Poa4go59dxMyJ7vOl7QijjQ4f9R2xv7kd"
        self.ERROR_URL = "https://discord.com/api/webhooks/877288202921181245/5SA47NLbwnyo7LS4ucHgiik3tUSYP2N2mLSUjfhT-C0SmAvSBzadd2jN0EOywIM6pHWV"
        self.ENTRY_ORDER_FILLED_URL = "https://discord.com/api/webhooks/877626821762506822/265l8uzCqikqeXr7XRht0zGr0ZTGR_NzmH41SzgUUYsSv1kEBQnu9TaZ8BO-ta3Kp_Z_"
        self.ENTRY_ORDER_PLACED_MOVED_URL = "https://discord.com/api/webhooks/877794754803404801/VnQK7oTa0bT0a4B6YIENVwn3oAN2h3CjL52pOwxmWYKoul_JA9z5IE3cAKLlKweuCeSe"
        self.STOPLOSS_HIT_URL = "https://discord.com/api/webhooks/877795014288236584/RjEdsIFH1tq3ZqK4DrFq1I63ExtKPaCVDHmrcGxEKwzuWXQz5dumd2zJ6l_NAtELeeSi"
        self.ENTRY_ORDER_NOT_TRIGGERED = "https://discord.com/api/webhooks/877803785282531328/WDtOJLcy9Deqt-sQ3nuc9y7imyeZ6BHvFXTlSNqdZ4ZvNpAks70xOMXiybB5AHW0YarN"
        self.ENTRY_ORDER_NOT_PLACED = "https://discord.com/api/webhooks/877806728425652226/B3VvNFG2xrD9_i-5KA8cBxcaVR_LZaGZOzzpMtjO7DFyTX53-mtLbOpp_RFxdNH0sNTn"
        self.COOLDOWN_LOGS_URL = "https://discord.com/api/webhooks/898326514276368384/HeK0W_z1GDtYU1DCR8jEfVOCQ-59ux2g9C-iBJi-kk6N_95osnLL3Bmr0jKzqCxfXwZw"
        self.ACTIVEPAIR_LOGS_URL = "https://discord.com/api/webhooks/923312210015563827/jMOp3r9yyCSzN-fj6YQi1A-7OQu1Pr0VZhT2m1kPrrSry4XQMAZ1o57G1flLuwvMWlEE"


        self.discordUsername = f"{self.marginSymbol}_G{self.logSheetName[-2]}"

        ###################################
        #######Google Sheet Variables######
        ###################################

        gc = pygsheets.authorize(service_file='googleKeys.json')
        self.sh = gc.open(self.logSheetName)

        self.todayStatsSheet = self.sh[0]
        self.dailyLogSheet = self.sh[1]
        self.tradeLogSheet = self.sh[2]
        self.perCoinStatsSheet = self.sh[3]

        self.overallStatsLongSheet = self.sh[4]
        self.overallStatsShortSheet = self.sh[5]
        # overallStatsSheet = self.sh[6]

        self.targetRecognitionSheet = self.sh[7]

        self.cooldownV1StartbarSheet = self.sh[8]
        self.cooldownV1DivEntrySheet = self.sh[9]
        self.cooldownV1ReEntrySheet = self.sh[10]

        self.cooldownV2StartbarSheet = self.sh[11]
        self.cooldownV2DivEntrySheet = self.sh[12]
        self.cooldownV2ReEntrySheet = self.sh[13]

        self.cooldownV3StartbarSheet = self.sh[14]
        self.cooldownV3DivEntrySheet = self.sh[15]
        self.cooldownV3ReEntrySheet = self.sh[16]

        ###################################
        #######Cleaning Old Log Files######
        ###################################

        # if os.path.exists(f"{self.mainFolder}output_{self.symbol}_{self.ltfTimeFrame}_{self.logSheetName[-2]}.txt"):
        #     os.remove(f"{self.mainFolder}output_{self.symbol}_{self.ltfTimeFrame}_{self.logSheetName[-2]}.txt")

        if os.path.exists(f"{self.mainFolder}outputLTFData_{self.symbol}_{self.ltfTimeFrame}_{self.logSheetName[-2]}.txt"):
            os.remove(f"{self.mainFolder}outputLTFData_{self.symbol}_{self.ltfTimeFrame}_{self.logSheetName[-2]}.txt")

        if os.path.exists(f"{self.mainFolder}outputCandleData_{self.symbol}_{self.ltfTimeFrame}_{self.logSheetName[-2]}.txt"):
            os.remove(f"{self.mainFolder}outputCandleData_{self.symbol}_{self.ltfTimeFrame}_{self.logSheetName[-2]}.txt")

        if os.path.exists(f"{self.mainFolder}outputSwingData_{self.symbol}_{self.ltfTimeFrame}_{self.logSheetName[-2]}.txt"):
            os.remove(f"{self.mainFolder}outputSwingData_{self.symbol}_{self.ltfTimeFrame}_{self.logSheetName[-2]}.txt")

        for i in range(1, 9):
            if os.path.exists(f"{self.mainFolder}outputDTF{i}Data_{self.symbol}_{self.ltfTimeFrame}_{self.logSheetName[-2]}.txt"):
                os.remove(f"{self.mainFolder}outputDTF{i}Data_{self.symbol}_{self.ltfTimeFrame}_{self.logSheetName[-2]}.txt")

    def errorLog(self, msg):
        payload = {
            "username": self.discordUsername,
            "content": f"{msg}"
        }

        requests.post(self.ERROR_URL, json=payload)

    def divergenceFailedLog(self, noOfDivergenceFound):
        payload = {
            "username": self.discordUsername,
            "content": f"Divergence Failed -: Found {noOfDivergenceFound} divergence"
        }

        requests.post(self.DIVERGENCE_FAILED_URL, json=payload)

    def divergencePassedLog(self):
        payload = {
            "username": self.discordUsername,
            "content": f"Divergence Test Passed"
        }

        requests.post(self.DIVERGENCE_PASSED_URL, json=payload)

    def targetRecognitionPassedLog(self):
        payload = {
            "username": self.discordUsername,
            "content": f"Target Recognition Test Passed"
        }

        requests.post(self.TARGET_RECOGNITION_PASSED_URL, json=payload)

    def targetRecognitionFailedLog(self):
        payload = {
            "username": self.discordUsername,
            "content": f"Target Recognition Test Failed"
        }

        requests.post(self.TARGET_RECOGNITION_FAILED_URL, json=payload)

    def dtfPassedLog(self):
        payload = {
            "username": self.discordUsername,
            "content": f"DTF Test Passed"
        }

        requests.post(self.DTF_PASSED_URL, json=payload)

    def dtfFailedLog(self):
        payload = {
            "username": self.discordUsername,
            "content": f"DTF Test Failed"
        }

        requests.post(self.DTF_FAILED_URL, json=payload)

    def swingFoundLog(self, skk):
        payload = {
            "username": self.discordUsername,
            "content": skk
        }

        requests.post(self.SWING_FOUND_LOGS_URL, json=payload)

    def orderLogs(self, skk):
        payload = {
            "username": self.discordUsername,
            "content": skk
        }

        requests.post(self.ORDER_LOGS_URL, json=payload)

    def cross3xTradeCancelledDueToBorrowLimitLog(self):
        if self.current_order["TYPE"] == "LONG":
            borrowLimit = str(self.current_order["MAX_BORROW_LIMIT_COINPAIR"])
            required = str(float(float(self.current_order["ENTRYORDER_PRICE"]) * float(self.current_order["AMOUNT"])))
        else:
            borrowLimit = str(self.current_order["MAX_BORROW_LIMIT_ASSET"])
            required = str(self.current_order["AMOUNT"])

        embeds = [
            {
                "title": "Borrow Limit less then required",
                "fields": [
                    {
                        "name": "Wallet",
                        "value": "Cross 3x",
                    },
                    {
                        "name": "Trade Type",
                        "value": self.current_order["TYPE"],
                    },
                    {
                        "name": "Amount",
                        "value": str(self.current_order["AMOUNT"]),
                        "inline": True
                    },
                    {
                        "name": "Price",
                        "value": str(self.current_order["ENTRYORDER_PRICE"]),
                        "inline": True
                    },
                    {
                        "name": "Total Price",
                        "value": str(float(float(self.current_order["ENTRYORDER_PRICE"]) * float(self.current_order["AMOUNT"]))),
                        "inline": True
                    },
                    {
                        "name": "Cross Borrow Limit",
                        "value": str(borrowLimit),
                        "inline": True
                    },
                    {
                        "name": "Required",
                        "value": str(required),
                        "inline": True
                    },
                    {
                        "name": "RISK TIER",
                        "value": str(self.current_order["RISK TIER"]),
                        "inline": True
                    },
                    {
                        "name": "RISK PER TRADE RATIO",
                        "value": str(self.current_order["Risk Per Trade Percentage"]),
                        "inline": True
                    },
                    {
                        "name": "RISK PER TRADE",
                        "value": str(self.current_order["Risk Per Trade"]),
                        "inline": True
                    }
                ]
            }
        ]

        payload = {
            "username": self.discordUsername,
            "embeds": embeds
        }

        requests.post(self.ORDER_LOGS_URL, json=payload)
        requests.post(self.ENTRY_ORDER_NOT_PLACED, json=payload)

    def isoTradeCancelledDueToBorrowLimitLog(self):
        if self.current_order["TYPE"] == "LONG":
            trueBorrowLimit = float(self.current_order["MAX_BORROW_LIMIT_COINPAIR"]) / float(self.current_order["TRANSFERRED"])
        else:
            trueBorrowLimit = float(self.current_order["MAX_BORROW_LIMIT_ASSET"]) / (float(self.current_order["TRANSFERRED"]) / float(self.current_order["ENTRYORDER_PRICE"]))

        embeds = [
            {
                "title": "Borrow Limit less then required",
                "fields": [
                    {
                        "name": "Wallet",
                        "value": f"ISO {self.current_order['WALLET']}x",
                    },
                    {
                        "name": "Trade Type",
                        "value": self.current_order["TYPE"],
                    },
                    {
                        "name": "Amount",
                        "value": str(self.current_order["AMOUNT"]),
                        "inline": True
                    },
                    {
                        "name": "Price",
                        "value": str(self.current_order["ENTRYORDER_PRICE"]),
                        "inline": True
                    },
                    {
                        "name": "Total Price",
                        "value": str(float(float(self.current_order["ENTRYORDER_PRICE"]) * float(self.current_order["AMOUNT"]))),
                        "inline": True
                    },
                    {
                        "name": "Wallet Multiplication Ratio",
                        "value": str(self.current_order["WALLET_MULTIPLICATION_RATIO"]),
                        "inline": True
                    },
                    {
                        "name": "Transferred",
                        "value": str(self.current_order["TRANSFERRED"]),
                        "inline": True
                    },
                    {
                        "name": "Coinpair Max Borrow Limit",
                        "value": str(self.current_order["MAX_BORROW_LIMIT_COINPAIR"]),
                        "inline": True
                    },
                    {
                        "name": "Asset Max Borrow Limit",
                        "value": str(self.current_order["MAX_BORROW_LIMIT_ASSET"]),
                        "inline": True
                    },
                    {
                        "name": "True Borrow Limit Ratio",
                        "value": str(trueBorrowLimit),
                        "inline": True
                    },
                    {
                        "name": "RISK TIER",
                        "value": str(self.current_order["RISK TIER"]),
                        "inline": True
                    },
                    {
                        "name": "RISK PER TRADE RATIO",
                        "value": str(self.current_order["Risk Per Trade Percentage"]),
                        "inline": True
                    },
                    {
                        "name": "RISK PER TRADE",
                        "value": str(self.current_order["Risk Per Trade"]),
                        "inline": True
                    }
                ]
            }
        ]

        payload = {
            "username": self.discordUsername,
            "embeds": embeds
        }

        requests.post(self.ORDER_LOGS_URL, json=payload)
        requests.post(self.ENTRY_ORDER_NOT_PLACED, json=payload)

    def insufficientFundInCrossToTransferLog(self, transferred, crossBalance):
        embeds = [
            {
                "title": "Not Sufficient Fund In Cross To Transfer",
                "fields": [
                    {
                        "name": "Wallet",
                        "value": f"ISO {self.current_order['WALLET']}x",
                    },
                    {
                        "name": "Trade Type",
                        "value": self.current_order["TYPE"],
                    },
                    {
                        "name": "Amount",
                        "value": str(self.current_order["AMOUNT"]),
                        "inline": True
                    },
                    {
                        "name": "Price",
                        "value": str(self.current_order["ENTRYORDER_PRICE"]),
                        "inline": True
                    },
                    {
                        "name": "Total Price",
                        "value": str(float(float(self.current_order["ENTRYORDER_PRICE"]) * float(self.current_order["AMOUNT"]))),
                        "inline": True
                    },
                    {
                        "name": "Wallet Multiplication Ratio",
                        "value": str(self.current_order["WALLET_MULTIPLICATION_RATIO"]),
                        "inline": True
                    },
                    {
                        "name": "Transferred Required",
                        "value": str(transferred),
                        "inline": True
                    },
                    {
                        "name": "Cross Balance",
                        "value": str(crossBalance),
                        "inline": True
                    },
                    {
                        "name": "RISK TIER",
                        "value": str(self.current_order["RISK TIER"]),
                        "inline": True
                    },
                    {
                        "name": "RISK PER TRADE RATIO",
                        "value": str(self.current_order["Risk Per Trade Percentage"]),
                        "inline": True
                    },
                    {
                        "name": "RISK PER TRADE",
                        "value": str(self.current_order["Risk Per Trade"]),
                        "inline": True
                    }
                ]
            }
        ]

        payload = {
            "username": self.discordUsername,
            "embeds": embeds
        }

        requests.post(self.ORDER_LOGS_URL, json=payload)
        requests.post(self.ENTRY_ORDER_NOT_PLACED, json=payload)

    def placedOrderLogs(self):
        if self.current_order['WALLET'] != "CROSS 3X":
            if self.current_order["TYPE"] == "LONG":
                trueBorrowLimit = float(self.current_order["MAX_BORROW_LIMIT_COINPAIR"]) / float(self.current_order["TRANSFERRED"])
            else:
                trueBorrowLimit = float(self.current_order["MAX_BORROW_LIMIT_ASSET"]) / (float(self.current_order["TRANSFERRED"]) / float(self.current_order["ENTRYORDER_PRICE"]))

            embeds = [
                {
                    "title": "Entry Order Placed",
                    "fields": [
                        {
                            "name": "Wallet",
                            "value": f"ISO {self.current_order['WALLET']}x",
                        },
                        {
                            "name": "Trade Type",
                            "value": self.current_order["TYPE"],
                        },
                        {
                            "name": "Amount",
                            "value": str(self.current_order["AMOUNT"]),
                            "inline": True
                        },
                        {
                            "name": "Price",
                            "value": str(self.current_order["ENTRYORDER_PRICE"]),
                            "inline": True
                        },
                        {
                            "name": "Total Price",
                            "value": str(float(float(self.current_order["ENTRYORDER_PRICE"]) * float(self.current_order["AMOUNT"]))),
                            "inline": True
                        },
                        {
                            "name": "Wallet Multiplication Ratio",
                            "value": str(self.current_order["WALLET_MULTIPLICATION_RATIO"]),
                            "inline": True
                        },
                        {
                            "name": "Transferred",
                            "value": str(self.current_order["TRANSFERRED"]),
                            "inline": True
                        },
                        {
                            "name": "Coinpair Max Borrow Limit",
                            "value": str(self.current_order["MAX_BORROW_LIMIT_COINPAIR"]),
                            "inline": True
                        },
                        {
                            "name": "Asset Max Borrow Limit",
                            "value": str(self.current_order["MAX_BORROW_LIMIT_ASSET"]),
                            "inline": True
                        },
                        {
                            "name": "True Borrow Limit Ratio",
                            "value": str(trueBorrowLimit),
                            "inline": True
                        },
                        {
                            "name": "RISK TIER",
                            "value": str(self.current_order["RISK TIER"]),
                            "inline": True
                        },
                        {
                            "name": "RISK PER TRADE RATIO",
                            "value": str(self.current_order["Risk Per Trade Percentage"]),
                            "inline": True
                        },
                        {
                            "name": "RISK PER TRADE",
                            "value": str(self.current_order["Risk Per Trade"]),
                            "inline": True
                        }
                    ]
                }
            ]
        else:
            embeds = [
                {
                    "title": "Entry Order Placed",
                    "fields": [
                        {
                            "name": "Wallet",
                            "value": "Cross 3x",
                        },
                        {
                            "name": "Trade Type",
                            "value": self.current_order["TYPE"],
                        },
                        {
                            "name": "Amount",
                            "value": str(self.current_order["AMOUNT"]),
                            "inline": True
                        },
                        {
                            "name": "Price",
                            "value": str(self.current_order["ENTRYORDER_PRICE"]),
                            "inline": True
                        },
                        {
                            "name": "Total Price",
                            "value": str(float(float(self.current_order["ENTRYORDER_PRICE"]) * float(self.current_order["AMOUNT"]))),
                            "inline": True
                        },
                        {
                            "name": "Coinpair Max Borrow Limit",
                            "value": str(self.current_order["MAX_BORROW_LIMIT_COINPAIR"]),
                            "inline": True
                        },
                        {
                            "name": "Asset Max Borrow Limit",
                            "value": str(self.current_order["MAX_BORROW_LIMIT_ASSET"]),
                            "inline": True
                        },
                        {
                            "name": "RISK TIER",
                            "value": str(self.current_order["RISK TIER"]),
                            "inline": True
                        },
                        {
                            "name": "RISK PER TRADE RATIO",
                            "value": str(self.current_order["Risk Per Trade Percentage"]),
                            "inline": True
                        },
                        {
                            "name": "RISK PER TRADE",
                            "value": str(self.current_order["Risk Per Trade"]),
                            "inline": True
                        }
                    ]
                }
            ]

        payload = {
            "username": self.discordUsername,
            "embeds": embeds
        }

        requests.post(self.ORDER_LOGS_URL, json=payload)
        requests.post(self.ENTRY_ORDER_PLACED_MOVED_URL, json=payload)

    def movedOrderLogs(self):
        if self.current_order['WALLET'] != "CROSS 3X":
            if self.current_order["TYPE"] == "LONG":
                trueBorrowLimit = float(self.current_order["MAX_BORROW_LIMIT_COINPAIR"]) / float(self.current_order["TRANSFERRED"])
            else:
                trueBorrowLimit = float(self.current_order["MAX_BORROW_LIMIT_ASSET"]) / (float(self.current_order["TRANSFERRED"]) / float(self.current_order["ENTRYORDER_PRICE"]))

            embeds = [
                {
                    "title": "Entry Order Moved",
                    "fields": [
                        {
                            "name": "Wallet",
                            "value": f"ISO {self.current_order['WALLET']}x",
                        },
                        {
                            "name": "Trade Type",
                            "value": self.current_order["TYPE"],
                        },
                        {
                            "name": "Amount",
                            "value": str(self.current_order["AMOUNT"]),
                            "inline": True
                        },
                        {
                            "name": "Price",
                            "value": str(self.current_order["ENTRYORDER_PRICE"]),
                            "inline": True
                        },
                        {
                            "name": "Total Price",
                            "value": str(float(
                                float(self.current_order["ENTRYORDER_PRICE"]) * float(self.current_order["AMOUNT"]))),
                            "inline": True
                        },
                        {
                            "name": "Wallet Multiplication Ratio",
                            "value": str(self.current_order["WALLET_MULTIPLICATION_RATIO"]),
                            "inline": True
                        },
                        {
                            "name": "Transferred",
                            "value": str(self.current_order["TRANSFERRED"]),
                            "inline": True
                        },
                        {
                            "name": "Coinpair Max Borrow Limit",
                            "value": str(self.current_order["MAX_BORROW_LIMIT_COINPAIR"]),
                            "inline": True
                        },
                        {
                            "name": "Asset Max Borrow Limit",
                            "value": str(self.current_order["MAX_BORROW_LIMIT_ASSET"]),
                            "inline": True
                        },
                        {
                            "name": "True Borrow Limit Ratio",
                            "value": str(trueBorrowLimit),
                            "inline": True
                        },
                        {
                            "name": "RISK TIER",
                            "value": str(self.current_order["RISK TIER"]),
                            "inline": True
                        },
                        {
                            "name": "RISK PER TRADE RATIO",
                            "value": str(self.current_order["Risk Per Trade Percentage"]),
                            "inline": True
                        },
                        {
                            "name": "RISK PER TRADE",
                            "value": str(self.current_order["Risk Per Trade"]),
                            "inline": True
                        }
                    ]
                }
            ]
        else:
            embeds = [
                {
                    "title": "Entry Order Moved",
                    "fields": [
                        {
                            "name": "Wallet",
                            "value": "CROSS 3x",
                        },
                        {
                            "name": "Trade Type",
                            "value": self.current_order["TYPE"],
                        },
                        {
                            "name": "Amount",
                            "value": str(self.current_order["AMOUNT"]),
                            "inline": True
                        },
                        {
                            "name": "Price",
                            "value": str(self.current_order["ENTRYORDER_PRICE"]),
                            "inline": True
                        },
                        {
                            "name": "Total Price",
                            "value": str(float(float(self.current_order["ENTRYORDER_PRICE"]) * float(self.current_order["AMOUNT"]))),
                            "inline": True
                        },
                        {
                            "name": "Coinpair Max Borrow Limit",
                            "value": str(self.current_order["MAX_BORROW_LIMIT_COINPAIR"]),
                            "inline": True
                        },
                        {
                            "name": "Asset Max Borrow Limit",
                            "value": str(self.current_order["MAX_BORROW_LIMIT_ASSET"]),
                            "inline": True
                        },
                        {
                            "name": "RISK TIER",
                            "value": str(self.current_order["RISK TIER"]),
                            "inline": True
                        },
                        {
                            "name": "RISK PER TRADE RATIO",
                            "value": str(self.current_order["Risk Per Trade Percentage"]),
                            "inline": True
                        },
                        {
                            "name": "RISK PER TRADE",
                            "value": str(self.current_order["Risk Per Trade"]),
                            "inline": True
                        }
                    ]
                }
            ]

        payload = {
            "username": self.discordUsername,
            "embeds": embeds
        }

        requests.post(self.ORDER_LOGS_URL, json=payload)
        requests.post(self.ENTRY_ORDER_PLACED_MOVED_URL, json=payload)

    def notTriggeredLogs(self):
        if self.current_order['WALLET'] != "CROSS 3X":
            if self.current_order["TYPE"] == "LONG":
                trueBorrowLimit = float(self.current_order["MAX_BORROW_LIMIT_COINPAIR"]) / float(self.current_order["TRANSFERRED"])
            else:
                trueBorrowLimit = float(self.current_order["MAX_BORROW_LIMIT_ASSET"]) / (float(self.current_order["TRANSFERRED"]) / float(self.current_order["ENTRYORDER_PRICE"]))

            embeds = [
                {
                    "title": "Entry Order not triggered",
                    "fields": [
                        {
                            "name": "Wallet",
                            "value": f"ISO {self.current_order['WALLET']}x",
                            "inline": True
                        },
                        {
                            "name": "Trade Type",
                            "value": self.current_order["TYPE"],
                            "inline": True
                        },
                        {
                            "name": "Amount",
                            "value": str(self.current_order["AMOUNT"]),
                            "inline": True
                        },
                        {
                            "name": "Avg Price",
                            "value": str(self.current_order["ENTRYORDER_PRICE"]),
                            "inline": True
                        },
                        {
                            "name": "Total Price",
                            "value": str(float(float(self.current_order["ENTRYORDER_PRICE"]) * float(self.current_order["AMOUNT"]))),
                            "inline": True
                        },
                        {
                            "name": "Wallet Multiplication Ratio",
                            "value": str(self.current_order["WALLET_MULTIPLICATION_RATIO"]),
                            "inline": True
                        },
                        {
                            "name": "Transferred",
                            "value": str(self.current_order["TRANSFERRED"]),
                            "inline": True
                        },
                        {
                            "name": "Coinpair Max Borrow Limit",
                            "value": str(self.current_order["MAX_BORROW_LIMIT_COINPAIR"]),
                            "inline": True
                        },
                        {
                            "name": "Asset Max Borrow Limit",
                            "value": str(self.current_order["MAX_BORROW_LIMIT_ASSET"]),
                            "inline": True
                        },
                        {
                            "name": "True Borrow Limit Ratio",
                            "value": str(trueBorrowLimit),
                            "inline": True
                        },
                        {
                            "name": "RISK TIER",
                            "value": str(self.current_order["RISK TIER"]),
                            "inline": True
                        },
                        {
                            "name": "RISK PER TRADE RATIO",
                            "value": str(self.current_order["Risk Per Trade Percentage"]),
                            "inline": True
                        },
                        {
                            "name": "RISK PER TRADE",
                            "value": str(self.current_order["Risk Per Trade"]),
                            "inline": True
                        }
                    ]
                }
            ]
        else:
            embeds = [
                {
                    "title": "Entry Order not triggered",
                    "fields": [
                        {
                            "name": "Wallet",
                            "value": "CROSS 3x",
                            "inline": True
                        },
                        {
                            "name": "Trade Type",
                            "value": self.current_order["TYPE"],
                            "inline": True
                        },
                        {
                            "name": "Amount",
                            "value": str(self.current_order["AMOUNT"]),
                            "inline": True
                        },
                        {
                            "name": "Price",
                            "value": str(self.current_order["ENTRYORDER_PRICE"]),
                            "inline": True
                        },
                        {
                            "name": "Coinpair Max Borrow Limit",
                            "value": str(self.current_order["MAX_BORROW_LIMIT_COINPAIR"]),
                            "inline": True
                        },
                        {
                            "name": "Asset Max Borrow Limit",
                            "value": str(self.current_order["MAX_BORROW_LIMIT_ASSET"]),
                            "inline": True
                        },
                        {
                            "name": "RISK TIER",
                            "value": str(self.current_order["RISK TIER"]),
                            "inline": True
                        },
                        {
                            "name": "RISK PER TRADE RATIO",
                            "value": str(self.current_order["Risk Per Trade Percentage"]),
                            "inline": True
                        },
                        {
                            "name": "RISK PER TRADE",
                            "value": str(self.current_order["Risk Per Trade"]),
                            "inline": True
                        }
                    ]
                }
            ]

        payload = {
            "username": self.discordUsername,
            "embeds": embeds
        }

        requests.post(self.ORDER_LOGS_URL, json=payload)
        requests.post(self.ENTRY_ORDER_NOT_TRIGGERED, json=payload)

    def filledOrderLogs(self):
        if self.current_order['WALLET'] != "CROSS 3X":
            if self.current_order["TYPE"] == "LONG":
                trueBorrowLimit = float(self.current_order["MAX_BORROW_LIMIT_COINPAIR"]) / float(self.current_order["TRANSFERRED"])
            else:
                trueBorrowLimit = float(self.current_order["MAX_BORROW_LIMIT_ASSET"]) / (float(self.current_order["TRANSFERRED"]) / float(self.current_order["ENTRYORDER_PRICE"]))

            embeds = [
                {
                    "title": "Entry Order Filled",
                    "fields": [
                        {
                            "name": "Wallet",
                            "value": f"ISO {self.current_order['WALLET']}x",
                            "inline": True
                        },
                        {
                            "name": "Trade Type",
                            "value": self.current_order["TYPE"],
                            "inline": True
                        },
                        {
                            "name": "Entry Time",
                            "value": str(self.current_order["ENTRY_TIME"]),
                            "inline": True
                        },
                        {
                            "name": "Amount",
                            "value": str(self.current_order["AMOUNT"]),
                            "inline": True
                        },
                        {
                            "name": "Avg Price",
                            "value": str(self.current_order["ENTRYORDER_AVG_PRICE"]),
                            "inline": True
                        },
                        {
                            "name": "Total Price",
                            "value": str(float(float(self.current_order["ENTRYORDER_AVG_PRICE"]) * float(self.current_order["AMOUNT"]))),
                            "inline": True
                        },
                        {
                            "name": "Wallet Multiplication Ratio",
                            "value": str(self.current_order["WALLET_MULTIPLICATION_RATIO"]),
                            "inline": True
                        },
                        {
                            "name": "Transferred",
                            "value": str(self.current_order["TRANSFERRED"]),
                            "inline": True
                        },
                        {
                            "name": "Coinpair Max Borrow Limit",
                            "value": str(self.current_order["MAX_BORROW_LIMIT_COINPAIR"]),
                            "inline": True
                        },
                        {
                            "name": "Asset Max Borrow Limit",
                            "value": str(self.current_order["MAX_BORROW_LIMIT_ASSET"]),
                            "inline": True
                        },
                        {
                            "name": "True Borrow Limit Ratio",
                            "value": str(trueBorrowLimit),
                            "inline": True
                        },
                        {
                            "name": "RISK TIER",
                            "value": str(self.current_order["RISK TIER"]),
                            "inline": True
                        },
                        {
                            "name": "RISK PER TRADE RATIO",
                            "value": str(self.current_order["Risk Per Trade Percentage"]),
                            "inline": True
                        },
                        {
                            "name": "RISK PER TRADE",
                            "value": str(self.current_order["Risk Per Trade"]),
                            "inline": True
                        },
                        {
                            "name": "Trail SL",
                            "value": self.trailSL,
                            "inline": True
                        },
                    ]
                }
            ]
        else:
            embeds = [
                {
                    "title": "Entry Order Filled",
                    "fields": [
                        {
                            "name": "Wallet",
                            "value": "CROSS 3x",
                            "inline": True
                        },
                        {
                            "name": "Trade Type",
                            "value": self.current_order["TYPE"],
                            "inline": True
                        },
                        {
                            "name": "Entry Time",
                            "value": str(self.current_order["ENTRY_TIME"]),
                            "inline": True
                        },
                        {
                            "name": "Amount",
                            "value": str(self.current_order["AMOUNT"]),
                            "inline": True
                        },
                        {
                            "name": "Avg Price",
                            "value": str(self.current_order["ENTRYORDER_AVG_PRICE"]),
                            "inline": True
                        },
                        {
                            "name": "Coinpair Max Borrow Limit",
                            "value": str(self.current_order["MAX_BORROW_LIMIT_COINPAIR"]),
                            "inline": True
                        },
                        {
                            "name": "Asset Max Borrow Limit",
                            "value": str(self.current_order["MAX_BORROW_LIMIT_ASSET"]),
                            "inline": True
                        },
                        {
                            "name": "RISK TIER",
                            "value": str(self.current_order["RISK TIER"]),
                            "inline": True
                        },
                        {
                            "name": "RISK PER TRADE RATIO",
                            "value": str(self.current_order["Risk Per Trade Percentage"]),
                            "inline": True
                        },
                        {
                            "name": "RISK PER TRADE",
                            "value": str(self.current_order["Risk Per Trade"]),
                            "inline": True
                        },
                        {
                            "name": "Trail SL",
                            "value": self.trailSL,
                            "inline": True
                        }
                    ]
                }
            ]

        payload = {
            "username": self.discordUsername,
            "embeds": embeds
        }

        requests.post(self.ORDER_LOGS_URL, json=payload)
        requests.post(self.ENTRY_ORDER_FILLED_URL, json=payload)

    def stoplossHitLogs(self):
        if self.current_order['WALLET'] != "CROSS 3X":
            wallet = f"ISO {self.current_order['WALLET']}x"
        else:
            wallet = "CROSS 3x"

        percentROI = 0

        if self.current_order["TYPE"] == "LONG":
            roi = ((float(self.current_order["EXITORDER_AVG_PRICE"]) - float(self.current_order["ENTRYORDER_AVG_PRICE"])) / float(self.current_order["ENTRYORDER_AVG_PRICE"])) * 100

            if self.current_order["TRADE_TYPE"] == "POSTCLOSE DIVENTRY":
                roi = roi * 2
            elif self.current_order["TRADE_TYPE"] == "POSTCLOSE REENTRY":
                roi = roi * 2

            percentROI = roi

            if roi >= 0:
                win = True
            else:
                win = False

            roi = str(roi) + "%"
        else:
            roi = ((float(self.current_order["ENTRYORDER_AVG_PRICE"]) - float(self.current_order["EXITORDER_AVG_PRICE"])) / float(self.current_order["ENTRYORDER_AVG_PRICE"])) * 100

            if self.current_order["TRADE_TYPE"] == "POSTCLOSE DIVENTRY":
                roi = roi * 2
            elif self.current_order["TRADE_TYPE"] == "POSTCLOSE REENTRY":
                roi = roi * 2

            percentROI = roi

            if roi >= 0:
                win = True
            else:
                win = False

            roi = str(roi) + "%"

        embeds = [
            {
                "title": "Stoploss Hit",
                "fields": [
                    {
                        "name": "Wallet",
                        "value": wallet,
                        "inline": True
                    },
                    {
                        "name": "Trade Type",
                        "value": self.current_order["TYPE"],
                        "inline": True
                    },
                    {
                        "name": "Entry Time",
                        "value": str(self.current_order["ENTRY_TIME"]),
                        "inline": True
                    },
                    {
                        "name": "Exit Time",
                        "value": str(self.current_order["EXIT_TIME"]),
                        "inline": True
                    },
                    {
                        "name": "Trail SL",
                        "value": self.trailSL,
                        "inline": True
                    },
                    {
                        "name": "Amount",
                        "value": str(self.current_order["AMOUNT"]),
                        "inline": True
                    },
                    {
                        "name": "Entry Avg Price",
                        "value": str(self.current_order["ENTRYORDER_AVG_PRICE"]),
                        "inline": True
                    },
                    {
                        "name": "Exit Avg Price",
                        "value": str(self.current_order["EXITORDER_AVG_PRICE"]),
                        "inline": True
                    },
                    {
                        "name": "ROI",
                        "value": roi,
                        "inline": True
                    }
                ]
            }
        ]

        if self.current_order["TRADE_TYPE"] == "STARTBAR ENTRY":
            if not win:
                self.disableTradesDueToLoss()

        payload = {
            "username": self.discordUsername,
            "embeds": embeds
        }

        requests.post(self.ORDER_LOGS_URL, json=payload)
        requests.post(self.STOPLOSS_HIT_URL, json=payload)

        if self.current_order["TYPE"] == "LONG":
            long = True
        else:
            long = False

        ###Updating Today's Stats Sheet
        df = pd.DataFrame(self.todayStatsSheet.get_all_records())

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

        self.todayStatsSheet.update_value(f'B2', totalTrades + 1)
        if long:
            self.todayStatsSheet.update_value(f'B3', totalLongTrades + 1)
        else:
            self.todayStatsSheet.update_value(f'B4', totalShortTrades + 1)


        self.todayStatsSheet.update_value(f'B38', currentROISheet + percentROI)
        if long:
            self.todayStatsSheet.update_value(f'B39', currentLongROISheet + percentROI)
        else:
            self.todayStatsSheet.update_value(f'B40', currentShortROISheet + percentROI)

        if win:
            self.todayStatsSheet.update_value(f'B6', winTrades + 1)

            if long:
                self.todayStatsSheet.update_value(f'B7', winLongTrades + 1)
            else:
                self.todayStatsSheet.update_value(f'B8', winShortTrades + 1)
        else:
            self.todayStatsSheet.update_value(f'B10', lossTrades + 1)

            if long:
                self.todayStatsSheet.update_value(f'B11', lossLongTrades + 1)
            else:
                self.todayStatsSheet.update_value(f'B12', lossShortTrades + 1)


        if self.coinPair == "BTC":
            self.todayStatsSheet.update_value(f'B14', btcTrades + 1)
            if long:
                self.todayStatsSheet.update_value(f'B15', btcLongTrades + 1)
            else:
                self.todayStatsSheet.update_value(f'B16', btcShortTrades + 1)


            if win:
                self.todayStatsSheet.update_value(f'B26', btcWinTrades + 1)
                if long:
                    self.todayStatsSheet.update_value(f'B27', btcLongWinTrades + 1)
                else:
                    self.todayStatsSheet.update_value(f'B28', btcShortWinTrades + 1)


        elif self.coinPair == "USDT":
            self.todayStatsSheet.update_value(f'B18', usdtTrades + 1)
            if long:
                self.todayStatsSheet.update_value(f'B19', usdtLongTrades + 1)
            else:
                self.todayStatsSheet.update_value(f'B20', usdtShortTrades + 1)

            if win:
                self.todayStatsSheet.update_value(f'B30', usdtWinTrades + 1)
                if long:
                    self.todayStatsSheet.update_value(f'B31', usdtLongWinTrades + 1)
                else:
                    self.todayStatsSheet.update_value(f'B32', usdtShortWinTrades + 1)
        elif self.coinPair == "ETH":
            self.todayStatsSheet.update_value(f'B22', ethTrades + 1)
            if long:
                self.todayStatsSheet.update_value(f'B23', ethLongTrades + 1)
            else:
                self.todayStatsSheet.update_value(f'B24', ethShortTrades + 1)

            if win:
                self.todayStatsSheet.update_value(f'B34', ethWinTrades + 1)
                if long:
                    self.todayStatsSheet.update_value(f'B35', ethLongWinTrades + 1)
                else:
                    self.todayStatsSheet.update_value(f'B36', ethShortWinTrades + 1)

        ##Updating Per Coin Sheets
        perCoinTotalTrades = int(self.perCoinStatsSheet.get_value(f'B{self.sheetNo}'))
        perCoinWinningTrades = int(self.perCoinStatsSheet.get_value(f'C{self.sheetNo}'))

        self.perCoinStatsSheet.update_value(f'B{self.sheetNo}', perCoinTotalTrades + 1)

        if win:
            self.perCoinStatsSheet.update_value(f'C{self.sheetNo}', perCoinWinningTrades + 1)

        ##Updating Overal Sheets
        if long:
            overallStatsSheet = self.overallStatsLongSheet
        else:
            overallStatsSheet = self.overallStatsShortSheet

        # startBarTotalTrades = int(overallStatsSheet.get_value(f'B3'))
        # startBarWinningTrades = int(overallStatsSheet.get_value(f'F3'))
        startBarBTCTotalTrades = int(overallStatsSheet.get_value(f'C3'))
        startBarBTCWinningTrades = int(overallStatsSheet.get_value(f'G3'))
        startBarUSDTTotalTrades = int(overallStatsSheet.get_value(f'D3'))
        startBarUSDTWinningTrades = int(overallStatsSheet.get_value(f'H3'))
        startBarETHTotalTrades = int(overallStatsSheet.get_value(f'E3'))
        startBarETHWinningTrades = int(overallStatsSheet.get_value(f'I3'))

        # divEntryTotalTrades = int(overallStatsSheet.get_value(f'B4'))
        # divEntryWinningTrades = int(overallStatsSheet.get_value(f'F4'))
        divEntryBTCTotalTrades = int(overallStatsSheet.get_value(f'C4'))
        divEntryBTCWinningTrades = int(overallStatsSheet.get_value(f'G4'))
        divEntryUSDTTotalTrades = int(overallStatsSheet.get_value(f'D4'))
        divEntryUSDTWinningTrades = int(overallStatsSheet.get_value(f'H4'))
        divEntryETHTotalTrades = int(overallStatsSheet.get_value(f'E4'))
        divEntryETHWinningTrades = int(overallStatsSheet.get_value(f'I4'))

        # reEntryTotalTrades = int(overallStatsSheet.get_value(f'B5'))
        # reEntryWinningTrades = int(overallStatsSheet.get_value(f'F5'))
        reEntryBTCTotalTrades = int(overallStatsSheet.get_value(f'C5'))
        reEntryBTCWinningTrades = int(overallStatsSheet.get_value(f'G5'))
        reEntryUSDTTotalTrades = int(overallStatsSheet.get_value(f'D5'))
        reEntryUSDTWinningTrades = int(overallStatsSheet.get_value(f'H5'))
        reEntryETHTotalTrades = int(overallStatsSheet.get_value(f'E5'))
        reEntryETHWinningTrades = int(overallStatsSheet.get_value(f'I5'))

        startBarBTCROI = float(overallStatsSheet.get_value(f'G11'))
        startBarUSDTROI = float(overallStatsSheet.get_value(f'H11'))
        startBarETHROI = float(overallStatsSheet.get_value(f'I11'))

        divEntryBTCROI = float(overallStatsSheet.get_value(f'G12'))
        divEntryUSDTROI = float(overallStatsSheet.get_value(f'H12'))
        divEntryETHROI = float(overallStatsSheet.get_value(f'I12'))

        reEntryBTCROI = float(overallStatsSheet.get_value(f'G13'))
        reEntryUSDTROI = float(overallStatsSheet.get_value(f'H13'))
        reEntryETHROI = float(overallStatsSheet.get_value(f'I13'))

        if self.current_order["TRADE_TYPE"] == "STARTBAR ENTRY":
            if self.coinPair == "BTC":
                overallStatsSheet.update_value(f'C3', startBarBTCTotalTrades + 1)
                overallStatsSheet.update_value(f'G11', startBarBTCROI + percentROI)
                if win:
                    overallStatsSheet.update_value(f'G3', startBarBTCWinningTrades + 1)
            elif self.coinPair == "USDT":
                overallStatsSheet.update_value(f'D3', startBarUSDTTotalTrades + 1)
                overallStatsSheet.update_value(f'H11', startBarUSDTROI + percentROI)
                if win:
                    overallStatsSheet.update_value(f'H3', startBarUSDTWinningTrades + 1)
            elif self.coinPair == "ETH":
                overallStatsSheet.update_value(f'E3', startBarETHTotalTrades + 1)
                overallStatsSheet.update_value(f'I11', startBarETHROI + percentROI)
                if win:
                    overallStatsSheet.update_value(f'I3', startBarETHWinningTrades + 1)

        elif self.current_order["TRADE_TYPE"] == "POSTCLOSE DIVENTRY":
            if self.coinPair == "BTC":
                overallStatsSheet.update_value(f'C4', divEntryBTCTotalTrades + 1)
                overallStatsSheet.update_value(f'G12', divEntryBTCROI + percentROI)
                if win:
                    overallStatsSheet.update_value(f'G4', divEntryBTCWinningTrades + 1)
            elif self.coinPair == "USDT":
                overallStatsSheet.update_value(f'D4', divEntryUSDTTotalTrades + 1)
                overallStatsSheet.update_value(f'H12', divEntryUSDTROI + percentROI)
                if win:
                    overallStatsSheet.update_value(f'H4', divEntryUSDTWinningTrades + 1)
            elif self.coinPair == "ETH":
                overallStatsSheet.update_value(f'E4', divEntryETHTotalTrades + 1)
                overallStatsSheet.update_value(f'I12', divEntryETHROI + percentROI)
                if win:
                    overallStatsSheet.update_value(f'I4', divEntryETHWinningTrades + 1)

        elif self.current_order["TRADE_TYPE"] == "POSTCLOSE REENTRY":
            if self.coinPair == "BTC":
                overallStatsSheet.update_value(f'C5', reEntryBTCTotalTrades + 1)
                overallStatsSheet.update_value(f'G13', reEntryBTCROI + percentROI)
                if win:
                    overallStatsSheet.update_value(f'G5', reEntryBTCWinningTrades + 1)
            elif self.coinPair == "USDT":
                overallStatsSheet.update_value(f'D5', reEntryUSDTTotalTrades + 1)
                overallStatsSheet.update_value(f'H13', reEntryUSDTROI + percentROI)
                if win:
                    overallStatsSheet.update_value(f'H5', reEntryUSDTWinningTrades + 1)
            elif self.coinPair == "ETH":
                overallStatsSheet.update_value(f'E5', reEntryETHTotalTrades + 1)
                overallStatsSheet.update_value(f'I13', reEntryETHROI + percentROI)
                if win:
                    overallStatsSheet.update_value(f'I5', reEntryETHWinningTrades + 1)


        ##Updating Trades Sheet
        newTradeRow = [self.marginSymbol,
                       self.current_order['TYPE'],
                       self.current_order["ENTRY_TIME"],
                       self.current_order["EXIT_TIME"],
                       self.current_order["ENTRYORDER_AVG_PRICE"],
                       self.current_order["EXITORDER_AVG_PRICE"],
                       percentROI,
                       self.trailSL,
                       self.current_order['STARTBAR_TIME'],
                       self.current_order['STARTBAR_STOCH'],
                       self.current_order['STARTBAR_CCI'],
                       self.current_order['STARTBAR_CLOSE'],
                       self.current_order['NO_OF_HTF_CONFIRMATION'],
                       self.current_order['DIVBAR_FOUND'],
                       str(self.current_order["DTF_RESULT"][0]),
                       str(self.current_order["DTF_RESULT"][1]),
                       str(self.current_order["DTF_RESULT"][2]),
                       str(self.current_order["DTF_RESULT"][3]),
                       str(self.current_order["DTF_RESULT"][4]),
                       str(self.current_order["DTF_RESULT"][5]),
                       str(self.current_order["DTF_RESULT"][6]),
                       str(self.current_order["DTF_RESULT"][7])
                       ]

        cells = self.tradeLogSheet.get_all_values(include_tailing_empty_rows=False, include_tailing_empty=False, returnas='matrix')
        last_row = len(cells)
        self.tradeLogSheet.insert_rows(last_row, number=1, values=newTradeRow)

    def log(self, skk):
        with open(f'{self.mainFolder}output_{self.symbol}_{self.ltfTimeFrame}_{self.logSheetName[-2]}.txt', 'a', encoding='utf-8') as f:
            print(f'{self.discordUsername} - {skk}')

            f.write('{}'.format(skk))
            f.write("\n")
            f.flush()

    def discordLog(self, skk):
        payload = {
            "username": self.discordUsername,
            "content": skk
        }

        requests.post(self.BINANCE_LOGS_URL, json=payload)

    def ltfPrint(self, skk):
        with open(f'{self.mainFolder}outputLTFData_{self.symbol}_{self.ltfTimeFrame}_{self.logSheetName[-2]}.txt', 'w', encoding='utf-8') as f:
            f.write('{}'.format(skk))
            f.flush()

    def dtf1Print(self, skk):
        with open(f'{self.mainFolder}outputDTF1Data_{self.symbol}_{self.ltfTimeFrame}_{self.logSheetName[-2]}.txt', 'w', encoding='utf-8') as f:
            f.write('{}'.format(skk))
            f.flush()

    def dtf2Print(self, skk):
        with open(f'{self.mainFolder}outputDTF2Data_{self.symbol}_{self.ltfTimeFrame}_{self.logSheetName[-2]}.txt', 'w', encoding='utf-8') as f:
            f.write('{}'.format(skk))
            f.flush()

    def dtf3Print(self, skk):
        with open(f'{self.mainFolder}outputDTF3Data_{self.symbol}_{self.ltfTimeFrame}_{self.logSheetName[-2]}.txt', 'w', encoding='utf-8') as f:
            f.write('{}'.format(skk))
            f.flush()

    def dtf4Print(self, skk):
        with open(f'{self.mainFolder}outputDTF4Data_{self.symbol}_{self.ltfTimeFrame}_{self.logSheetName[-2]}.txt', 'w', encoding='utf-8') as f:
            f.write('{}'.format(skk))
            f.flush()

    def dtf5Print(self, skk):
        with open(f'{self.mainFolder}outputDTF5Data_{self.symbol}_{self.ltfTimeFrame}_{self.logSheetName[-2]}.txt', 'w', encoding='utf-8') as f:
            f.write('{}'.format(skk))
            f.flush()

    def dtf6Print(self, skk):
        with open(f'{self.mainFolder}outputDTF6Data_{self.symbol}_{self.ltfTimeFrame}_{self.logSheetName[-2]}.txt', 'w', encoding='utf-8') as f:
            f.write('{}'.format(skk))
            f.flush()

    def dtf7Print(self, skk):
        with open(f'{self.mainFolder}outputDTF7Data_{self.symbol}_{self.ltfTimeFrame}_{self.logSheetName[-2]}.txt', 'w', encoding='utf-8') as f:
            f.write('{}'.format(skk))
            f.flush()

    def dtf8Print(self, skk):
        with open(f'{self.mainFolder}outputDTF8Data_{self.symbol}_{self.ltfTimeFrame}_{self.logSheetName[-2]}.txt', 'w', encoding='utf-8') as f:
            f.write('{}'.format(skk))
            f.flush()

    def swingLog(self, skk):
        with open(f'{self.mainFolder}outputSwingData_{self.symbol}_{self.ltfTimeFrame}_{self.logSheetName[-2]}.txt', 'a', encoding='utf-8') as f:
            f.write('{}'.format(skk))
            f.write("\n")
            f.flush()

    def candleLog(self, skk):
        with open(f'{self.mainFolder}outputCandleData_{self.symbol}_{self.ltfTimeFrame}_{self.logSheetName[-2]}.txt', 'a', encoding='utf-8') as f:
            f.write('{}'.format(skk))
            f.write("\n")
            f.flush()

    def htfErrorLog(self, skk, no):
        with open(f'{self.mainFolder}errorHTF{no}_{self.symbol}_{self.ltfTimeFrame}_{self.logSheetName[-2]}.txt', 'a', encoding='utf-8') as f:
            f.write('{}'.format(skk))
            f.flush()

    def preloadCheckSwing(self, df, index, row, swingStrength):
        checkRowIndex = df.index.get_loc(index)
        prevs = df.iloc[(checkRowIndex - swingStrength): checkRowIndex]
        nexts = df.iloc[(checkRowIndex + 1): (checkRowIndex + swingStrength + 1)]

        if len(prevs) > (swingStrength - 1) and len(nexts) > (swingStrength - 1):
            if (prevs["high"] < row["high"]).all() and (nexts["high"] < row["high"]).all():
                self.swingHigh.append(row.name)
                self.swingHighData.append(row['high'])
            elif (prevs["low"] > row["low"]).all() and (nexts["low"] > row["low"]).all():
                self.swingLow.append(row.name)
                self.swingLowData.append(row['low'])

    def preloadSwingData(self):
        from_date = (datetime.date.today() - datetime.timedelta(days=60)).strftime("%Y-%m-%d")
        s_date = datetime.datetime.strptime(from_date, '%Y-%m-%d')
        start_date = int(calendar.timegm(s_date.timetuple()) * 1000 + s_date.microsecond / 1000)

        columns = ['open_time', 'open', 'high', 'low', 'close', 'volume',
                   'close_time', 'quote_asset_volume', 'no_of_trades',
                   'taker_base_vol', 'taker_quote_vol', 'ignore']
        df = pd.DataFrame(columns=columns)

        end_date = datetime.datetime.now(datetime.timezone.utc)
        utc_time = end_date.replace(tzinfo=datetime.timezone.utc)
        utc_timestamp = utc_time.timestamp()

        run = True
        while run:
            r = requests.get('https://api.binance.com/api/v3/klines',
                             params={
                                 "symbol": self.marginSymbol,
                                 "interval": self.ltfTimeFrame,
                                 "startTime": int(start_date),
                                 "limit": 1000
                             })

            data = json.loads(r.text)
            a_series = pd.DataFrame(data, columns=df.columns)
            df = df.append(a_series)

            last_candle_close_time = df.iloc[-1].close_time / 1000.0
            if last_candle_close_time <= utc_timestamp:
                start_date = last_candle_close_time * 1000 + 1
            else:
                run = False

        df.index = [datetime.datetime.utcfromtimestamp(x / 1000.0) for x in df.open_time]

        df.high = df.high.astype(float)
        df.close = df.close.astype(float)
        df.low = df.low.astype(float)
        df.open = df.open.astype(float)
        df.volume = df.volume.astype(float)

        df.drop(df.tail(1).index, inplace=True)

        for index, row in df.iterrows():
            self.preloadCheckSwing(df, index, row, self.swingStrength)

        self.swingLog("Saved Swings")
        self.swingLog(self.swingHigh[-5:])
        self.swingLog(self.swingHighData[-5:])
        self.swingLog(self.swingLow[-5:])
        self.swingLog(self.swingLowData[-5:])

    def downloadData(self, timeframe, limit=20):
        data = self.exchange.fetch_ohlcv(symbol=self.historicalSymbol, timeframe=timeframe, limit=limit)

        df = pd.DataFrame(data, columns=['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume'])

        df['timestamp'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in df['Datetime']]
        df['Open'] = df['Open'].astype(np.float64)
        df['High'] = df['High'].astype(np.float64)
        df['Low'] = df['Low'].astype(np.float64)
        df['Close'] = df['Close'].astype(np.float64)
        df['Volume'] = df['Volume'].astype(np.float64)

        df["Datetime"] = pd.to_datetime(df["timestamp"], format="%Y-%m-%d %H:%M")
        df = df.set_index('Datetime')

        df.drop(columns=["Volume"], inplace=True)
        df.drop(df.tail(1).index, inplace=True)

        return df

    def preloadLTFData(self):
        self.ltfData = self.downloadData(self.ltfTimeFrame)

        self.addIndicatorOnLTF()

        self.ltfPrint(self.ltfData)

    def preloadDTFData(self):
        self.dtf1Data = self.downloadData(self.dtf1Timeframe)
        self.dtf2Data = self.downloadData(self.dtf2Timeframe)
        self.dtf3Data = self.downloadData(self.dtf3Timeframe)
        self.dtf4Data = self.downloadData(self.dtf4Timeframe)
        self.dtf5Data = self.downloadData(self.dtf5Timeframe)
        self.dtf6Data = self.downloadData(self.dtf6Timeframe)
        self.dtf7Data = self.downloadData(self.dtf7Timeframe)
        self.dtf8Data = self.downloadData(self.dtf8Timeframe)

        self.addIndicatorOnDTF1()
        self.addIndicatorOnDTF2()
        self.addIndicatorOnDTF3()
        self.addIndicatorOnDTF4()
        self.addIndicatorOnDTF5()
        self.addIndicatorOnDTF6()
        self.addIndicatorOnDTF7()
        self.addIndicatorOnDTF8()

        self.dtf1Print(self.dtf1Data)
        self.dtf2Print(self.dtf2Data)
        self.dtf3Print(self.dtf3Data)
        self.dtf4Print(self.dtf4Data)
        self.dtf5Print(self.dtf5Data)
        self.dtf6Print(self.dtf6Data)
        self.dtf7Print(self.dtf7Data)
        self.dtf8Print(self.dtf8Data)

    def addIndicatorOnLTF(self):
        stoch_indicator = StochasticOscillator(self.ltfData["High"], self.ltfData["Low"], self.ltfData["Close"], window=self.ltfStochKLength, smooth_window=3)
        self.ltfData["stoch"] = stoch_indicator.stoch_signal()

        cci_indicator = CCIIndicator(self.ltfData["High"], self.ltfData["Low"], self.ltfData["Close"], window=self.ltfCCILength)
        self.ltfData["cci"] = cci_indicator.cci()

        if len(self.ltfData) > self.atrParameter:
            atr_indicator = AverageTrueRange(self.ltfData["High"], self.ltfData["Low"], self.ltfData["Close"], window=self.atrParameter, fillna=True)
            self.ltfData["atr"] = atr_indicator.average_true_range()

        self.ltfData.loc[self.ltfData['Close'] >= self.ltfData['Open'], 'type'] = "GREEN"
        self.ltfData.loc[self.ltfData['Close'] < self.ltfData['Open'], 'type'] = "RED"

    def addIndicatorOnDTF1(self):
        cci_indicator = CCIIndicator(self.dtf1Data["High"], self.dtf1Data["Low"], self.dtf1Data["Close"], window=self.ltfCCILength)
        self.dtf1Data["cci"] = cci_indicator.cci()

        if len(self.dtf1Data) > self.atrParameter:
            atr_indicator = AverageTrueRange(self.dtf1Data["High"], self.dtf1Data["Low"], self.dtf1Data["Close"], window=self.atrParameter, fillna=True)
            self.dtf1Data["atr"] = atr_indicator.average_true_range()

        self.dtf1Data.loc[self.dtf1Data['Close'] >= self.dtf1Data['Open'], 'type'] = "GREEN"
        self.dtf1Data.loc[self.dtf1Data['Close'] < self.dtf1Data['Open'], 'type'] = "RED"

        stoch_indicator = StochasticOscillator(self.dtf1Data["High"], self.dtf1Data["Low"], self.dtf1Data["Close"], window=5, smooth_window=3)
        self.dtf1Data["stoch"] = stoch_indicator.stoch_signal()

    def addIndicatorOnDTF2(self):
        cci_indicator = CCIIndicator(self.dtf2Data["High"], self.dtf2Data["Low"], self.dtf2Data["Close"], window=self.ltfCCILength)
        self.dtf2Data["cci"] = cci_indicator.cci()

        if len(self.dtf2Data) > self.atrParameter:
            atr_indicator = AverageTrueRange(self.dtf2Data["High"], self.dtf2Data["Low"], self.dtf2Data["Close"], window=self.atrParameter, fillna=True)
            self.dtf2Data["atr"] = atr_indicator.average_true_range()

        self.dtf2Data.loc[self.dtf2Data['Close'] >= self.dtf2Data['Open'], 'type'] = "GREEN"
        self.dtf2Data.loc[self.dtf2Data['Close'] < self.dtf2Data['Open'], 'type'] = "RED"

        stoch_indicator = StochasticOscillator(self.dtf2Data["High"], self.dtf2Data["Low"], self.dtf2Data["Close"], window=5, smooth_window=3)
        self.dtf2Data["stoch"] = stoch_indicator.stoch_signal()

    def addIndicatorOnDTF3(self):
        cci_indicator = CCIIndicator(self.dtf3Data["High"], self.dtf3Data["Low"], self.dtf3Data["Close"], window=self.ltfCCILength)
        self.dtf3Data["cci"] = cci_indicator.cci()

        if len(self.dtf3Data) > self.atrParameter:
            atr_indicator = AverageTrueRange(self.dtf3Data["High"], self.dtf3Data["Low"], self.dtf3Data["Close"], window=self.atrParameter, fillna=True)
            self.dtf3Data["atr"] = atr_indicator.average_true_range()

        self.dtf3Data.loc[self.dtf3Data['Close'] >= self.dtf3Data['Open'], 'type'] = "GREEN"
        self.dtf3Data.loc[self.dtf3Data['Close'] < self.dtf3Data['Open'], 'type'] = "RED"

        stoch_indicator = StochasticOscillator(self.dtf3Data["High"], self.dtf3Data["Low"], self.dtf3Data["Close"], window=5, smooth_window=3)
        self.dtf3Data["stoch"] = stoch_indicator.stoch_signal()

    def addIndicatorOnDTF4(self):
        cci_indicator = CCIIndicator(self.dtf4Data["High"], self.dtf4Data["Low"], self.dtf4Data["Close"], window=self.ltfCCILength)
        self.dtf4Data["cci"] = cci_indicator.cci()

        if len(self.dtf4Data) > self.atrParameter:
            atr_indicator = AverageTrueRange(self.dtf4Data["High"], self.dtf4Data["Low"], self.dtf4Data["Close"], window=self.atrParameter, fillna=True)
            self.dtf4Data["atr"] = atr_indicator.average_true_range()

        self.dtf4Data.loc[self.dtf4Data['Close'] >= self.dtf4Data['Open'], 'type'] = "GREEN"
        self.dtf4Data.loc[self.dtf4Data['Close'] < self.dtf4Data['Open'], 'type'] = "RED"

        stoch_indicator = StochasticOscillator(self.dtf4Data["High"], self.dtf4Data["Low"], self.dtf4Data["Close"], window=5, smooth_window=3)
        self.dtf4Data["stoch"] = stoch_indicator.stoch_signal()

    def addIndicatorOnDTF5(self):
        cci_indicator = CCIIndicator(self.dtf5Data["High"], self.dtf5Data["Low"], self.dtf5Data["Close"], window=self.ltfCCILength)
        self.dtf5Data["cci"] = cci_indicator.cci()

        if len(self.dtf5Data) > self.atrParameter:
            atr_indicator = AverageTrueRange(self.dtf5Data["High"], self.dtf5Data["Low"], self.dtf5Data["Close"], window=self.atrParameter, fillna=True)
            self.dtf5Data["atr"] = atr_indicator.average_true_range()

        self.dtf5Data.loc[self.dtf5Data['Close'] >= self.dtf5Data['Open'], 'type'] = "GREEN"
        self.dtf5Data.loc[self.dtf5Data['Close'] < self.dtf5Data['Open'], 'type'] = "RED"

        stoch_indicator = StochasticOscillator(self.dtf5Data["High"], self.dtf5Data["Low"], self.dtf5Data["Close"], window=5, smooth_window=3)
        self.dtf5Data["stoch"] = stoch_indicator.stoch_signal()

    def addIndicatorOnDTF6(self):
        cci_indicator = CCIIndicator(self.dtf6Data["High"], self.dtf6Data["Low"], self.dtf6Data["Close"], window=self.ltfCCILength)
        self.dtf6Data["cci"] = cci_indicator.cci()

        if len(self.dtf6Data) > self.atrParameter:
            atr_indicator = AverageTrueRange(self.dtf6Data["High"], self.dtf6Data["Low"], self.dtf6Data["Close"], window=self.atrParameter, fillna=True)
            self.dtf6Data["atr"] = atr_indicator.average_true_range()

        self.dtf6Data.loc[self.dtf6Data['Close'] >= self.dtf6Data['Open'], 'type'] = "GREEN"
        self.dtf6Data.loc[self.dtf6Data['Close'] < self.dtf6Data['Open'], 'type'] = "RED"

        stoch_indicator = StochasticOscillator(self.dtf6Data["High"], self.dtf6Data["Low"], self.dtf6Data["Close"], window=5, smooth_window=3)
        self.dtf6Data["stoch"] = stoch_indicator.stoch_signal()

    def addIndicatorOnDTF7(self):
        cci_indicator = CCIIndicator(self.dtf7Data["High"], self.dtf7Data["Low"], self.dtf7Data["Close"], window=self.ltfCCILength)
        self.dtf7Data["cci"] = cci_indicator.cci()

        if len(self.dtf7Data) > self.atrParameter:
            atr_indicator = AverageTrueRange(self.dtf7Data["High"], self.dtf7Data["Low"], self.dtf7Data["Close"], window=self.atrParameter, fillna=True)
            self.dtf7Data["atr"] = atr_indicator.average_true_range()

        self.dtf7Data.loc[self.dtf7Data['Close'] >= self.dtf7Data['Open'], 'type'] = "GREEN"
        self.dtf7Data.loc[self.dtf7Data['Close'] < self.dtf7Data['Open'], 'type'] = "RED"

        stoch_indicator = StochasticOscillator(self.dtf7Data["High"], self.dtf7Data["Low"], self.dtf7Data["Close"], window=5, smooth_window=3)
        self.dtf7Data["stoch"] = stoch_indicator.stoch_signal()

    def addIndicatorOnDTF8(self):
        cci_indicator = CCIIndicator(self.dtf8Data["High"], self.dtf8Data["Low"], self.dtf8Data["Close"], window=self.ltfCCILength)
        self.dtf8Data["cci"] = cci_indicator.cci()

        if len(self.dtf8Data) > self.atrParameter:
            atr_indicator = AverageTrueRange(self.dtf8Data["High"], self.dtf8Data["Low"], self.dtf8Data["Close"], window=self.atrParameter, fillna=True)
            self.dtf8Data["atr"] = atr_indicator.average_true_range()

        self.dtf8Data.loc[self.dtf8Data['Close'] >= self.dtf8Data['Open'], 'type'] = "GREEN"
        self.dtf8Data.loc[self.dtf8Data['Close'] < self.dtf8Data['Open'], 'type'] = "RED"

        stoch_indicator = StochasticOscillator(self.dtf8Data["High"], self.dtf8Data["Low"], self.dtf8Data["Close"], window=5, smooth_window=3)
        self.dtf8Data["stoch"] = stoch_indicator.stoch_signal()

    def addCandle(self, utcTime, openPrice, high, low, close):
        if "m" in self.ltfTimeFrame:
            utcTime = datetime.datetime.strptime(utcTime.strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M') - datetime.timedelta(minutes=int(self.ltfTimeFrame.replace("m", "")))
        elif "h" in self.ltfTimeFrame:
            utcTime = datetime.datetime.strptime(utcTime.strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M') - datetime.timedelta(hours=int(self.ltfTimeFrame.replace("h", "")))
        elif "d" in self.ltfTimeFrame:
            utcTime = datetime.datetime.strptime(utcTime.strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M') - datetime.timedelta(days=int(self.ltfTimeFrame.replace("d", "")))

        self.candleLog(f"LTF({self.ltfTimeFrame}) Data {utcTime.strftime('%Y-%m-%d %H:%M:%S')} -: Open- {openPrice}, High- {high}, Low- {low}, Close- {close}")

        self.ltfData = self.ltfData.append({
            'timestamp': utcTime.strftime("%Y-%m-%d %H:%M:%S"),
            'Open': float(openPrice),
            'High': float(high),
            'Low': float(low),
            'Close': float(close),
        }, ignore_index=True)

        self.ltfData["Datetime"] = pd.to_datetime(self.ltfData["timestamp"], format="%Y-%m-%d %H:%M")
        self.ltfData = self.ltfData.set_index('Datetime')

        self.addIndicatorOnLTF()

        self.ltfPrint(self.ltfData)

    def addDTF1Candle(self, utcTime, openPrice, high, low, close):
        if "m" in self.dtf1Timeframe:
            utcTime = datetime.datetime.strptime(utcTime.strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M') - datetime.timedelta(minutes=int(self.dtf1Timeframe.replace("m", "")))
        elif "h" in self.dtf1Timeframe:
            utcTime = datetime.datetime.strptime(utcTime.strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M') - datetime.timedelta(hours=int(self.dtf1Timeframe.replace("h", "")))
        elif "d" in self.dtf1Timeframe:
            utcTime = datetime.datetime.strptime(utcTime.strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M') - datetime.timedelta(days=int(self.dtf1Timeframe.replace("d", "")))

        self.candleLog(f"DTF1({self.dtf1Timeframe}) Data {utcTime.strftime('%Y-%m-%d %H:%M:%S')} -: Open- {openPrice}, High- {high}, Low- {low}, Close- {close}")

        self.dtf1Data = self.dtf1Data.append({
            'timestamp': utcTime.strftime("%Y-%m-%d %H:%M:%S"),
            'Open': float(openPrice),
            'High': float(high),
            'Low': float(low),
            'Close': float(close),
        }, ignore_index=True)

        self.dtf1Data["Datetime"] = pd.to_datetime(self.dtf1Data["timestamp"], format="%Y-%m-%d %H:%M")
        self.dtf1Data = self.dtf1Data.set_index('Datetime')

        self.addIndicatorOnDTF1()

        self.dtf1Print(self.dtf1Data)

    def addDTF2Candle(self, utcTime, openPrice, high, low, close):
        if "m" in self.dtf2Timeframe:
            utcTime = datetime.datetime.strptime(utcTime.strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M') - datetime.timedelta(minutes=int(self.dtf2Timeframe.replace("m", "")))
        elif "h" in self.dtf2Timeframe:
            utcTime = datetime.datetime.strptime(utcTime.strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M') - datetime.timedelta(hours=int(self.dtf2Timeframe.replace("h", "")))
        elif "d" in self.dtf2Timeframe:
            utcTime = datetime.datetime.strptime(utcTime.strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M') - datetime.timedelta(days=int(self.dtf2Timeframe.replace("d", "")))

        self.candleLog(f"DTF2({self.dtf2Timeframe}) Data {utcTime.strftime('%Y-%m-%d %H:%M:%S')} -: Open- {openPrice}, High- {high}, Low- {low}, Close- {close}")

        self.dtf2Data = self.dtf2Data.append({
            'timestamp': utcTime.strftime("%Y-%m-%d %H:%M:%S"),
            'Open': float(openPrice),
            'High': float(high),
            'Low': float(low),
            'Close': float(close),
        }, ignore_index=True)

        self.dtf2Data["Datetime"] = pd.to_datetime(self.dtf2Data["timestamp"], format="%Y-%m-%d %H:%M")
        self.dtf2Data = self.dtf2Data.set_index('Datetime')

        self.addIndicatorOnDTF2()

        self.dtf2Print(self.dtf2Data)

    def addDTF3Candle(self, utcTime, openPrice, high, low, close):
        if "m" in self.dtf3Timeframe:
            utcTime = datetime.datetime.strptime(utcTime.strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M') - datetime.timedelta(minutes=int(self.dtf3Timeframe.replace("m", "")))
        elif "h" in self.dtf3Timeframe:
            utcTime = datetime.datetime.strptime(utcTime.strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M') - datetime.timedelta(hours=int(self.dtf3Timeframe.replace("h", "")))
        elif "d" in self.dtf3Timeframe:
            utcTime = datetime.datetime.strptime(utcTime.strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M') - datetime.timedelta(days=int(self.dtf3Timeframe.replace("d", "")))

        utcTime = datetime.datetime.strptime(utcTime.strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M')

        self.candleLog(f"DTF3({self.dtf3Timeframe}) Data {utcTime.strftime('%Y-%m-%d %H:%M:%S')} -: Open- {openPrice}, High- {high}, Low- {low}, Close- {close}")

        self.dtf3Data = self.dtf3Data.append({
            'timestamp': utcTime.strftime("%Y-%m-%d %H:%M:%S"),
            'Open': float(openPrice),
            'High': float(high),
            'Low': float(low),
            'Close': float(close),
        }, ignore_index=True)

        self.dtf3Data["Datetime"] = pd.to_datetime(self.dtf3Data["timestamp"], format="%Y-%m-%d %H:%M")
        self.dtf3Data = self.dtf3Data.set_index('Datetime')

        self.addIndicatorOnDTF3()

        self.dtf3Print(self.dtf3Data)

    def addDTF4Candle(self, utcTime, openPrice, high, low, close):
        if "m" in self.dtf4Timeframe:
            utcTime = datetime.datetime.strptime(utcTime.strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M') - datetime.timedelta(minutes=int(self.dtf4Timeframe.replace("m", "")))
        elif "h" in self.dtf4Timeframe:
            utcTime = datetime.datetime.strptime(utcTime.strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M') - datetime.timedelta(hours=int(self.dtf4Timeframe.replace("h", "")))
        elif "d" in self.dtf4Timeframe:
            utcTime = datetime.datetime.strptime(utcTime.strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M') - datetime.timedelta(days=int(self.dtf4Timeframe.replace("d", "")))

        utcTime = datetime.datetime.strptime(utcTime.strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M')

        self.candleLog(f"DTF4({self.dtf4Timeframe}) Data {utcTime.strftime('%Y-%m-%d %H:%M:%S')} -: Open- {openPrice}, High- {high}, Low- {low}, Close- {close}")

        self.dtf4Data = self.dtf4Data.append({
            'timestamp': utcTime.strftime("%Y-%m-%d %H:%M:%S"),
            'Open': float(openPrice),
            'High': float(high),
            'Low': float(low),
            'Close': float(close),
        }, ignore_index=True)

        self.dtf4Data["Datetime"] = pd.to_datetime(self.dtf4Data["timestamp"], format="%Y-%m-%d %H:%M")
        self.dtf4Data = self.dtf4Data.set_index('Datetime')

        self.addIndicatorOnDTF4()

        self.dtf4Print(self.dtf4Data)

    def addDTF5Candle(self, utcTime, openPrice, high, low, close):
        if "m" in self.dtf5Timeframe:
            utcTime = datetime.datetime.strptime(utcTime.strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M') - datetime.timedelta(minutes=int(self.dtf5Timeframe.replace("m", "")))
        elif "h" in self.dtf5Timeframe:
            utcTime = datetime.datetime.strptime(utcTime.strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M') - datetime.timedelta(hours=int(self.dtf5Timeframe.replace("h", "")))
        elif "d" in self.dtf5Timeframe:
            utcTime = datetime.datetime.strptime(utcTime.strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M') - datetime.timedelta(days=int(self.dtf5Timeframe.replace("d", "")))

        utcTime = datetime.datetime.strptime(utcTime.strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M')

        self.candleLog(f"DTF5({self.dtf5Timeframe}) Data {utcTime.strftime('%Y-%m-%d %H:%M:%S')} -: Open- {openPrice}, High- {high}, Low- {low}, Close- {close}")

        self.dtf5Data = self.dtf5Data.append({
            'timestamp': utcTime.strftime("%Y-%m-%d %H:%M:%S"),
            'Open': float(openPrice),
            'High': float(high),
            'Low': float(low),
            'Close': float(close),
        }, ignore_index=True)

        self.dtf5Data["Datetime"] = pd.to_datetime(self.dtf5Data["timestamp"], format="%Y-%m-%d %H:%M")
        self.dtf5Data = self.dtf5Data.set_index('Datetime')

        self.addIndicatorOnDTF5()

        self.dtf5Print(self.dtf5Data)

    def addDTF6Candle(self, utcTime, openPrice, high, low, close):
        if "m" in self.dtf6Timeframe:
            utcTime = datetime.datetime.strptime(utcTime.strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M') - datetime.timedelta(minutes=int(self.dtf6Timeframe.replace("m", "")))
        elif "h" in self.dtf6Timeframe:
            utcTime = datetime.datetime.strptime(utcTime.strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M') - datetime.timedelta(hours=int(self.dtf6Timeframe.replace("h", "")))
        elif "d" in self.dtf6Timeframe:
            utcTime = datetime.datetime.strptime(utcTime.strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M') - datetime.timedelta(days=int(self.dtf6Timeframe.replace("d", "")))

        utcTime = datetime.datetime.strptime(utcTime.strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M')

        self.candleLog(f"DTF6({self.dtf6Timeframe}) Data {utcTime.strftime('%Y-%m-%d %H:%M:%S')} -: Open- {openPrice}, High- {high}, Low- {low}, Close- {close}")

        self.dtf6Data = self.dtf6Data.append({
            'timestamp': utcTime.strftime("%Y-%m-%d %H:%M:%S"),
            'Open': float(openPrice),
            'High': float(high),
            'Low': float(low),
            'Close': float(close),
        }, ignore_index=True)

        self.dtf6Data["Datetime"] = pd.to_datetime(self.dtf6Data["timestamp"], format="%Y-%m-%d %H:%M")
        self.dtf6Data = self.dtf6Data.set_index('Datetime')

        self.addIndicatorOnDTF6()

        self.dtf6Print(self.dtf6Data)

    def addDTF7Candle(self, utcTime, openPrice, high, low, close):
        if "m" in self.dtf7Timeframe:
            utcTime = datetime.datetime.strptime(utcTime.strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M') - datetime.timedelta(minutes=int(self.dtf7Timeframe.replace("m", "")))
        elif "h" in self.dtf7Timeframe:
            utcTime = datetime.datetime.strptime(utcTime.strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M') - datetime.timedelta(hours=int(self.dtf7Timeframe.replace("h", "")))
        elif "d" in self.dtf7Timeframe:
            utcTime = datetime.datetime.strptime(utcTime.strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M') - datetime.timedelta(days=int(self.dtf7Timeframe.replace("d", "")))

        utcTime = datetime.datetime.strptime(utcTime.strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M')

        self.candleLog(f"DTF7({self.dtf7Timeframe}) Data {utcTime.strftime('%Y-%m-%d %H:%M:%S')} -: Open- {openPrice}, High- {high}, Low- {low}, Close- {close}")

        self.dtf7Data = self.dtf7Data.append({
            'timestamp': utcTime.strftime("%Y-%m-%d %H:%M:%S"),
            'Open': float(openPrice),
            'High': float(high),
            'Low': float(low),
            'Close': float(close),
        }, ignore_index=True)

        self.dtf7Data["Datetime"] = pd.to_datetime(self.dtf7Data["timestamp"], format="%Y-%m-%d %H:%M")
        self.dtf7Data = self.dtf7Data.set_index('Datetime')

        self.addIndicatorOnDTF7()

        self.dtf7Print(self.dtf7Data)

    def addDTF8Candle(self, utcTime, openPrice, high, low, close):
        if "m" in self.dtf8Timeframe:
            utcTime = datetime.datetime.strptime(utcTime.strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M') - datetime.timedelta(minutes=int(self.dtf8Timeframe.replace("m", "")))
        elif "h" in self.dtf8Timeframe:
            utcTime = datetime.datetime.strptime(utcTime.strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M') - datetime.timedelta(hours=int(self.dtf8Timeframe.replace("h", "")))
        elif "d" in self.dtf8Timeframe:
            utcTime = datetime.datetime.strptime(utcTime.strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M') - datetime.timedelta(days=int(self.dtf8Timeframe.replace("d", "")))

        utcTime = datetime.datetime.strptime(utcTime.strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M')

        self.candleLog(f"DTF8({self.dtf8Timeframe}) Data {utcTime.strftime('%Y-%m-%d %H:%M:%S')} -: Open- {openPrice}, High- {high}, Low- {low}, Close- {close}")

        self.dtf8Data = self.dtf8Data.append({
            'timestamp': utcTime.strftime("%Y-%m-%d %H:%M:%S"),
            'Open': float(openPrice),
            'High': float(high),
            'Low': float(low),
            'Close': float(close),
        }, ignore_index=True)

        self.dtf8Data["Datetime"] = pd.to_datetime(self.dtf8Data["timestamp"], format="%Y-%m-%d %H:%M")
        self.dtf8Data = self.dtf8Data.set_index('Datetime')

        self.addIndicatorOnDTF8()

        self.dtf8Print(self.dtf8Data)

    def downloadHTFData(self):
        if self.htf1TimeFrame == "24d":
            collection = self.db[f"{self.marginSymbol}_1M"]

            past_candles = collection.find().sort([('_id', -1)]).limit(25)
            self.htf1Data = pd.DataFrame(past_candles)
            self.htf1Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf1Data['Open_time']]

            self.htf1Data.set_index('Datetime', inplace=True)
            self.htf1Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf1Data["Till"] = self.htf1Data.index.shift(1, freq="1M")
        elif self.htf1TimeFrame == "6d":
            collection = self.db[f"{self.marginSymbol}_6d"]

            past_candles = collection.find().sort([('_id', -1)]).limit(100)
            self.htf1Data = pd.DataFrame(past_candles)
            self.htf1Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time)) for time in self.htf1Data['Open_time']]

            self.htf1Data.set_index('Datetime', inplace=True)
            self.htf1Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf1Data["Till"] = self.htf1Data.index.shift(1, freq="6D")

        self.htf1Data = self.htf1Data.dropna()
        self.htf1Data = self.htf1Data.iloc[::-1]

        if self.htf2TimeFrame == "6d":
            collection = self.db[f"{self.marginSymbol}_6d"]

            past_candles = collection.find().sort([('_id', -1)]).limit(200)
            self.htf2Data = pd.DataFrame(past_candles)
            self.htf2Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time)) for time in self.htf2Data['Open_time']]

            self.htf2Data.set_index('Datetime', inplace=True)
            self.htf2Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf2Data["Till"] = self.htf2Data.index.shift(1, freq="6D")
        elif self.htf2TimeFrame == "1d":
            collection = self.db[f"{self.marginSymbol}_1d"]

            past_candles = collection.find().sort([('_id', -1)]).limit(200)
            self.htf2Data = pd.DataFrame(past_candles)
            self.htf2Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf2Data['Open_time']]

            self.htf2Data.set_index('Datetime', inplace=True)
            self.htf2Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf2Data["Till"] = self.htf2Data.index.shift(1, freq="1D")

        self.htf2Data = self.htf2Data.dropna()
        self.htf2Data = self.htf2Data.iloc[::-1]

        if self.htf3TimeFrame == "1d":
            collection = self.db[f"{self.marginSymbol}_1d"]

            past_candles = collection.find().sort([('_id', -1)]).limit(200)
            self.htf3Data = pd.DataFrame(past_candles)
            self.htf3Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf3Data['Open_time']]

            self.htf3Data.set_index('Datetime', inplace=True)
            self.htf3Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf3Data["Till"] = self.htf3Data.index.shift(1, freq="1D")
        elif self.htf3TimeFrame == "4h":
            collection = self.db[f"{self.marginSymbol}_4h"]

            past_candles = collection.find().sort([('_id', -1)]).limit(300)
            self.htf3Data = pd.DataFrame(past_candles)
            self.htf3Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf3Data['Open_time']]

            self.htf3Data.set_index('Datetime', inplace=True)
            self.htf3Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf3Data["Till"] = self.htf3Data.index.shift(1, freq="4H")

        self.htf3Data = self.htf3Data.dropna()
        self.htf3Data = self.htf3Data.iloc[::-1]

        if self.htf4TimeFrame == "6d":
            collection = self.db[f"{self.marginSymbol}_6d"]

            past_candles = collection.find().sort([('_id', -1)]).limit(200)
            self.htf4Data = pd.DataFrame(past_candles)
            self.htf4Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time)) for time in self.htf4Data['Open_time']]

            self.htf4Data.set_index('Datetime', inplace=True)
            self.htf4Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf4Data["Till"] = self.htf4Data.index.shift(1, freq="6D")
        elif self.htf4TimeFrame == "3d":
            collection = self.db[f"{self.marginSymbol}_3d"]

            past_candles = collection.find().sort([('_id', -1)]).limit(200)
            self.htf4Data = pd.DataFrame(past_candles)
            self.htf4Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf4Data['Open_time']]

            self.htf4Data.set_index('Datetime', inplace=True)
            self.htf4Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf4Data["Till"] = self.htf4Data.index.shift(1, freq="3D")
        elif self.htf4TimeFrame == "1d":
            collection = self.db[f"{self.marginSymbol}_1d"]

            past_candles = collection.find().sort([('_id', -1)]).limit(200)
            self.htf4Data = pd.DataFrame(past_candles)
            self.htf4Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf4Data['Open_time']]

            self.htf4Data.set_index('Datetime', inplace=True)
            self.htf4Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf4Data["Till"] = self.htf4Data.index.shift(1, freq="1D")
        elif self.htf4TimeFrame == "8h":
            collection = self.db[f"{self.marginSymbol}_8h"]

            past_candles = collection.find().sort([('_id', -1)]).limit(200)
            self.htf4Data = pd.DataFrame(past_candles)
            self.htf4Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf4Data['Open_time']]

            self.htf4Data.set_index('Datetime', inplace=True)
            self.htf4Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf4Data["Till"] = self.htf4Data.index.shift(1, freq="8H")
        elif self.htf4TimeFrame == "4h":
            collection = self.db[f"{self.marginSymbol}_4h"]

            past_candles = collection.find().sort([('_id', -1)]).limit(200)
            self.htf4Data = pd.DataFrame(past_candles)
            self.htf4Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf4Data['Open_time']]

            self.htf4Data.set_index('Datetime', inplace=True)
            self.htf4Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf4Data["Till"] = self.htf4Data.index.shift(1, freq="4H")
        elif self.htf4TimeFrame == "2h":
            collection = self.db[f"{self.marginSymbol}_2h"]

            past_candles = collection.find().sort([('_id', -1)]).limit(200)
            self.htf4Data = pd.DataFrame(past_candles)
            self.htf4Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf4Data['Open_time']]

            self.htf4Data.set_index('Datetime', inplace=True)
            self.htf4Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf4Data["Till"] = self.htf4Data.index.shift(1, freq="2H")
        elif self.htf4TimeFrame == "1h":
            collection = self.db[f"{self.marginSymbol}_1h"]

            past_candles = collection.find().sort([('_id', -1)]).limit(200)
            self.htf4Data = pd.DataFrame(past_candles)
            self.htf4Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf4Data['Open_time']]

            self.htf4Data.set_index('Datetime', inplace=True)
            self.htf4Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf4Data["Till"] = self.htf4Data.index.shift(1, freq="1H")

        self.htf4Data = self.htf4Data.dropna()
        self.htf4Data = self.htf4Data.iloc[::-1]

        if self.htf5TimeFrame == "6d":
            collection = self.db[f"{self.marginSymbol}_6d"]

            past_candles = collection.find().sort([('_id', -1)]).limit(200)
            self.htf5Data = pd.DataFrame(past_candles)
            self.htf5Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time)) for time in self.htf5Data['Open_time']]

            self.htf5Data.set_index('Datetime', inplace=True)
            self.htf5Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf5Data["Till"] = self.htf5Data.index.shift(1, freq="6D")
        elif self.htf5TimeFrame == "3d":
            collection = self.db[f"{self.marginSymbol}_3d"]

            past_candles = collection.find().sort([('_id', -1)]).limit(200)
            self.htf5Data = pd.DataFrame(past_candles)
            self.htf5Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf5Data['Open_time']]

            self.htf5Data.set_index('Datetime', inplace=True)
            self.htf5Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf5Data["Till"] = self.htf5Data.index.shift(1, freq="3D")
        elif self.htf5TimeFrame == "1d":
            collection = self.db[f"{self.marginSymbol}_1d"]

            past_candles = collection.find().sort([('_id', -1)]).limit(200)
            self.htf5Data = pd.DataFrame(past_candles)
            self.htf5Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf5Data['Open_time']]

            self.htf5Data.set_index('Datetime', inplace=True)
            self.htf5Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf5Data["Till"] = self.htf5Data.index.shift(1, freq="1D")
        elif self.htf5TimeFrame == "8h":
            collection = self.db[f"{self.marginSymbol}_8h"]

            past_candles = collection.find().sort([('_id', -1)]).limit(200)
            self.htf5Data = pd.DataFrame(past_candles)
            self.htf5Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf5Data['Open_time']]

            self.htf5Data.set_index('Datetime', inplace=True)
            self.htf5Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf5Data["Till"] = self.htf5Data.index.shift(1, freq="8H")
        elif self.htf5TimeFrame == "4h":
            collection = self.db[f"{self.marginSymbol}_4h"]

            past_candles = collection.find().sort([('_id', -1)]).limit(200)
            self.htf5Data = pd.DataFrame(past_candles)
            self.htf5Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf5Data['Open_time']]

            self.htf5Data.set_index('Datetime', inplace=True)
            self.htf5Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf5Data["Till"] = self.htf5Data.index.shift(1, freq="4H")
        elif self.htf5TimeFrame == "2h":
            collection = self.db[f"{self.marginSymbol}_2h"]

            past_candles = collection.find().sort([('_id', -1)]).limit(200)
            self.htf5Data = pd.DataFrame(past_candles)
            self.htf5Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf5Data['Open_time']]

            self.htf5Data.set_index('Datetime', inplace=True)
            self.htf5Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf5Data["Till"] = self.htf5Data.index.shift(1, freq="2H")
        elif self.htf5TimeFrame == "1h":
            collection = self.db[f"{self.marginSymbol}_1h"]

            past_candles = collection.find().sort([('_id', -1)]).limit(200)
            self.htf5Data = pd.DataFrame(past_candles)
            self.htf5Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf5Data['Open_time']]

            self.htf5Data.set_index('Datetime', inplace=True)
            self.htf5Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf5Data["Till"] = self.htf5Data.index.shift(1, freq="1H")

        self.htf5Data = self.htf5Data.dropna()
        self.htf5Data = self.htf5Data.iloc[::-1]

        if self.htf6TimeFrame == "6d":
            collection = self.db[f"{self.marginSymbol}_6d"]

            past_candles = collection.find().sort([('_id', -1)]).limit(200)
            self.htf6Data = pd.DataFrame(past_candles)
            self.htf6Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time)) for time in self.htf6Data['Open_time']]

            self.htf6Data.set_index('Datetime', inplace=True)
            self.htf6Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf6Data["Till"] = self.htf6Data.index.shift(1, freq="6D")
        elif self.htf6TimeFrame == "3d":
            collection = self.db[f"{self.marginSymbol}_3d"]

            past_candles = collection.find().sort([('_id', -1)]).limit(200)
            self.htf6Data = pd.DataFrame(past_candles)
            self.htf6Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf6Data['Open_time']]

            self.htf6Data.set_index('Datetime', inplace=True)
            self.htf6Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf6Data["Till"] = self.htf6Data.index.shift(1, freq="3D")
        elif self.htf6TimeFrame == "1d":
            collection = self.db[f"{self.marginSymbol}_1d"]

            past_candles = collection.find().sort([('_id', -1)]).limit(200)
            self.htf6Data = pd.DataFrame(past_candles)
            self.htf6Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf6Data['Open_time']]

            self.htf6Data.set_index('Datetime', inplace=True)
            self.htf6Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf6Data["Till"] = self.htf6Data.index.shift(1, freq="1D")
        elif self.htf6TimeFrame == "8h":
            collection = self.db[f"{self.marginSymbol}_8h"]

            past_candles = collection.find().sort([('_id', -1)]).limit(200)
            self.htf6Data = pd.DataFrame(past_candles)
            self.htf6Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf6Data['Open_time']]

            self.htf6Data.set_index('Datetime', inplace=True)
            self.htf6Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf6Data["Till"] = self.htf6Data.index.shift(1, freq="8H")
        elif self.htf6TimeFrame == "4h":
            collection = self.db[f"{self.marginSymbol}_4h"]

            past_candles = collection.find().sort([('_id', -1)]).limit(200)
            self.htf6Data = pd.DataFrame(past_candles)
            self.htf6Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf6Data['Open_time']]

            self.htf6Data.set_index('Datetime', inplace=True)
            self.htf6Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf6Data["Till"] = self.htf6Data.index.shift(1, freq="4H")
        elif self.htf6TimeFrame == "2h":
            collection = self.db[f"{self.marginSymbol}_2h"]

            past_candles = collection.find().sort([('_id', -1)]).limit(200)
            self.htf6Data = pd.DataFrame(past_candles)
            self.htf6Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf6Data['Open_time']]

            self.htf6Data.set_index('Datetime', inplace=True)
            self.htf6Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf6Data["Till"] = self.htf6Data.index.shift(1, freq="2H")
        elif self.htf6TimeFrame == "1h":
            collection = self.db[f"{self.marginSymbol}_1h"]

            past_candles = collection.find().sort([('_id', -1)]).limit(200)
            self.htf6Data = pd.DataFrame(past_candles)
            self.htf6Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf6Data['Open_time']]

            self.htf6Data.set_index('Datetime', inplace=True)
            self.htf6Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf6Data["Till"] = self.htf6Data.index.shift(1, freq="1H")

        self.htf6Data = self.htf6Data.dropna()
        self.htf6Data = self.htf6Data.iloc[::-1]

        if self.htf7TimeFrame == "1d":
            collection = self.db[f"{self.marginSymbol}_1d"]

            past_candles = collection.find().sort([('_id', -1)])
            self.htf7Data = pd.DataFrame(past_candles)
            self.htf7Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf7Data['Open_time']]

            self.htf7Data.set_index('Datetime', inplace=True)
            self.htf7Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf7Data["Till"] = self.htf7Data.index.shift(1, freq="1D")
        elif self.htf7TimeFrame == "3d":
            collection = self.db[f"{self.marginSymbol}_3d"]

            past_candles = collection.find().sort([('_id', -1)])
            self.htf7Data = pd.DataFrame(past_candles)
            self.htf7Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf7Data['Open_time']]

            self.htf7Data.set_index('Datetime', inplace=True)
            self.htf7Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf7Data["Till"] = self.htf7Data.index.shift(1, freq="3D")
        elif self.htf7TimeFrame == "6d":
            collection = self.db[f"{self.marginSymbol}_6d"]

            past_candles = collection.find().sort([('_id', -1)])
            self.htf7Data = pd.DataFrame(past_candles)
            self.htf7Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time)) for time in self.htf7Data['Open_time']]

            self.htf7Data.set_index('Datetime', inplace=True)
            self.htf7Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf7Data["Till"] = self.htf7Data.index.shift(1, freq="6D")
        elif self.htf7TimeFrame == "1h":
            collection = self.db[f"{self.marginSymbol}_1h"]

            past_candles = collection.find().sort([('_id', -1)])
            self.htf7Data = pd.DataFrame(past_candles)
            self.htf7Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf7Data['Open_time']]

            self.htf7Data.set_index('Datetime', inplace=True)
            self.htf7Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf7Data["Till"] = self.htf7Data.index.shift(1, freq="1H")
        elif self.htf7TimeFrame == "2h":
            collection = self.db[f"{self.marginSymbol}_2h"]

            past_candles = collection.find().sort([('_id', -1)])
            self.htf7Data = pd.DataFrame(past_candles)
            self.htf7Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf7Data['Open_time']]

            self.htf7Data.set_index('Datetime', inplace=True)
            self.htf7Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf7Data["Till"] = self.htf7Data.index.shift(1, freq="2H")
        elif self.htf7TimeFrame == "4h":
            collection = self.db[f"{self.marginSymbol}_4h"]

            past_candles = collection.find().sort([('_id', -1)])
            self.htf7Data = pd.DataFrame(past_candles)
            self.htf7Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf7Data['Open_time']]

            self.htf7Data.set_index('Datetime', inplace=True)
            self.htf7Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf7Data["Till"] = self.htf7Data.index.shift(1, freq="4H")
        elif self.htf7TimeFrame == "8h":
            collection = self.db[f"{self.marginSymbol}_8h"]

            past_candles = collection.find().sort([('_id', -1)])
            self.htf7Data = pd.DataFrame(past_candles)
            self.htf7Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf7Data['Open_time']]

            self.htf7Data.set_index('Datetime', inplace=True)
            self.htf7Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf7Data["Till"] = self.htf7Data.index.shift(1, freq="8H")
        elif self.htf7TimeFrame == "1M":
            collection = self.db[f"{self.marginSymbol}_1M"]

            past_candles = collection.find().sort([('_id', -1)])
            self.htf7Data = pd.DataFrame(past_candles)
            self.htf7Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf7Data['Open_time']]
            self.htf7Data.set_index('Datetime', inplace=True)
            self.htf7Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)
            self.htf7Data["Till"] = self.htf7Data.index.shift(1, freq="1M")

        if self.htf7TimeFrame != "1M":
            self.htf7Data = self.htf7Data.dropna()

        self.htf7Data = self.htf7Data.iloc[::-1]

        if self.htf8TimeFrame == "1d":
            collection = self.db[f"{self.marginSymbol}_1d"]

            past_candles = collection.find().sort([('_id', -1)])
            self.htf8Data = pd.DataFrame(past_candles)
            self.htf8Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf8Data['Open_time']]

            self.htf8Data.set_index('Datetime', inplace=True)
            self.htf8Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf8Data["Till"] = self.htf8Data.index.shift(1, freq="1D")
        elif self.htf8TimeFrame == "3d":
            collection = self.db[f"{self.marginSymbol}_3d"]

            past_candles = collection.find().sort([('_id', -1)])
            self.htf8Data = pd.DataFrame(past_candles)
            self.htf8Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf8Data['Open_time']]

            self.htf8Data.set_index('Datetime', inplace=True)
            self.htf8Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf8Data["Till"] = self.htf8Data.index.shift(1, freq="3D")
        elif self.htf8TimeFrame == "6d":
            collection = self.db[f"{self.marginSymbol}_6d"]

            past_candles = collection.find().sort([('_id', -1)])
            self.htf8Data = pd.DataFrame(past_candles)
            self.htf8Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time)) for time in self.htf8Data['Open_time']]

            self.htf8Data.set_index('Datetime', inplace=True)
            self.htf8Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf8Data["Till"] = self.htf8Data.index.shift(1, freq="6D")
        elif self.htf8TimeFrame == "1h":
            collection = self.db[f"{self.marginSymbol}_1h"]

            past_candles = collection.find().sort([('_id', -1)])
            self.htf8Data = pd.DataFrame(past_candles)
            self.htf8Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf8Data['Open_time']]

            self.htf8Data.set_index('Datetime', inplace=True)
            self.htf8Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf8Data["Till"] = self.htf8Data.index.shift(1, freq="1H")
        elif self.htf8TimeFrame == "2h":
            collection = self.db[f"{self.marginSymbol}_2h"]

            past_candles = collection.find().sort([('_id', -1)])
            self.htf8Data = pd.DataFrame(past_candles)
            self.htf8Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf8Data['Open_time']]

            self.htf8Data.set_index('Datetime', inplace=True)
            self.htf8Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf8Data["Till"] = self.htf8Data.index.shift(1, freq="2H")
        elif self.htf8TimeFrame == "4h":
            collection = self.db[f"{self.marginSymbol}_4h"]

            past_candles = collection.find().sort([('_id', -1)])
            self.htf8Data = pd.DataFrame(past_candles)
            self.htf8Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf8Data['Open_time']]

            self.htf8Data.set_index('Datetime', inplace=True)
            self.htf8Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf8Data["Till"] = self.htf8Data.index.shift(1, freq="4H")
        elif self.htf8TimeFrame == "8h":
            collection = self.db[f"{self.marginSymbol}_8h"]

            past_candles = collection.find().sort([('_id', -1)])
            self.htf8Data = pd.DataFrame(past_candles)
            self.htf8Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf8Data['Open_time']]

            self.htf8Data.set_index('Datetime', inplace=True)
            self.htf8Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf8Data["Till"] = self.htf8Data.index.shift(1, freq="8H")
        elif self.htf8TimeFrame == "12h":
            collection = self.db[f"{self.marginSymbol}_12h"]

            past_candles = collection.find().sort([('_id', -1)])
            self.htf8Data = pd.DataFrame(past_candles)
            self.htf8Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf8Data['Open_time']]

            self.htf8Data.set_index('Datetime', inplace=True)
            self.htf8Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf8Data["Till"] = self.htf8Data.index.shift(1, freq="12H")
        elif self.htf8TimeFrame == "1M":
            collection = self.db[f"{self.marginSymbol}_1M"]

            past_candles = collection.find().sort([('_id', -1)])
            self.htf8Data = pd.DataFrame(past_candles)
            self.htf8Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf8Data['Open_time']]
            self.htf8Data.set_index('Datetime', inplace=True)
            self.htf8Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)
            self.htf8Data["Till"] = self.htf8Data.index.shift(1, freq="1M")

        if self.htf8TimeFrame != "1M":
            self.htf8Data = self.htf8Data.dropna()

        self.htf8Data = self.htf8Data.iloc[::-1]

        if self.htf9TimeFrame == "1d":
            collection = self.db[f"{self.marginSymbol}_1d"]

            past_candles = collection.find().sort([('_id', -1)])
            self.htf9Data = pd.DataFrame(past_candles)
            self.htf9Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf9Data['Open_time']]

            self.htf9Data.set_index('Datetime', inplace=True)
            self.htf9Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf9Data["Till"] = self.htf9Data.index.shift(1, freq="1D")
        elif self.htf9TimeFrame == "3d":
            collection = self.db[f"{self.marginSymbol}_3d"]

            past_candles = collection.find().sort([('_id', -1)])
            self.htf9Data = pd.DataFrame(past_candles)
            self.htf9Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf9Data['Open_time']]

            self.htf9Data.set_index('Datetime', inplace=True)
            self.htf9Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf9Data["Till"] = self.htf9Data.index.shift(1, freq="3D")
        elif self.htf9TimeFrame == "6d":
            collection = self.db[f"{self.marginSymbol}_6d"]

            past_candles = collection.find().sort([('_id', -1)])
            self.htf9Data = pd.DataFrame(past_candles)
            self.htf9Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time)) for time in self.htf9Data['Open_time']]

            self.htf9Data.set_index('Datetime', inplace=True)
            self.htf9Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf9Data["Till"] = self.htf9Data.index.shift(1, freq="6D")
        elif self.htf9TimeFrame == "1h":
            collection = self.db[f"{self.marginSymbol}_1h"]

            past_candles = collection.find().sort([('_id', -1)])
            self.htf9Data = pd.DataFrame(past_candles)
            self.htf9Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf9Data['Open_time']]

            self.htf9Data.set_index('Datetime', inplace=True)
            self.htf9Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf9Data["Till"] = self.htf9Data.index.shift(1, freq="1H")
        elif self.htf9TimeFrame == "2h":
            collection = self.db[f"{self.marginSymbol}_2h"]

            past_candles = collection.find().sort([('_id', -1)])
            self.htf9Data = pd.DataFrame(past_candles)
            self.htf9Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf9Data['Open_time']]

            self.htf9Data.set_index('Datetime', inplace=True)
            self.htf9Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf9Data["Till"] = self.htf9Data.index.shift(1, freq="2H")
        elif self.htf9TimeFrame == "4h":
            collection = self.db[f"{self.marginSymbol}_4h"]

            past_candles = collection.find().sort([('_id', -1)])
            self.htf9Data = pd.DataFrame(past_candles)
            self.htf9Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf9Data['Open_time']]

            self.htf9Data.set_index('Datetime', inplace=True)
            self.htf9Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf9Data["Till"] = self.htf9Data.index.shift(1, freq="4H")
        elif self.htf9TimeFrame == "8h":
            collection = self.db[f"{self.marginSymbol}_8h"]

            past_candles = collection.find().sort([('_id', -1)])
            self.htf9Data = pd.DataFrame(past_candles)
            self.htf9Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf9Data['Open_time']]

            self.htf9Data.set_index('Datetime', inplace=True)
            self.htf9Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf9Data["Till"] = self.htf9Data.index.shift(1, freq="8H")
        elif self.htf9TimeFrame == "12h":
            collection = self.db[f"{self.marginSymbol}_12h"]

            past_candles = collection.find().sort([('_id', -1)])
            self.htf9Data = pd.DataFrame(past_candles)
            self.htf9Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf9Data['Open_time']]

            self.htf9Data.set_index('Datetime', inplace=True)
            self.htf9Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)

            self.htf9Data["Till"] = self.htf9Data.index.shift(1, freq="12H")
        elif self.htf9TimeFrame == "1M":
            collection = self.db[f"{self.marginSymbol}_1M"]

            past_candles = collection.find().sort([('_id', -1)])
            self.htf9Data = pd.DataFrame(past_candles)
            self.htf9Data['Datetime'] = [datetime.datetime.utcfromtimestamp(float(time) / 1000) for time in self.htf9Data['Open_time']]
            self.htf9Data.set_index('Datetime', inplace=True)
            self.htf9Data.drop(columns=['Open_time', 'Close_time', 'Open_time_datetime', 'Close_time_datetime'], inplace=True)
            self.htf9Data["Till"] = self.htf9Data.index.shift(1, freq="1M")

        if self.htf9TimeFrame != "1M":
            self.htf9Data = self.htf9Data.dropna()

        self.htf9Data = self.htf9Data.iloc[::-1]

    def addIndicatorOnHTF1(self):
        if self.htf1Method == "MACD":
            macd_indicator = MACD(self.htf1Data["Close"], window_fast=self.htf1MACDfastLength, window_slow=self.htf1MACDslowLength, window_sign=self.htf1MACDSmoothing)
            self.htf1Data["macd"] = macd_indicator.macd()
            self.htf1Data["macdsignal"] = macd_indicator.macd_signal()

        if self.htf1Method == "EMA":
            emaData = EMAIndicator(self.htf1Data["Close"], window=self.htf1EMA)
            self.htf1Data['EMA'] = emaData.ema_indicator()

        if self.htf1Method == "Heiken Ashi":
            self.htf1Data['HA_Close'] = (self.htf1Data['Open'] + self.htf1Data['High'] + self.htf1Data['Low'] + self.htf1Data['Close']) / 4
            self.htf1Data['HA_Open'] = (self.htf1Data['Open'].shift(1) + self.htf1Data['Close'].shift(1)) / 2
            self.htf1Data.iloc[0, self.htf1Data.columns.get_loc("HA_Open")] = (self.htf1Data.iloc[0]['Open'] + self.htf1Data.iloc[0]['Close']) / 2
            self.htf1Data['HA_High'] = self.htf1Data[['High', 'Low', 'HA_Open', 'HA_Close']].max(axis=1)
            self.htf1Data['HA_Low'] = self.htf1Data[['High', 'Low', 'HA_Open', 'HA_Close']].min(axis=1)

            self.htf1Data.loc[self.htf1Data['HA_Close'] >= self.htf1Data['HA_Open'], 'type'] = "GREEN"
            self.htf1Data.loc[self.htf1Data['HA_Close'] < self.htf1Data['HA_Open'], 'type'] = "RED"

    def addIndicatorOnHTF2(self):
        if self.htf2Method == "MACD":
            macd_indicator = MACD(self.htf2Data["Close"], window_fast=self.htf2MACDfastLength, window_slow=self.htf2MACDslowLength, window_sign=self.htf2MACDSmoothing)
            self.htf2Data["macd"] = macd_indicator.macd()
            self.htf2Data["macdsignal"] = macd_indicator.macd_signal()

        if self.htf2Method == "EMA":
            emaData = EMAIndicator(self.htf2Data["Close"], window=self.htf2EMA)
            self.htf2Data['EMA'] = emaData.ema_indicator()

        if self.htf2Method == "Heiken Ashi":
            self.htf2Data['HA_Close'] = (self.htf2Data['Open'] + self.htf2Data['High'] + self.htf2Data['Low'] + self.htf2Data['Close']) / 4
            self.htf2Data['HA_Open'] = (self.htf2Data['Open'].shift(1) + self.htf2Data['Close'].shift(1)) / 2
            self.htf2Data.iloc[0, self.htf2Data.columns.get_loc("HA_Open")] = (self.htf2Data.iloc[0]['Open'] + self.htf2Data.iloc[0]['Close']) / 2
            self.htf2Data['HA_High'] = self.htf2Data[['High', 'Low', 'HA_Open', 'HA_Close']].max(axis=1)
            self.htf2Data['HA_Low'] = self.htf2Data[['High', 'Low', 'HA_Open', 'HA_Close']].min(axis=1)

            self.htf2Data.loc[self.htf2Data['HA_Close'] >= self.htf2Data['HA_Open'], 'type'] = "GREEN"
            self.htf2Data.loc[self.htf2Data['HA_Close'] < self.htf2Data['HA_Open'], 'type'] = "RED"

    def addIndicatorOnHTF3(self):
        if self.htf3Method == "MACD":
            macd_indicator = MACD(self.htf3Data["Close"], window_fast=self.htf3MACDfastLength, window_slow=self.htf3MACDslowLength, window_sign=self.htf3MACDSmoothing)
            self.htf3Data["macd"] = macd_indicator.macd()
            self.htf3Data["macdsignal"] = macd_indicator.macd_signal()

        if self.htf3Method == "EMA":
            emaData = EMAIndicator(self.htf3Data["Close"], window=self.htf3EMA)
            self.htf3Data['EMA'] = emaData.ema_indicator()

        if self.htf3Method == "Heiken Ashi":
            self.htf3Data['HA_Close'] = (self.htf3Data['Open'] + self.htf3Data['High'] + self.htf3Data['Low'] + self.htf3Data['Close']) / 4
            self.htf3Data['HA_Open'] = (self.htf3Data['Open'].shift(1) + self.htf3Data['Close'].shift(1)) / 2
            self.htf3Data.iloc[0, self.htf3Data.columns.get_loc("HA_Open")] = (self.htf3Data.iloc[0]['Open'] + self.htf3Data.iloc[0]['Close']) / 2
            self.htf3Data['HA_High'] = self.htf3Data[['High', 'Low', 'HA_Open', 'HA_Close']].max(axis=1)
            self.htf3Data['HA_Low'] = self.htf3Data[['High', 'Low', 'HA_Open', 'HA_Close']].min(axis=1)

            self.htf3Data.loc[self.htf3Data['HA_Close'] >= self.htf3Data['HA_Open'], 'type'] = "GREEN"
            self.htf3Data.loc[self.htf3Data['HA_Close'] < self.htf3Data['HA_Open'], 'type'] = "RED"

    def addIndicatorOnHTF4(self):
        stoch_indicator = StochasticOscillator(self.htf4Data["High"], self.htf4Data["Low"], self.htf4Data["Close"], window=5, smooth_window=3)
        self.htf4Data["stoch"] = stoch_indicator.stoch_signal()

    def addIndicatorOnHTF5(self):
        stoch_indicator = StochasticOscillator(self.htf5Data["High"], self.htf5Data["Low"], self.htf5Data["Close"], window=5, smooth_window=3)
        self.htf5Data["stoch"] = stoch_indicator.stoch_signal()

    def addIndicatorOnHTF6(self):
        stoch_indicator = StochasticOscillator(self.htf6Data["High"], self.htf6Data["Low"], self.htf6Data["Close"], window=5, smooth_window=3)
        self.htf6Data["stoch"] = stoch_indicator.stoch_signal()

    def addIndicatorOnHTF7(self):
        stoch_indicator = StochasticOscillator(self.htf7Data["High"], self.htf7Data["Low"], self.htf7Data["Close"], window=5, smooth_window=3)
        self.htf7Data["stoch"] = stoch_indicator.stoch_signal()

    def addIndicatorOnHTF8(self):
        stoch_indicator = StochasticOscillator(self.htf8Data["High"], self.htf8Data["Low"], self.htf8Data["Close"], window=5, smooth_window=3)
        self.htf8Data["stoch"] = stoch_indicator.stoch_signal()

    def addIndicatorOnHTF9(self):
        stoch_indicator = StochasticOscillator(self.htf9Data["High"], self.htf9Data["Low"], self.htf9Data["Close"], window=5, smooth_window=3)
        self.htf9Data["stoch"] = stoch_indicator.stoch_signal()

    def clearPastTrade(self):
        self.log(json.dumps(self.current_order))

        payload = {
            "username": self.discordUsername,
            "content": json.dumps(self.current_order)
        }

        requests.post(self.CLEAR_POSITION_URL, json=payload)

        self.currentStatus = 0

        self.setupBarNo = 0
        self.divCountTillNow = 0
        self.successfulDivCount = 0
        self.orderAlreadyOpenFor = 0
        self.trailSTL = self.TSLBars
        self.dcSetupBarLeft = self.dcSetupBarRechecks

        self.entryFilled = False
        self.checkEntryOrderPrice = False

        self.stoplossFilled = False
        self.checkStoplossOrderPrice = False

        self.reEntryBarsCheckTillNow = 0
        self.reEntryCyclesCheckTillNow = 0

        self.postCloseCheckTillNow = 0
        self.postCloseDivCountTillNow = 0
        self.postCloseSuccessfulDivCount = 0

        self.fakeOrder = False

        self.current_order.clear()

    def htfTest(self, mainIndex, trend):
        self.downloadHTFData()
        self.addIndicatorOnHTF1()
        self.addIndicatorOnHTF2()
        self.addIndicatorOnHTF3()
        self.addIndicatorOnHTF4()
        self.addIndicatorOnHTF5()
        self.addIndicatorOnHTF6()
        self.addIndicatorOnHTF7()
        self.addIndicatorOnHTF8()
        self.addIndicatorOnHTF9()

        htfResult = [None, None, None, None, None, None, None, None, None]
        noLong = 0
        noShort = 0

        ### HTF 1 Confirmation ###
        htf1Row = self.htf1Data.iloc[-1]

        # self.log(f"HTF check -: {htf1Row.name} - {htf1Row['Till']}")
        try:
            if self.htf1Method == "EMA":
                if htf1Row["Close"] >= htf1Row["EMA"]:
                    htfResult[0] = "LONG"
                    noLong = noLong + 1
                elif htf1Row["EMA"] > htf1Row["Close"]:
                    htfResult[0] = "SHORT"
                    noShort = noShort + 1

            elif self.htf1Method == "Heiken Ashi":
                if htf1Row["type"] == "GREEN":
                    htfResult[0] = "LONG"
                    noLong = noLong + 1
                elif htf1Row["type"] == "RED":
                    htfResult[0] = "SHORT"
                    noShort = noShort + 1

            elif self.htf1Method == "MACD":
                if htf1Row["macd"] >= htf1Row["macdsignal"]:
                    htfResult[0] = "LONG"
                    noLong = noLong + 1
                elif htf1Row["macd"] < htf1Row["macdsignal"]:
                    htfResult[0] = "SHORT"
                    noShort = noShort + 1
        except Exception as e:
            self.log(f"{self.marginSymbol} - Error in HTF 1 Test -: {e}")
            self.errorLog(f"Error IN HTF 1 Test -: {e}")
            self.htfErrorLog(self.htf1Data, "1")
            self.htfErrorLog("*" * 32, "1")
            self.htfErrorLog(htf1Row, "1")
            sys.exit(0)

        ### HTF 2 Confirmation ###
        htf2Row = self.htf2Data.iloc[-1]

        try:
            if self.htf2Method == "Heiken Ashi":
                if htf2Row["type"] == "GREEN":
                    htfResult[1] = "LONG"
                    noLong = noLong + 1
                elif htf2Row["type"] == "RED":
                    htfResult[1] = "SHORT"
                    noShort = noShort + 1

            elif self.htf2Method == "EMA":
                if htf2Row["Close"] >= htf2Row["EMA"]:
                    htfResult[1] = "LONG"
                    noLong = noLong + 1
                elif htf2Row["EMA"] > htf2Row["Close"]:
                    htfResult[1] = "SHORT"
                    noShort = noShort + 1

            elif self.htf2Method == "MACD":
                if htf2Row["macd"] >= htf2Row["macdsignal"]:
                    htfResult[1] = "LONG"
                    noLong = noLong + 1
                elif htf2Row["macd"] < htf2Row["macdsignal"]:
                    htfResult[1] = "SHORT"
                    noShort = noShort + 1
        except Exception as e:
            self.log(f"{self.marginSymbol} - Error in HTF 2 Test -: {e}")
            self.errorLog(f"Error IN HTF 2 Test -: {e}")
            self.htfErrorLog(self.htf2Data, "2")
            self.htfErrorLog("*" * 32, "2")
            self.htfErrorLog(htf2Row, "2")
            sys.exit(0)

        ### HTF 3 Confirmation ###
        htf3Row = self.htf3Data.iloc[-1]

        try:
            if self.htf3Method == "Heiken Ashi":
                if htf3Row["type"] == "GREEN":
                    htfResult[2] = "LONG"
                    noLong = noLong + 1
                elif htf3Row["type"] == "RED":
                    htfResult[2] = "SHORT"
                    noShort = noShort + 1

            elif self.htf3Method == "EMA":
                if htf3Row["Close"] >= htf3Row["EMA"]:
                    htfResult[2] = "LONG"
                    noLong = noLong + 1
                elif htf3Row["EMA"] > htf3Row["Close"]:
                    htfResult[2] = "SHORT"
                    noShort = noShort + 1

            elif self.htf3Method == "MACD":
                if htf3Row["macd"] >= htf3Row["macdsignal"]:
                    htfResult[2] = "LONG"
                    noLong = noLong + 1
                elif htf3Row["macd"] < htf3Row["macdsignal"]:
                    htfResult[2] = "SHORT"
                    noShort = noShort + 1
        except Exception as e:
            self.log(f"{self.marginSymbol} - Error in HTF 3 Test -: {e}")
            self.errorLog(f"Error IN HTF 3 Test -: {e}")
            self.htfErrorLog(self.htf3Data, "3")
            self.htfErrorLog("*" * 32, "3")
            self.htfErrorLog(htf3Row, "3")
            sys.exit(0)

        ### HTF 4 Confirmation ###
        if self.htf4Button == "On":
            htf4Row = self.htf4Data.iloc[-1]

            if self.htf4Method == "StochK":
                if htf4Row["stoch"] <= self.htf4StochKOS:
                    htfResult[3] = "LONG"
                    noLong = noLong + 1
                elif htf4Row["stoch"] >= self.htf4StochKOB:
                    htfResult[3] = "SHORT"
                    noShort = noShort + 1

        ### HTF 5 Confirmation ###
        if self.htf5Button == "On":
            htf5Row = self.htf5Data.iloc[-1]

            if self.htf5Method == "StochK":
                if htf5Row["stoch"] <= self.htf5StochKOS:
                    htfResult[4] = "LONG"
                    noLong = noLong + 1
                elif htf5Row["stoch"] >= self.htf5StochKOB:
                    htfResult[4] = "SHORT"
                    noShort = noShort + 1

        ### HTF 6 Confirmation ###
        if self.htf6Button == "On":
            htf6Row = self.htf6Data.iloc[-1]

            if self.htf6Method == "StochK":
                if htf6Row["stoch"] <= self.htf6StochKOS:
                    htfResult[5] = "LONG"
                    noLong = noLong + 1
                elif htf6Row["stoch"] >= self.htf6StochKOB:
                    htfResult[5] = "SHORT"
                    noShort = noShort + 1

        ### HTF 7 Confirmation ###
        if self.htf7Button == "On":
            htf7Row = self.htf7Data.iloc[-1]

            if self.htf4Method == "StochK":
                if htf7Row["stoch"] <= self.htf7StochKOS:
                    htfResult[6] = "LONG"
                    noLong = noLong + 1
                elif htf7Row["stoch"] >= self.htf7StochKOB:
                    htfResult[6] = "SHORT"
                    noShort = noShort + 1

        ### HTF 8 Confirmation ###
        if self.htf8Button == "On":
            htf8Row = self.htf8Data.iloc[-1]

            if self.htf4Method == "StochK":
                if htf8Row["stoch"] <= self.htf8StochKOS:
                    htfResult[7] = "LONG"
                    noLong = noLong + 1
                elif htf8Row["stoch"] >= self.htf8StochKOB:
                    htfResult[7] = "SHORT"
                    noShort = noShort + 1

        ### HTF 9 Confirmation ###
        if self.htf9Button == "On":
            htf9Row = self.htf9Data.iloc[-1]

            if self.htf4Method == "StochK":
                if htf9Row["stoch"] <= self.htf9StochKOS:
                    htfResult[8] = "LONG"
                    noLong = noLong + 1
                elif htf9Row["stoch"] >= self.htf9StochKOB:
                    htfResult[8] = "SHORT"
                    noShort = noShort + 1

        self.log(f"{mainIndex.strftime('%Y-%m-%d %H:%M')} HTF Result -:")
        self.log(htfResult)

        ###Check if HTF Passed###
        if noShort >= self.minHTFConfirm and trend == "SHORT":
            return True, noShort, htfResult

        if noLong >= self.minHTFConfirm and trend == "LONG":
            return True, noLong, htfResult

        return False, 0, htfResult

    def divTest(self, currentRow, prevRow, searchType, startBarCCI, startBarClose):
        ##Return restart, cancel, 1barBackResult, startBarBackResult

        if self.countSameAsDiv == "Off":

            if self.current_order["TYPE"] == "LONG":
                if currentRow["type"] == "RED":
                    if searchType == "1 Bar Back":
                        if currentRow["cci"] > prevRow["cci"] and currentRow["Close"] < prevRow["Close"]:
                            return False, False, True, False
                        elif currentRow["cci"] < startBarCCI and currentRow["Close"] < prevRow["Close"]:
                            if self.startBarRecheck == "Cancel Startup Bar":
                                return False, True, False, False
                            elif self.startBarRecheck == "Restart Startup Bar":
                                return True, False, False, False
                            elif self.startBarRecheck == "Do Nothing":
                                return False, False, False, False
                    elif searchType == "Start Bar":
                        if currentRow["cci"] > startBarCCI and currentRow["Close"] < startBarClose:
                            return False, False, False, True
                        elif currentRow["cci"] < startBarCCI and currentRow["Close"] < startBarClose:
                            if self.startBarRecheck == "Cancel Startup Bar":
                                return False, True, False, False
                            elif self.startBarRecheck == "Restart Startup Bar":
                                return True, False, False, False
                            elif self.startBarRecheck == "Do Nothing":
                                return False, False, False, False
                    elif searchType == "Either":
                        if currentRow["cci"] > prevRow["cci"] and currentRow["Close"] < prevRow["Close"]:
                            return False, False, True, False
                        elif currentRow["cci"] > startBarCCI and currentRow["Close"] < startBarClose:
                            return False, False, False, True
                        elif currentRow["cci"] < startBarCCI and currentRow["Close"] < prevRow["Close"]:
                            if self.startBarRecheck == "Cancel Startup Bar":
                                return False, True, False, False
                            elif self.startBarRecheck == "Restart Startup Bar":
                                return True, False, False, False
                            elif self.startBarRecheck == "Do Nothing":
                                return False, False, False, False
                        elif currentRow["cci"] < startBarCCI and currentRow["Close"] < startBarClose:
                            if self.startBarRecheck == "Cancel Startup Bar":
                                return False, True, False, False
                            elif self.startBarRecheck == "Restart Startup Bar":
                                return True, False, False, False
                            elif self.startBarRecheck == "Do Nothing":
                                return False, False, False, False
                    elif searchType == "Both":
                        if currentRow["cci"] > prevRow["cci"] and currentRow["Close"] < prevRow["Close"] and currentRow["cci"] > startBarCCI and currentRow["Close"] < startBarClose:
                            return False, False, True, False
                        elif currentRow["cci"] < startBarCCI and currentRow["Close"] < prevRow["Close"]:
                            if self.startBarRecheck == "Cancel Startup Bar":
                                return False, True, False, False
                            elif self.startBarRecheck == "Restart Startup Bar":
                                return True, False, False, False
                            elif self.startBarRecheck == "Do Nothing":
                                return False, False, False, False
                        elif currentRow["cci"] < startBarCCI and currentRow["Close"] < startBarClose:
                            if self.startBarRecheck == "Cancel Startup Bar":
                                return False, True, False, False
                            elif self.startBarRecheck == "Restart Startup Bar":
                                return True, False, False, False
                            elif self.startBarRecheck == "Do Nothing":
                                return False, False, False, False

                return False, False, False, False

            elif self.current_order["TYPE"] == "SHORT":
                if currentRow["type"] == "GREEN":
                    if searchType == "1 Bar Back":
                        if currentRow["cci"] < prevRow["cci"] and currentRow["Close"] > prevRow["Close"]:
                            return False, False, True, False
                        elif currentRow["cci"] > startBarCCI and currentRow["Close"] > prevRow["Close"]:
                            if self.startBarRecheck == "Cancel Startup Bar":
                                return False, True, False, False
                            elif self.startBarRecheck == "Restart Startup Bar":
                                return True, False, False, False
                            elif self.startBarRecheck == "Do Nothing":
                                return False, False, False, False
                    elif searchType == "Start Bar":
                        if currentRow["cci"] < startBarCCI and currentRow["Close"] > startBarClose:
                            return False, False, False, True
                        elif currentRow["cci"] > startBarCCI and currentRow["Close"] > startBarClose:
                            if self.startBarRecheck == "Cancel Startup Bar":
                                return False, True, False, False
                            elif self.startBarRecheck == "Restart Startup Bar":
                                return True, False, False, False
                            elif self.startBarRecheck == "Do Nothing":
                                return False, False, False, False
                    elif searchType == "Either":
                        if currentRow["cci"] < prevRow["cci"] and currentRow["Close"] > prevRow["Close"]:
                            return False, False, True, False
                        elif currentRow["cci"] < startBarCCI and currentRow["Close"] > startBarClose:
                            return False, False, False, True
                        elif currentRow["cci"] > startBarCCI and currentRow["Close"] > startBarClose:
                            if self.startBarRecheck == "Cancel Startup Bar":
                                return False, True, False, False
                            elif self.startBarRecheck == "Restart Startup Bar":
                                return True, False, False, False
                            elif self.startBarRecheck == "Do Nothing":
                                return False, False, False, False
                        elif currentRow["cci"] > startBarCCI and currentRow["Close"] > prevRow["Close"]:
                            if self.startBarRecheck == "Cancel Startup Bar":
                                return False, True, False, False
                            elif self.startBarRecheck == "Restart Startup Bar":
                                return True, False, False, False
                            elif self.startBarRecheck == "Do Nothing":
                                return False, False, False, False
                    elif searchType == "Both":
                        if currentRow["cci"] < prevRow["cci"] and currentRow["Close"] > prevRow["Close"] and currentRow["cci"] < startBarCCI and currentRow["Close"] > startBarClose:
                            return False, False, True, False
                        elif currentRow["cci"] > startBarCCI and currentRow["Close"] > startBarClose:
                            if self.startBarRecheck == "Cancel Startup Bar":
                                return False, True, False, False
                            elif self.startBarRecheck == "Restart Startup Bar":
                                return True, False, False, False
                            elif self.startBarRecheck == "Do Nothing":
                                return False, False, False, False
                        elif currentRow["cci"] > startBarCCI and currentRow["Close"] > prevRow["Close"]:
                            if self.startBarRecheck == "Cancel Startup Bar":
                                return False, True, False, False
                            elif self.startBarRecheck == "Restart Startup Bar":
                                return True, False, False, False
                            elif self.startBarRecheck == "Do Nothing":
                                return False, False, False, False

                return False, False, False, False

        elif self.countSameAsDiv == "On":

            if self.current_order["TYPE"] == "LONG":
                if currentRow["type"] == "RED":
                    if searchType == "1 Bar Back":
                        if currentRow["cci"] >= prevRow["cci"] and currentRow["Close"] <= prevRow["Close"]:
                            return False, False, True, False
                        elif currentRow["cci"] <= startBarCCI and currentRow["Close"] <= prevRow["Close"]:
                            if self.startBarRecheck == "Cancel Startup Bar":
                                return False, True, False, False
                            elif self.startBarRecheck == "Restart Startup Bar":
                                return True, False, False, False
                            elif self.startBarRecheck == "Do Nothing":
                                return False, False, False, False
                    elif searchType == "Start Bar":
                        if currentRow["cci"] >= startBarCCI and currentRow["Close"] <= startBarClose:
                            return False, False, False, True
                        elif currentRow["cci"] <= startBarCCI and currentRow["Close"] <= startBarClose:
                            if self.startBarRecheck == "Cancel Startup Bar":
                                return False, True, False, False
                            elif self.startBarRecheck == "Restart Startup Bar":
                                return True, False, False, False
                            elif self.startBarRecheck == "Do Nothing":
                                return False, False, False, False
                    elif searchType == "Either":
                        if currentRow["cci"] >= prevRow["cci"] and currentRow["Close"] <= prevRow["Close"]:
                            return False, False, True, False
                        elif currentRow["cci"] >= startBarCCI and currentRow["Close"] <= startBarClose:
                            return False, False, False, True
                        elif currentRow["cci"] <= startBarCCI and currentRow["Close"] <= prevRow["Close"]:
                            if self.startBarRecheck == "Cancel Startup Bar":
                                return False, True, False, False
                            elif self.startBarRecheck == "Restart Startup Bar":
                                return True, False, False, False
                            elif self.startBarRecheck == "Do Nothing":
                                return False, False, False, False
                        elif currentRow["cci"] <= startBarCCI and currentRow["Close"] <= startBarClose:
                            if self.startBarRecheck == "Cancel Startup Bar":
                                return False, True, False, False
                            elif self.startBarRecheck == "Restart Startup Bar":
                                return True, False, False, False
                            elif self.startBarRecheck == "Do Nothing":
                                return False, False, False, False
                    elif searchType == "Both":
                        if currentRow["cci"] >= prevRow["cci"] and currentRow["Close"] <= prevRow["Close"] and currentRow["cci"] >= startBarCCI and currentRow["Close"] <= startBarClose:
                            return False, False, True, False
                        elif currentRow["cci"] <= startBarCCI and currentRow["Close"] <= prevRow["Close"]:
                            if self.startBarRecheck == "Cancel Startup Bar":
                                return False, True, False, False
                            elif self.startBarRecheck == "Restart Startup Bar":
                                return True, False, False, False
                            elif self.startBarRecheck == "Do Nothing":
                                return False, False, False, False
                        elif currentRow["cci"] <= startBarCCI and currentRow["Close"] <= startBarClose:
                            if self.startBarRecheck == "Cancel Startup Bar":
                                return False, True, False, False
                            elif self.startBarRecheck == "Restart Startup Bar":
                                return True, False, False, False
                            elif self.startBarRecheck == "Do Nothing":
                                return False, False, False, False

                return False, False, False, False

            elif self.current_order["TYPE"] == "SHORT":
                if currentRow["type"] == "GREEN":
                    if searchType == "1 Bar Back":
                        if currentRow["cci"] <= prevRow["cci"] and currentRow["Close"] >= prevRow["Close"]:
                            return False, False, True, False
                        elif currentRow["cci"] >= startBarCCI and currentRow["Close"] >= prevRow["Close"]:
                            if self.startBarRecheck == "Cancel Startup Bar":
                                return False, True, False, False
                            elif self.startBarRecheck == "Restart Startup Bar":
                                return True, False, False, False
                            elif self.startBarRecheck == "Do Nothing":
                                return False, False, False, False
                    elif searchType == "Start Bar":
                        if currentRow["cci"] <= startBarCCI and currentRow["Close"] >= startBarClose:
                            return False, False, False, True
                        elif currentRow["cci"] >= startBarCCI and currentRow["Close"] >= startBarClose:
                            if self.startBarRecheck == "Cancel Startup Bar":
                                return False, True, False, False
                            elif self.startBarRecheck == "Restart Startup Bar":
                                return True, False, False, False
                            elif self.startBarRecheck == "Do Nothing":
                                return False, False, False, False
                    elif searchType == "Either":
                        if currentRow["cci"] <= prevRow["cci"] and currentRow["Close"] >= prevRow["Close"]:
                            return False, False, True, False
                        elif currentRow["cci"] <= startBarCCI and currentRow["Close"] >= startBarClose:
                            return False, False, False, True
                        elif currentRow["cci"] >= startBarCCI and currentRow["Close"] >= startBarClose:
                            if self.startBarRecheck == "Cancel Startup Bar":
                                return False, True, False, False
                            elif self.startBarRecheck == "Restart Startup Bar":
                                return True, False, False, False
                            elif self.startBarRecheck == "Do Nothing":
                                return False, False, False, False
                        elif currentRow["cci"] >= startBarCCI and currentRow["Close"] >= prevRow["Close"]:
                            if self.startBarRecheck == "Cancel Startup Bar":
                                return False, True, False, False
                            elif self.startBarRecheck == "Restart Startup Bar":
                                return True, False, False, False
                            elif self.startBarRecheck == "Do Nothing":
                                return False, False, False, False
                    elif searchType == "Both":
                        if currentRow["cci"] <= prevRow["cci"] and currentRow["Close"] >= prevRow["Close"] and currentRow["cci"] <= startBarCCI and currentRow["Close"] >= startBarClose:
                            return False, False, True, False
                        elif currentRow["cci"] >= startBarCCI and currentRow["Close"] >= startBarClose:
                            if self.startBarRecheck == "Cancel Startup Bar":
                                return False, True, False, False
                            elif self.startBarRecheck == "Restart Startup Bar":
                                return True, False, False, False
                            elif self.startBarRecheck == "Do Nothing":
                                return False, False, False, False
                        elif currentRow["cci"] >= startBarCCI and currentRow["Close"] >= prevRow["Close"]:
                            if self.startBarRecheck == "Cancel Startup Bar":
                                return False, True, False, False
                            elif self.startBarRecheck == "Restart Startup Bar":
                                return True, False, False, False
                            elif self.startBarRecheck == "Do Nothing":
                                return False, False, False, False

                return False, False, False, False

    def dtfTestUtil(self, mainIndex, dtfRows, dtfNo, divRequired, dtfLastDivStochKOB, dtfLastDivStochKOS):
        dtfStartbarFound = False
        dtfShortestCCI = 1000
        dtfLargestCCI = -1000
        dtfStartbarIndex = 0

        for index, row in dtfRows.iterrows():
            if row["cci"] > self.dtfCCIShortLimit and self.current_order["TYPE"] == "SHORT" and row["cci"] >= dtfLargestCCI:
                if self.dtfStochKOB == 0 or (self.dtfStochKOB != 0 and row["stoch"] > self.dtfStochKOB):
                    dtfStartbarFound = True
                    dtfStartbarIndex = index

                    self.current_order[f"dtf{dtfNo}StartbarCCI"] = row['cci']
                    self.current_order[f"dtf{dtfNo}StartbarClose"] = row['Close']
                    dtfLargestCCI = row["cci"]

                    self.log(f"{mainIndex.strftime('%Y-%m-%d %H:%M')} Found DTF{dtfNo} Startbar at {index}")


            elif row["cci"] < self.dtfCCILongLimit and self.current_order["TYPE"] == "LONG" and row["cci"] <= dtfShortestCCI:
                if self.dtfStochKOS == 0 or (self.dtfStochKOS != 0 and row["stoch"] < self.dtfStochKOS):
                    dtfStartbarFound = True
                    dtfStartbarIndex = index

                    self.current_order[f"dtf{dtfNo}StartbarCCI"] = row['cci']
                    self.current_order[f"dtf{dtfNo}StartbarClose"] = row['Close']
                    dtfShortestCCI = row["cci"]

                    self.log(f"{mainIndex.strftime('%Y-%m-%d %H:%M')} Found DTF{dtfNo} Startbar at {index}")

        if not dtfStartbarFound:
            self.log(f"{mainIndex.strftime('%Y-%m-%d %H:%M')}  No DTF{dtfNo} Startbar Found")
            return False
        else:
            dtfDivRows = dtfRows.loc[dtfStartbarIndex:]
            dtfPrevRow = dtfDivRows.iloc[0]
            dtfDivRows = dtfDivRows.iloc[1:, :]

            if len(dtfDivRows) == 0:
                return False
            else:
                dtfSuccessfullCount = 0

                for index, row in dtfDivRows.iterrows():
                    restartStartbar, cancelStartbar, prevBarResult, startBarResult = self.divTest(row, dtfPrevRow, self.searchDivOnly, self.current_order[f"dtf{dtfNo}StartbarCCI"], self.current_order[f"dtf{dtfNo}StartbarClose"])

                    if prevBarResult or startBarResult:
                        self.log(f"{mainIndex.strftime('%Y-%m-%d %H:%M')} Found DTF Divergence at {index}")
                        dtfSuccessfullCount = dtfSuccessfullCount + 1

                    if dtfSuccessfullCount == divRequired:
                        if self.current_order['TYPE'] == "LONG":

                            if row["stoch"] > dtfLastDivStochKOS != 0:
                                return False
                            else:
                                self.log(f"{mainIndex.strftime('%Y-%m-%d %H:%M')} DTF{dtfNo} Pass")
                                return True

                        else:

                            if row["stoch"] < dtfLastDivStochKOB != 0:
                                return False
                            else:
                                self.log(f"{mainIndex.strftime('%Y-%m-%d %H:%M')} DTF{dtfNo} Pass")
                                return True

                    dtfPrevRow = row

                return False

    def dtfTest(self, mainIndex):
        dtfResult = [None, None, None, None, None, None, None, None, None]
        dtfpass = 0

        if self.checkDTF1 == "On":
            dtf1Rows = self.dtf1Data.tail(self.dtf1DivWindow)
            dtfResult[1] = self.dtfTestUtil(mainIndex, dtf1Rows, 1, self.dtf1DivRequired, self.dtf1LastDivStochKOB, self.dtf1LastDivStochKOS)

            if dtfResult[1]:
                dtfpass = dtfpass + 1

        if self.checkDTF2 == "On":
            dtf2Rows = self.dtf2Data.tail(self.dtf2DivWindow)
            dtfResult[2] = self.dtfTestUtil(mainIndex, dtf2Rows, 2, self.dtf2DivRequired, self.dtf2LastDivStochKOB, self.dtf2LastDivStochKOS)

            if dtfResult[2]:
                dtfpass = dtfpass + 2

        if self.checkDTF3 == "On":
            dtf3Rows = self.dtf3Data.tail(self.dtf3DivWindow)
            dtfResult[3] = self.dtfTestUtil(mainIndex, dtf3Rows, 3, self.dtf3DivRequired, self.dtf3LastDivStochKOB, self.dtf3LastDivStochKOS)

            if dtfResult[3]:
                dtfpass = dtfpass + 1

        if self.checkDTF4 == "On":
            dtf4Rows = self.dtf4Data.tail(self.dtf4DivWindow)
            dtfResult[4] = self.dtfTestUtil(mainIndex, dtf4Rows, 4, self.dtf4DivRequired, self.dtf4LastDivStochKOB, self.dtf4LastDivStochKOS)

            if dtfResult[4]:
                dtfpass = dtfpass + 1

        if self.checkDTF5 == "On":
            dtf5Rows = self.dtf5Data.tail(self.dtf5DivWindow)
            dtfResult[5] = self.dtfTestUtil(mainIndex, dtf5Rows, 5, self.dtf5DivRequired, self.dtf5LastDivStochKOB, self.dtf5LastDivStochKOS)

            if dtfResult[5]:
                dtfpass = dtfpass + 1

        if self.checkDTF6 == "On":
            dtf6Rows = self.dtf6Data.tail(self.dtf6DivWindow)
            dtfResult[6] = self.dtfTestUtil(mainIndex, dtf6Rows, 6, self.dtf6DivRequired, self.dtf6LastDivStochKOB, self.dtf6LastDivStochKOS)

            if dtfResult[6]:
                dtfpass = dtfpass + 1

        if self.checkDTF7 == "On":
            dtf7Rows = self.dtf7Data.tail(self.dtf7DivWindow)
            dtfResult[7] = self.dtfTestUtil(mainIndex, dtf7Rows, 7, self.dtf7DivRequired, self.dtf7LastDivStochKOB, self.dtf7LastDivStochKOS)

            if dtfResult[7]:
                dtfpass = dtfpass + 1

        if self.checkDTF8 == "On":
            dtf8Rows = self.dtf8Data.tail(self.dtf8DivWindow)
            dtfResult[8] = self.dtfTestUtil(mainIndex, dtf8Rows, 8, self.dtf8DivRequired, self.dtf8LastDivStochKOB, self.dtf8LastDivStochKOS)

            if dtfResult[8]:
                dtfpass = dtfpass + 1

        ##First index is a dummy index, it will always be None
        del dtfResult[0]

        self.log(f"{mainIndex.strftime('%Y-%m-%d %H:%M')} DTF Result -: ")
        self.log(dtfResult)
        self.log(f"{mainIndex.strftime('%Y-%m-%d %H:%M')} DTF PASS -: {dtfpass}")
        self.log(f"{mainIndex.strftime('%Y-%m-%d %H:%M')} Trail SL Settings -: {self.mainTrailSL}")

        if dtfpass >= self.dtfMinPass:
            if self.mainTrailSL == "LTF":
                self.trailSL = "LTF"
            elif self.mainTrailSL == "DTF1":
                correctIndex = 1
                correctIndexFound = False

                for dtfR in dtfResult:
                    if dtfR:
                        correctIndexFound = True
                        break
                    correctIndex = correctIndex + 1

                if correctIndexFound:
                    self.trailSL = f"DTF{correctIndex}"
                else:
                    self.trailSL = "LTF"
            elif self.mainTrailSL == "DTF2":
                if dtfResult[0] == True and dtfResult[1] == True:
                    self.trailSL = "DTF2"
                else:
                    correctIndex = 1
                    correctIndexFound = False

                    for dtfR in dtfResult:
                        if dtfR:
                            correctIndexFound = True
                            break
                        correctIndex = correctIndex + 1

                    if correctIndexFound:
                        self.trailSL = f"DTF{correctIndex}"
                    else:
                        self.trailSL = "LTF"
            elif self.mainTrailSL == "DTF3a":
                if dtfResult[0] == True and dtfResult[1] == True and dtfResult[2] == True:
                    self.trailSL = "DTF3"
                else:
                    correctIndex = 1
                    correctIndexFound = False

                    for dtfR in dtfResult:
                        if dtfR:
                            correctIndexFound = True
                            break
                        correctIndex = correctIndex + 1

                    if correctIndexFound:
                        self.trailSL = f"DTF{correctIndex}"
                    else:
                        self.trailSL = "LTF"
            elif self.mainTrailSL == "DTF3b":
                if dtfResult[2] == True and (dtfResult[0] == True or dtfResult[1] == True):
                    self.trailSL = "DTF3"
                else:
                    correctIndex = 1
                    correctIndexFound = False

                    for dtfR in dtfResult:
                        if dtfR:
                            correctIndexFound = True
                            break
                        correctIndex = correctIndex + 1

                    if correctIndexFound:
                        self.trailSL = f"DTF{correctIndex}"
                    else:
                        self.trailSL = "LTF"

            self.log(f"{mainIndex.strftime('%Y-%m-%d %H:%M')} Trail SL -: {self.trailSL}")
            return True, dtfResult
        else:
            self.trailSL = "LTF"
            return False, dtfResult

    def checkSwing(self, index):
        lastCandleIndex = self.ltfData.index.get_loc(index)
        checkrowIndex = lastCandleIndex - self.swingStrength
        checkrow = self.ltfData.iloc[checkrowIndex]

        self.swingLog("*" * 80)
        self.swingLog("Swing Data Calculation")
        self.swingLog(f"Last Candle Index -: {lastCandleIndex}, Last Candle Name -: {index} ")
        self.swingLog(f"Checkrow index - {lastCandleIndex - self.swingStrength} Checkrow name -: {checkrow.name}")

        if checkrowIndex < 0:
            return False

        prevs = self.ltfData.iloc[(checkrowIndex - self.swingStrength): checkrowIndex]
        self.swingLog("Prev")
        self.swingLog(prevs)

        nexts = self.ltfData.iloc[(checkrowIndex + 1): (checkrowIndex + self.swingStrength + 1)]
        self.swingLog("Next")
        self.swingLog(nexts)

        self.swingLog("*" * 80)

        if len(prevs) > (self.swingStrength - 1) and len(nexts) > (self.swingStrength - 1):

            if (prevs["High"] < checkrow["High"]).all() and (nexts["High"] < checkrow["High"]).all():
                self.swingFoundLog(f"Swing Condition Fullfilled On {checkrow.name}")
                self.swingLog(f"Swing Condition Fullfilled On {checkrow.name}")
                self.swingHigh.append(checkrow.name)
                self.swingHighData.append(checkrow['High'])

                self.swingLog("Saved Swings")
                self.swingLog(self.swingHigh[-5:])
                self.swingLog(self.swingHighData[-5:])
                self.swingLog(self.swingLow[-5:])
                self.swingLog(self.swingLowData[-5:])

                return True

            elif (prevs["Low"] > checkrow["Low"]).all() and (nexts["Low"] > checkrow["Low"]).all():
                self.swingFoundLog(f"Swing Condition Fullfilled On {checkrow.name}")
                self.swingLog(f"Swing Condition Fullfilled On {checkrow.name}")

                self.swingLow.append(checkrow.name)
                self.swingLowData.append(checkrow['Low'])

                self.swingLog("Saved Swings")
                self.swingLog(self.swingHigh[-5:])
                self.swingLog(self.swingHighData[-5:])
                self.swingLog(self.swingLow[-5:])
                self.swingLog(self.swingLowData[-5:])

                return True

    def findDCLevels(self, high, low, orderType):
        originalDanielLevels = [0.148, 0.297, 0.375, 0.445, 0.500, 0.593, 0.625, 0.742, 0.890]
        danielLevels = [0.148, 0.297, 0.375, 0.445, 0.500, 0.593, 0.625, 0.742, 0.890]

        dclevels = []

        for i in range(1, self.dcLevelMultiplier + 1):
            for level in originalDanielLevels:
                danielLevels.append(i + level)

        max_level = high
        min_level = low

        if orderType == "LONG":
            for ratio in danielLevels:
                dclevels.append(max_level - (max_level - min_level) * ratio)
        else:
            for ratio in danielLevels:
                dclevels.append(min_level + (max_level - min_level) * ratio)

        return danielLevels, dclevels

    def checkTargetInRange(self, danielRatios, dcLevels, check1, check2):
        ##return danielLevel, check1, check2
        level = 0
        for dc in dcLevels:
            if dc - dc * self.targetRecognitionAllowance <= check1 <= dc + dc * self.targetRecognitionAllowance:
                self.log(f"Found {check1} in dc level {dc} daniel level {danielRatios[level]} with range {dc - dc * self.targetRecognitionAllowance}, {dc + dc * self.targetRecognitionAllowance}")
                return danielRatios[level], True, False
            if dc - dc * self.targetRecognitionAllowance <= check2 <= dc + dc * self.targetRecognitionAllowance:
                self.log(f"Found {check2} in dc level {dc}  daniel level {danielRatios[level]} with range {dc - dc * self.targetRecognitionAllowance}, {dc + dc * self.targetRecognitionAllowance}")
                return danielRatios[level], False, True

            level = level + 1

        return 0, False, False

    def checkTargetRecognitation(self, row, latestSwingHighData, latestSwingLowData, setupBarNo, redrawNumber):
        danielRatios, dclevels = self.findDCLevels(latestSwingHighData, latestSwingLowData, self.current_order['TYPE'])

        if self.current_order["TYPE"] == "LONG":
            dcPassed = False

            danielLevel, closeCheck, lowCheck = self.checkTargetInRange(danielRatios, dclevels, row["Close"], row["Low"])
            if closeCheck:
                ##DC Target Recogination found on Close of previous bar
                dcPassed = True
                self.current_order["DC_LOOKBACKBAR"] = 0
                self.current_order["DC_CHARACTERISTIC_USED"] = "Close"

            if lowCheck:
                ##DC Target Recogination found on Low of previous bar
                dcPassed = True
                self.current_order["DC_LOOKBACKBAR"] = 0
                self.current_order["DC_CHARACTERISTIC_USED"] = "Low"

            if not dcPassed:
                if self.dcLookbackPeriod == 1:
                    danielLevel, closeCheck, lowCheck = self.checkTargetInRange(danielRatios, dclevels,
                                                                                self.prevRow["Close"],
                                                                                self.prevRow["Low"])

                    if closeCheck:
                        ##DC Target Recogination found on Close of previous bar
                        dcPassed = True
                        self.current_order["DC_LOOKBACKBAR"] = 1
                        self.current_order["DC_CHARACTERISTIC_USED"] = "Close"

                    if lowCheck:
                        ##DC Target Recogination found on Low of previous bar
                        dcPassed = True
                        self.current_order["DC_LOOKBACKBAR"] = 1
                        self.current_order["DC_CHARACTERISTIC_USED"] = "Low"

            if dcPassed:
                self.current_order["DC_SETUPBAR"] = setupBarNo
                self.current_order["DC_SWINGREDRAW"] = redrawNumber
                self.current_order["DC_DANIEL_LEVEL"] = danielLevel
                return True

        elif self.current_order["TYPE"] == "SHORT":
            dcPassed = False

            danielLevel, closeCheck, highCheck = self.checkTargetInRange(danielRatios, dclevels, row["Close"],
                                                                         row["High"])

            if closeCheck:
                ##DC Target Recogination found on Close of previous bar
                dcPassed = True
                self.current_order["DC_LOOKBACKBAR"] = 0
                self.current_order["DC_CHARACTERISTIC_USED"] = "Close"

            if highCheck:
                ##DC Target Recogination found on Low of previous bar
                dcPassed = True
                self.current_order["DC_LOOKBACKBAR"] = 0
                self.current_order["DC_CHARACTERISTIC_USED"] = "High"

            if not dcPassed:
                if self.dcLookbackPeriod == 1:
                    danielLevel, closeCheck, highCheck = self.checkTargetInRange(danielRatios, dclevels,
                                                                                 self.prevRow["Close"],
                                                                                 self.prevRow["High"])

                    if closeCheck:
                        ##DC Target Recogination found on Close of previous bar
                        dcPassed = True
                        self.current_order["DC_LOOKBACKBAR"] = 1
                        self.current_order["DC_CHARACTERISTIC_USED"] = "Close"

                    if highCheck:
                        ##DC Target Recogination found on Low of previous bar
                        dcPassed = True
                        self.current_order["DC_LOOKBACKBAR"] = 1
                        self.current_order["DC_CHARACTERISTIC_USED"] = "High"

            if dcPassed:
                self.current_order["DC_SETUPBAR"] = setupBarNo
                self.current_order["DC_SWINGREDRAW"] = redrawNumber
                self.current_order["DC_DANIEL_LEVEL"] = danielLevel
                return True

        return False

    def targetReconginitionTest(self, row, setupBarNo):
        swingHighNo = -1
        swingLowNo = -1
        swingRedraw = 0

        if swingHighNo not in range(-len(self.swingHigh), len(self.swingHigh)):
            return False

        if swingLowNo not in range(-len(self.swingLow), len(self.swingLow)):
            return False

        latestSwingHighData = self.swingHighData[swingHighNo]
        latestSwingLowData = self.swingLowData[swingLowNo]

        checkTargetRecognitationPassed = self.checkTargetRecognitation(row, latestSwingHighData, latestSwingLowData, setupBarNo, swingRedraw)

        dcSwingRedraws = self.dcSwingRedraws

        if dcSwingRedraws > 0:
            if self.current_order["TYPE"] == "LONG":
                swingHighNo = swingHighNo - 1
                swingRedraw = swingRedraw + 1

                if swingHighNo not in range(-len(self.swingHigh), len(self.swingHigh)):
                    return False

                if swingLowNo not in range(-len(self.swingLow), len(self.swingLow)):
                    return False

                latestSwingHighData = self.swingHighData[swingHighNo]
                latestSwingLowData = self.swingLowData[swingLowNo]

                checkTargetRecognitationPassed = self.checkTargetRecognitation(row, latestSwingHighData, latestSwingLowData, setupBarNo, swingRedraw)

            if self.current_order["TYPE"] == "SHORT":
                swingLowNo = swingLowNo - 1
                swingRedraw = swingRedraw + 1

                if swingHighNo not in range(-len(self.swingHigh), len(self.swingHigh)):
                    return False

                if swingLowNo not in range(-len(self.swingLow), len(self.swingLow)):
                    return False

                latestSwingHighData = self.swingHighData[swingHighNo]
                latestSwingLowData = self.swingLowData[swingLowNo]

                checkTargetRecognitationPassed = self.checkTargetRecognitation(row, latestSwingHighData, latestSwingLowData, setupBarNo, swingRedraw)

            dcSwingRedraws = dcSwingRedraws - 1

        if not checkTargetRecognitationPassed:
            while dcSwingRedraws > 0:
                if self.current_order["TYPE"] == "LONG":
                    swingRedraw = swingRedraw + 1

                    if swingHighNo not in range(-len(self.swingHigh), len(self.swingHigh)):
                        return False

                    if swingLowNo not in range(-len(self.swingLow), len(self.swingLow)):
                        return False

                    latestSwingHigh = self.swingHigh[swingHighNo]
                    latestSwingLow = self.swingLow[swingLowNo]

                    if latestSwingHigh > latestSwingLow:
                        swingHighNo = swingHighNo - 1
                    else:
                        swingLowNo = swingLowNo - 1

                elif self.current_order["TYPE"] == "SHORT":
                    swingRedraw = swingRedraw + 1

                    if swingHighNo not in range(-len(self.swingHigh), len(self.swingHigh)):
                        return False

                    if swingLowNo not in range(-len(self.swingLow), len(self.swingLow)):
                        return False

                    latestSwingHigh = self.swingHigh[swingHighNo]
                    latestSwingLow = self.swingLow[swingLowNo]

                    if latestSwingLow > latestSwingHigh:
                        swingLowNo = swingLowNo - 1
                    else:
                        swingHighNo = swingHighNo - 1

                if swingHighNo not in range(-len(self.swingHigh), len(self.swingHigh)):
                    return False

                if swingLowNo not in range(-len(self.swingLow), len(self.swingLow)):
                    return False

                latestSwingHighData = self.swingHighData[swingHighNo]
                latestSwingLowData = self.swingLowData[swingLowNo]

                checkTargetRecognitationPassed = self.checkTargetRecognitation(row, latestSwingHighData, latestSwingLowData, setupBarNo, swingRedraw)

                if checkTargetRecognitationPassed:
                    break

                dcSwingRedraws = dcSwingRedraws - 1

        return checkTargetRecognitationPassed

    def accountBalance(self):
        spotBalance = self.client.get_account()
        usdtSPOTBalance = next((item for item in spotBalance['balances'] if item["asset"] == "USDT"), None)
        btcSPOTBalance = next((item for item in spotBalance['balances'] if item["asset"] == "BTC"), None)
        ethSPOTBalance = next((item for item in spotBalance['balances'] if item["asset"] == "ETH"), None)

        crossBalance = self.client.get_margin_account()
        usdtCROSSBalance = next((item for item in crossBalance['userAssets'] if item["asset"] == "USDT"), None)
        btcCROSSBalance = next((item for item in crossBalance['userAssets'] if item["asset"] == "BTC"), None)
        ethCROSSBalance = next((item for item in crossBalance['userAssets'] if item["asset"] == "ETH"), None)

        return usdtSPOTBalance["free"], usdtCROSSBalance["free"], btcSPOTBalance["free"], btcCROSSBalance["free"], ethSPOTBalance["free"], ethCROSSBalance["free"]

    def transferSPOTtoCROSS(self, asset, amount):
        try:
            transaction = self.client.transfer_spot_to_margin(asset=asset, amount=f'{amount}')
            return transaction
        except Exception as e:
            self.log(f"Error while transferring {asset} {amount} from spot to cross")
            self.errorLog(f"Error while transferring {asset} {amount} from spot to cross")
            self.log(f"Error -: {e}")
            self.errorLog(f"Error -: {e}")
            self.clearPastTrade()
            sys.exit()

    def transferCROSStoSPOT(self, asset, amount):
        try:
            transaction = self.client.transfer_margin_to_spot(asset=asset, amount=f'{amount}')
            return transaction
        except Exception as e:
            self.log(f"Error while transferring {asset} {amount} from cross to spot")
            self.errorLog(f"Error while transferring {asset} {amount} from cross to spot")
            self.log(f"Error -: {e}")
            self.errorLog(f"Error -: {e}")
            self.clearPastTrade()
            sys.exit()

    def transferSPOTtoISOLATEDMARGIN(self, asset, symbol, amount):
        try:
            transaction = self.client.transfer_spot_to_isolated_margin(asset=asset, symbol=symbol, amount=f'{amount}')
            return transaction
        except Exception as e:
            self.log(f"Error while transferring {asset}/{symbol} {amount} from spot to iso")
            self.errorLog(f"Error while transferring {asset}/{symbol} {amount} from spot to iso")
            self.log(f"Error -: {e}")
            self.errorLog(f"Error -: {e}")
            self.clearPastTrade()
            sys.exit()

    def transferISOLATEDMARGINtoSPOT(self, asset, symbol, amount):
        try:
            transaction = self.client.transfer_isolated_margin_to_spot(asset=asset, symbol=symbol, amount=f'{amount}')
            return transaction
        except Exception as e:
            self.log(f"Error while transferring {asset}/{symbol} {amount} from iso to spot")
            self.errorLog(f"Error while transferring {asset}/{symbol} {amount} from iso to spot")
            self.log(f"Error -: {e}")
            self.errorLog(f"Error -: {e}")
            self.clearPastTrade()
            sys.exit()

    def transferCROSStoISOLATEDMARGIN(self, asset, symbol, amount):
        try:
            self.transferCROSStoSPOT(asset=asset, amount=amount)
            self.transferSPOTtoISOLATEDMARGIN(asset=asset, symbol=symbol, amount=amount)
        except Exception as e:
            self.log(f"Error while transferring {asset}/{symbol} {amount} from cross to iso")
            self.errorLog(f"Error while transferring {asset}/{symbol} {amount} from cross to iso")
            self.log(f"Error -: {e}")
            self.errorLog(f"Error -: {e}")
            self.clearPastTrade()
            sys.exit()

    def transferISOLOATEDMARGINtoCROSS(self, asset, symbol, amount):
        try:
            self.transferISOLATEDMARGINtoSPOT(asset=asset, symbol=symbol, amount=amount)
            self.transferSPOTtoCROSS(asset=asset, amount=amount)
        except Exception as e:
            self.log(f"Error while transferring {asset}/{symbol} {amount} from iso to cross")
            self.errorLog(f"Error while transferring {asset}/{symbol} {amount} from iso to cross")
            self.log(f"Error -: {e}")
            self.errorLog(f"Error -: {e}")
            self.clearPastTrade()
            sys.exit()

    def transferAvailableMoneyOutOfISO(self, currTime, symbol):
        try:
            self.log(f"{currTime.strftime('%Y-%m-%d %H:%M:%S')} Transferring Money Out Of ISO Wallet")
            self.orderLogs(f"{currTime.strftime('%Y-%m-%d %H:%M:%S')} Transferring Money Out Of ISO Wallet")

            if self.onlyISO:
                self.log(f"Only Iso Coin so using spot account for {self.baseAsset}")

            info = self.client.get_isolated_margin_account()
            assetInfo = next((item for item in info['assets'] if item["symbol"] == symbol), None)

            baseAssetFree = float((assetInfo["baseAsset"])["free"])
            quoteAssetFree = float((assetInfo["quoteAsset"])["free"])

            baseAssetFees = float((assetInfo["baseAsset"])["borrowed"])
            quoteAssetFees = float((assetInfo["quoteAsset"])["borrowed"])

            self.log(f"{self.baseAsset} Free -: {baseAssetFree}, {self.baseAsset} Borrowed -: {baseAssetFees}")
            self.log(f"{self.coinPair} Free -: {quoteAssetFree}, {self.coinPair} Borrowed -: {quoteAssetFees}")

            if baseAssetFree > 0 and baseAssetFees > 0:
                self.log(f"Repaying the {self.baseAsset} borrowed")

                if baseAssetFees > baseAssetFree:
                    self.client.repay_margin_loan(asset=self.baseAsset, amount=f'{baseAssetFree}', isIsolated=True, symbol=symbol)
                    baseAssetFees = baseAssetFees - baseAssetFree
                elif baseAssetFees <= baseAssetFree:
                    self.client.repay_margin_loan(asset=self.baseAsset, amount=f'{baseAssetFees}', isIsolated=True, symbol=symbol)
                    baseAssetFees = 0

            if quoteAssetFree > 0 and quoteAssetFees > 0:
                self.log(f"Repaying the {self.coinPair} borrowed")

                if quoteAssetFees > quoteAssetFree:
                    self.client.repay_margin_loan(asset=self.coinPair, amount=f'{quoteAssetFree}', isIsolated=True, symbol=symbol)
                    quoteAssetFees = quoteAssetFees - quoteAssetFree
                elif quoteAssetFees <= quoteAssetFree:
                    self.client.repay_margin_loan(asset=self.coinPair, amount=f'{quoteAssetFree}', isIsolated=True, symbol=symbol)
                    quoteAssetFees = 0

            self.log(f"{self.baseAsset} Free -: {baseAssetFree}, {self.baseAsset} Borrowed -: {baseAssetFees}")
            self.log(f"{self.coinPair} Free -: {quoteAssetFree}, {self.coinPair} Borrowed -: {quoteAssetFees}")

            if baseAssetFees > 0:
                if self.onlyISO:
                    self.log(f"Transferring {self.baseAsset} from spot to iso for left borrowed amount")
                    self.transferSPOTtoISOLATEDMARGIN(asset=self.baseAsset, symbol=symbol, amount=baseAssetFees)
                else:
                    self.log(f"Transferring {self.baseAsset} from cross to iso for left borrowed amount")
                    self.transferCROSStoISOLATEDMARGIN(asset=self.baseAsset, symbol=symbol, amount=baseAssetFees)

                self.log(f"Repaying the {self.baseAsset} borrowed")
                self.client.repay_margin_loan(asset=self.baseAsset, amount=f'{baseAssetFees}', isIsolated=True, symbol=symbol)

            if quoteAssetFees > 0:
                self.log(f"Transferring {self.coinPair} from cross to iso for left borrowed amount")
                self.transferCROSStoISOLATEDMARGIN(asset=self.coinPair, symbol=symbol, amount=quoteAssetFees)

                self.log(f"Repaying the {self.coinPair} borrowed")
                self.client.repay_margin_loan(asset=self.coinPair, amount=f'{quoteAssetFees}', isIsolated=True, symbol=symbol)

            coinPairMaxTransfer = self.client.get_max_margin_transfer(asset=self.coinPair, isolatedSymbol=symbol)
            coinPairMaxTransfer = float(coinPairMaxTransfer['amount'])

            baseAssetMaxTransfer = self.client.get_max_margin_transfer(asset=self.baseAsset, isolatedSymbol=symbol)
            baseAssetMaxTransfer = float(baseAssetMaxTransfer['amount'])

            self.log(f"{self.coinPair} Max Transfer Allowed -: {coinPairMaxTransfer}")
            self.log(f"{self.baseAsset} Max Transfer Allowed -: {baseAssetMaxTransfer}")

            if coinPairMaxTransfer > 0:
                self.log(f"Transferring {self.coinPair} from iso to cross")
                self.transferISOLOATEDMARGINtoCROSS(asset=self.coinPair, symbol=symbol, amount=coinPairMaxTransfer)

            if baseAssetMaxTransfer > 0:
                if self.onlyISO:
                    self.log(f"Transferring {self.baseAsset} from iso to spot")
                    self.transferISOLATEDMARGINtoSPOT(asset=self.baseAsset, symbol=symbol, amount=baseAssetMaxTransfer)
                else:
                    self.log(f"Transferring {self.baseAsset} from iso to cross")
                    self.transferISOLOATEDMARGINtoCROSS(asset=self.baseAsset, symbol=symbol, amount=baseAssetMaxTransfer)

            self.log(f"{currTime.strftime('%Y-%m-%d %H:%M:%S')} Money Transferred Successfully Out Of ISO Wallet")
            self.orderLogs(f"{currTime.strftime('%Y-%m-%d %H:%M:%S')} Money Transferred Successfully Out Of ISO Wallet")
        except Exception as e:
            self.log(f"{currTime.strftime('%Y-%m-%d %H:%M:%S')} Got a Error while transferring money out of iso wallet")
            self.errorLog(f"{currTime.strftime('%Y-%m-%d %H:%M:%S')} Got a Error while transferring money out of iso wallet")
            self.log(f"Error -: {e}")
            self.errorLog(f"Error -: {e}")
            self.clearPastTrade()
            sys.exit()

    def placeEntryOrder(self, row):
        walletFound = self.findWallet(alwaysCross=True)

        if not walletFound:
            self.log(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Entry Order cancelled because no wallet found")
            self.orderLogs(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Entry Order cancelled because no wallet found")

            return False

        if self.current_order["TYPE"] == "LONG":
            price = row["High"] + self.entryTickOffset
        else:
            price = row["Low"] - self.entryTickOffset

        amount = self.minPositionSizing(row)
        amount = round_down(self.decimals, amount)

        if self.coinPair == "USDT":
            if amount * price < 11:
                amount = 11 / price
                amount = round_down(self.decimals, amount)

            if amount * price < 11:
                amount = 15 / price
                amount = round_down(self.decimals, amount)

        if self.coinPair == "BTC" or self.coinPair == "ETH":
            if amount < self.minQty:
                amount = self.minQty + (0.2 * self.minQty)
                amount = round_down(self.decimals, amount)

            if (amount * price) < self.minNotional:
                amount = (self.minNotional + (0.2 * self.minNotional)) / price
                amount = round_down(self.decimals, amount)

        originalAmount = amount
        originalPrice = price
        self.current_order["Original Entry Order Price"] = originalPrice
        self.current_order["Original Entry Order Amount"] = originalAmount

        self.current_order["ENTRYORDER_PRICE"] = price
        self.current_order["ENTRYORDER_MOVED"] = 0

        self.current_order["AMOUNT"] = amount

        usdtSPOTBalance, usdtCROSSBalance, btcSPOTBalance, btcCROSSBalance, ethSPOTBalance, ethCROSSBalance = self.accountBalance()

        if self.current_order['WALLET'] != "CROSS 3X":
            self.current_order["WALLET_MULTIPLICATION_RATIO"] = self.gParams.get(f"wallet_iso{self.current_order['WALLET']}")
            toTransfer = (amount * price) / self.gParams.get(f"wallet_iso{self.current_order['WALLET']}")

            if self.coinPair == "BTC":
                crossBalance = btcCROSSBalance
            else:
                crossBalance = usdtCROSSBalance

            if float(crossBalance) <= float(toTransfer):
                self.log(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} {self.coinPair} CROSS Balance less then required balance. {self.coinPair} Cross Balance - {crossBalance}, Required Balance - {toTransfer}, Amount - {amount}")
                self.orderLogs(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} {self.coinPair} CROSS Balance less then required balance. {self.coinPair} Cross Balance - {crossBalance}, Required Balance - {toTransfer}, Amount - {amount}")

                newAmount = originalAmount
                for i in range(self.quantityPercentageDownTimes):
                    newAmount = newAmount - ((self.quantityPercentageDown / 100) * newAmount)
                    newAmount = round_down(self.decimals, newAmount)
                    newToTransfer = (newAmount * price) / self.gParams.get(f"wallet_iso{self.current_order['WALLET']}")

                    self.log(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Changing Amount to {newAmount}. BTC Cross Balance - {btcCROSSBalance}, Required Balance - {newToTransfer}, Amount - {newAmount}")
                    self.orderLogs(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Changing Amount to {newAmount}. BTC Cross Balance - {btcCROSSBalance}, Required Balance - {newToTransfer}, Amount - {newAmount}")

                    if float(crossBalance) >= float(newToTransfer):
                        break

                toTransfer = (newAmount * price) / self.gParams.get(f"wallet_iso{self.current_order['WALLET']}")

                if float(crossBalance) <= float(toTransfer):
                    self.current_order["AMOUNT"] = newAmount

                    if self.onlyISO:
                        self.log(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Insufficient Balance for the trade after changing the amount. {self.coinPair} Cross Balance - {crossBalance}, Required Balance - {toTransfer}, Amount - {newAmount}")
                        self.orderLogs(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Insufficient Balance for the trade after changing the amount. {self.coinPair} Cross Balance - {crossBalance}, Required Balance - {toTransfer}, Amount - {newAmount}")

                        self.insufficientFundInCrossToTransferLog(crossBalance=btcCROSSBalance, transferred=toTransfer)
                        self.checkEntryOrderPrice = False

                        return False
                    else:
                        self.log(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Insufficient Balance for the trade after changing the amount. Changing Wallet to CROSS 3X, BTC Cross Balance - {btcCROSSBalance}, Required Balance - {toTransfer}, Amount - {newAmount}")
                        self.orderLogs(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Insufficient Balance for the trade after changing the amount. Changing Wallet to CROSS 3X, BTC Cross Balance - {btcCROSSBalance}, Required Balance - {toTransfer}, Amount - {newAmount}")
                        self.current_order['WALLET'] = "CROSS 3X"
                else:
                    self.log(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Got sufficient balance now after changing the amount. {self.coinPair} Cross Balance - {crossBalance}, Required Balance - {toTransfer}, Final Amount - {newAmount}")
                    self.orderLogs(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Got sufficient balance now after changing the amount. {self.coinPair} Cross Balance - {crossBalance}, Required Balance - {toTransfer}, Final Amount - {newAmount}")
                    self.current_order["TRANSFERRED"] = toTransfer
                    self.current_order["AMOUNT"] = newAmount
                    amount = newAmount
                    self.transferCROSStoISOLATEDMARGIN(asset="BTC", symbol=self.marginSymbol, amount=toTransfer)
            else:
                self.current_order["TRANSFERRED"] = toTransfer
                self.transferCROSStoISOLATEDMARGIN(asset=self.coinPair, symbol=self.marginSymbol, amount=toTransfer)

        if self.current_order['WALLET'] == "CROSS 3X":
            newAmount = originalAmount

            coinPairMaxBorrow = self.client.get_max_margin_loan(asset=self.coinPair)
            coinPairMaxTransfer = self.client.get_max_margin_transfer(asset=self.coinPair)

            coinPairMaxBorrow = float(coinPairMaxBorrow["amount"])
            coinPairMaxTransfer = float(coinPairMaxTransfer["amount"])

            coinPairBorrowAllowed = coinPairMaxBorrow + coinPairMaxTransfer

            assetMaxBorrow = self.client.get_max_margin_loan(asset=self.baseAsset)
            assetMaxTransfer = self.client.get_max_margin_transfer(asset=self.baseAsset)

            assetMaxBorrow = float(assetMaxBorrow["amount"])
            assetMaxTransfer = float(assetMaxTransfer["amount"])

            assetBorrowAllowed = assetMaxBorrow + assetMaxTransfer

            self.current_order["MAX_BORROW_LIMIT_COINPAIR"] = coinPairBorrowAllowed
            self.current_order["MAX_BORROW_LIMIT_ASSET"] = assetBorrowAllowed

            if self.current_order["TYPE"] == "LONG":
                toTransfer = (newAmount * price)

                if coinPairBorrowAllowed <= toTransfer:
                    self.log(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} CROSS Borrow Limit less then required balance. Borrow Limit - {coinPairBorrowAllowed}, Required Balance - {toTransfer}, Amount - {amount}")
                    self.orderLogs(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} CROSS Borrow Limit less then required balance. Borrow Limit - {coinPairBorrowAllowed}, Required Balance - {toTransfer}, Amount - {amount}")

                    for i in range(self.quantityPercentageDownTimes):
                        newAmount = newAmount - ((self.quantityPercentageDown / 100) * newAmount)
                        newAmount = round_down(self.decimals, newAmount)
                        newToTransfer = (newAmount * price)

                        self.log(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Changing Amount to {newAmount}. Borrow Limit - {coinPairBorrowAllowed}, Required Balance - {newToTransfer}, Amount - {newAmount}")
                        self.orderLogs(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Changing Amount to {newAmount}. Borrow Limit - {coinPairBorrowAllowed}, Required Balance - {newToTransfer}, Amount - {newAmount}")

                        if coinPairBorrowAllowed >= float(newToTransfer):
                            break

                    toTransfer = (newAmount * price)
                    if coinPairBorrowAllowed <= float(toTransfer):
                        self.log(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Insufficient Balance for the trade after changing the amount. Borrow Limit - {coinPairBorrowAllowed}, Required Balance - {toTransfer}, Amount - {newAmount}")
                        self.orderLogs(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Insufficient Balance for the trade after changing the amount. Borrow Limit - {coinPairBorrowAllowed}, Required Balance - {toTransfer}, Amount - {newAmount}")
                        self.current_order["AMOUNT"] = newAmount
                        self.cross3xTradeCancelledDueToBorrowLimitLog()
                        self.checkEntryOrderPrice = False
                        return False
                    else:
                        self.log(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Got sufficient balance now after changing the amount. Borrow Limit - {coinPairBorrowAllowed}, Required Balance - {toTransfer}, Final Amount - {newAmount}")
                        self.orderLogs(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Got sufficient balance now after changing the amount. Borrow Limit - {coinPairBorrowAllowed}, Required Balance - {toTransfer}, Amount - {newAmount}")
                        self.current_order["AMOUNT"] = newAmount
                        amount = newAmount
            else:
                if assetBorrowAllowed <= float(newAmount):
                    self.log(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} CROSS Borrow Limit less then required balance. Borrow Limit - {assetBorrowAllowed}, Amount - {amount}")
                    self.orderLogs(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} CROSS Borrow Limit less then required balance. Borrow Limit - {assetBorrowAllowed}, Amount - {amount}")

                    for i in range(self.quantityPercentageDownTimes):
                        newAmount = newAmount - ((self.quantityPercentageDown / 100) * newAmount)
                        newAmount = round_down(self.decimals, newAmount)

                        self.log(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Changing Amount to {newAmount}. Borrow Limit - {assetBorrowAllowed}, Amount - {newAmount}")
                        self.orderLogs(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Changing Amount to {newAmount}. Borrow Limit - {assetBorrowAllowed}, Amount - {newAmount}")

                        if assetBorrowAllowed >= float(newAmount):
                            break

                    if assetBorrowAllowed <= float(newAmount):
                        self.log(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Insufficient Balance for the trade after changing the amount. Borrow Limit - {assetBorrowAllowed}, Amount - {newAmount}")
                        self.orderLogs(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Insufficient Balance for the trade after changing the amount. Borrow Limit - {assetBorrowAllowed}, Amount - {newAmount}")
                        self.current_order["AMOUNT"] = newAmount
                        self.cross3xTradeCancelledDueToBorrowLimitLog()
                        self.checkEntryOrderPrice = False
                        return False
                    else:
                        self.log(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Got sufficient balance now after changing the amount. Borrow Limit - {assetBorrowAllowed}, Final Amount - {newAmount}")
                        self.orderLogs(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Got sufficient balance now after changing the amount. Borrow Limit - {assetBorrowAllowed},Final Amount - {newAmount}")
                        self.current_order["AMOUNT"] = newAmount
                        amount = newAmount

        else:
            coinPairMaxBorrow = self.client.get_max_margin_loan(asset=self.coinPair, isolatedSymbol=self.marginSymbol)
            coinPairMaxTransfer = self.client.get_max_margin_transfer(asset=self.coinPair, isolatedSymbol=self.marginSymbol)

            coinPairMaxBorrow = float(coinPairMaxBorrow["amount"])
            coinPairMaxTransfer = float(coinPairMaxTransfer["amount"])

            coinPairBorrowAllowed = coinPairMaxBorrow + coinPairMaxTransfer

            assetMaxBorrow = self.client.get_max_margin_loan(asset=self.baseAsset, isolatedSymbol=self.marginSymbol)
            assetMaxTransfer = self.client.get_max_margin_transfer(asset=self.baseAsset, isolatedSymbol=self.marginSymbol)

            assetMaxBorrow = float(assetMaxBorrow["amount"])
            assetMaxTransfer = float(assetMaxTransfer["amount"])

            assetBorrowAllowed = assetMaxBorrow + assetMaxTransfer

            self.current_order["MAX_BORROW_LIMIT_COINPAIR"] = coinPairBorrowAllowed
            self.current_order["MAX_BORROW_LIMIT_ASSET"] = assetBorrowAllowed
            self.current_order["AMOUNT"] = amount

            if self.current_order["TYPE"] == "LONG":
                requiredBalance = float(amount) * float(price)
                if float(coinPairBorrowAllowed) < float(requiredBalance):
                    amount = (float(coinPairBorrowAllowed) / float(price)) * 0.99
                    self.current_order["AMOUNT"] = amount

                    self.log(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Coinpair Borrow Limit less then required balance. Changing Amount to Borrow Limit.  Borrow Limit - {coinPairBorrowAllowed}, Balance Required - {requiredBalance}")
                    self.orderLogs(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Coinpair Borrow Limit less then required balance. Changing Amount to Borrow Limit.  Borrow Limit - {coinPairBorrowAllowed}, Balance Required - {requiredBalance}")

                    # self.isoTradeCancelledDueToBorrowLimitLog()
                    # self.checkEntryOrderPrice = False
                    # self.transferAvailableMoneyOutOfISO(currTime=row.name, symbol=self.marginSymbol)
                    # return False
            else:
                if float(assetBorrowAllowed) < float(amount):
                    amount = (float(assetBorrowAllowed)) * 0.99
                    self.current_order["AMOUNT"] = amount

                    self.log(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Asset Borrow Limit less then required amount. Changing Amount to Borrow Limit. Borrow Limit - {assetBorrowAllowed}, Amount - {amount}")
                    self.orderLogs(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Asset Borrow Limit less then required amount. Changing Amount to Borrow Limit.  Borrow Limit - {assetBorrowAllowed}, Amount - {amount}")

                    # self.isoTradeCancelledDueToBorrowLimitLog()
                    # self.checkEntryOrderPrice = False
                    # self.transferAvailableMoneyOutOfISO(currTime=row.name, symbol=self.marginSymbol)
                    # return False

        self.current_order["AMOUNT"] = amount

        self.log(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Entry Order set with price - {price} and amount - {amount}")
        self.orderLogs(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Entry Order set with price - {price} and amount - {amount}")
        self.placedOrderLogs()

        self.checkEntryOrderPrice = True
        return True

    def moveEntryOrder(self, row):
        if self.current_order['WALLET'] != "CROSS 3X":
            self.transferAvailableMoneyOutOfISO(currTime=row.name, symbol=self.marginSymbol)

        if self.current_order["TYPE"] == "LONG":
            price = row["High"] + self.entryTickOffset
            amount = self.current_order["AMOUNT"]
        else:
            price = row["Low"] - self.entryTickOffset
            amount = self.current_order["AMOUNT"]

        if self.coinPair == "USDT":
            if amount * price < 11:
                amount = 11 / price
                amount = round_down(self.decimals, amount)

            if amount * price < 11:
                amount = 15 / price
                amount = round_down(self.decimals, amount)

        if self.coinPair == "BTC" or self.coinPair == "ETH":
            if amount < self.minQty:
                amount = self.minQty + (0.2 * self.minQty)
                amount = round_down(self.decimals, amount)

            if (amount * price) < self.minNotional:
                amount = (self.minNotional + (0.2 * self.minNotional)) / price
                amount = round_down(self.decimals, amount)

        self.current_order["ENTRYORDER_PRICE"] = price
        self.current_order["ENTRYORDER_MOVED"] = self.orderAlreadyOpenFor

        originalAmount = amount
        self.current_order["AMOUNT"] = amount

        usdtSPOTBalance, usdtCROSSBalance, btcSPOTBalance, btcCROSSBalance, ethSPOTBalance, ethCROSSBalance = self.accountBalance()

        if self.current_order['WALLET'] != "CROSS 3X":
            self.current_order["WALLET_MULTIPLICATION_RATIO"] = self.gParams.get(f"wallet_iso{self.current_order['WALLET']}")
            toTransfer = (amount * price) / self.gParams.get(f"wallet_iso{self.current_order['WALLET']}")

            if self.coinPair == "BTC":
                crossBalance = btcCROSSBalance
            else:
                crossBalance = usdtCROSSBalance

            if float(crossBalance) <= float(toTransfer):
                self.log(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} {self.coinPair} CROSS Balance less then required balance. {self.coinPair} Cross Balance - {crossBalance}, Required Balance - {toTransfer}, Amount - {amount}")
                self.orderLogs(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} {self.coinPair} CROSS Balance less then required balance. {self.coinPair} Cross Balance - {crossBalance}, Required Balance - {toTransfer}, Amount - {amount}")

                newAmount = originalAmount
                for i in range(self.quantityPercentageDownTimes):
                    newAmount = newAmount - ((self.quantityPercentageDown / 100) * newAmount)
                    newAmount = round_down(self.decimals, newAmount)
                    newToTransfer = (newAmount * price) / self.gParams.get(f"wallet_iso{self.current_order['WALLET']}")

                    self.log(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Changing Amount to {newAmount}. BTC Cross Balance - {btcCROSSBalance}, Required Balance - {newToTransfer}, Amount - {newAmount}")
                    self.orderLogs(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Changing Amount to {newAmount}. BTC Cross Balance - {btcCROSSBalance}, Required Balance - {newToTransfer}, Amount - {newAmount}")

                    if float(crossBalance) >= float(newToTransfer):
                        break

                toTransfer = (newAmount * price) / self.gParams.get(f"wallet_iso{self.current_order['WALLET']}")

                if float(crossBalance) <= float(toTransfer):
                    self.current_order["AMOUNT"] = newAmount

                    if self.onlyISO:
                        self.log(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Insufficient Balance for the trade after changing the amount. {self.coinPair} Cross Balance - {crossBalance}, Required Balance - {toTransfer}, Amount - {newAmount}")
                        self.orderLogs(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Insufficient Balance for the trade after changing the amount. {self.coinPair} Cross Balance - {crossBalance}, Required Balance - {toTransfer}, Amount - {newAmount}")

                        self.insufficientFundInCrossToTransferLog(crossBalance=btcCROSSBalance, transferred=toTransfer)
                        self.checkEntryOrderPrice = False

                        return False
                    else:
                        self.log(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Insufficient Balance for the trade after changing the amount. Changing Wallet to CROSS 3X, BTC Cross Balance - {btcCROSSBalance}, Required Balance - {toTransfer}, Amount - {newAmount}")
                        self.orderLogs(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Insufficient Balance for the trade after changing the amount. Changing Wallet to CROSS 3X, BTC Cross Balance - {btcCROSSBalance}, Required Balance - {toTransfer}, Amount - {newAmount}")
                        self.current_order['WALLET'] = "CROSS 3X"
                else:
                    self.log(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Got sufficient balance now after changing the amount. {self.coinPair} Cross Balance - {crossBalance}, Required Balance - {toTransfer}, Final Amount - {newAmount}")
                    self.orderLogs(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Got sufficient balance now after changing the amount. {self.coinPair} Cross Balance - {crossBalance}, Required Balance - {toTransfer}, Final Amount - {newAmount}")
                    self.current_order["TRANSFERRED"] = toTransfer
                    self.current_order["AMOUNT"] = newAmount
                    amount = newAmount
                    self.transferCROSStoISOLATEDMARGIN(asset="BTC", symbol=self.marginSymbol, amount=toTransfer)
            else:
                self.current_order["TRANSFERRED"] = toTransfer
                self.transferCROSStoISOLATEDMARGIN(asset=self.coinPair, symbol=self.marginSymbol, amount=toTransfer)

        if self.current_order['WALLET'] == "CROSS 3X":
            newAmount = originalAmount

            coinPairMaxBorrow = self.client.get_max_margin_loan(asset=self.coinPair)
            coinPairMaxTransfer = self.client.get_max_margin_transfer(asset=self.coinPair)

            coinPairMaxBorrow = float(coinPairMaxBorrow["amount"])
            coinPairMaxTransfer = float(coinPairMaxTransfer["amount"])

            coinPairBorrowAllowed = coinPairMaxBorrow + coinPairMaxTransfer

            assetMaxBorrow = self.client.get_max_margin_loan(asset=self.baseAsset)
            assetMaxTransfer = self.client.get_max_margin_transfer(asset=self.baseAsset)

            assetMaxBorrow = float(assetMaxBorrow["amount"])
            assetMaxTransfer = float(assetMaxTransfer["amount"])

            assetBorrowAllowed = assetMaxBorrow + assetMaxTransfer

            self.current_order["MAX_BORROW_LIMIT_COINPAIR"] = coinPairBorrowAllowed
            self.current_order["MAX_BORROW_LIMIT_ASSET"] = assetBorrowAllowed

            if self.current_order["TYPE"] == "LONG":
                toTransfer = (newAmount * price)

                if coinPairBorrowAllowed <= toTransfer:
                    self.log(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} CROSS Borrow Limit less then required balance. Borrow Limit - {coinPairBorrowAllowed}, Required Balance - {toTransfer}, Amount - {amount}")
                    self.orderLogs(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} CROSS Borrow Limit less then required balance. Borrow Limit - {coinPairBorrowAllowed}, Required Balance - {toTransfer}, Amount - {amount}")

                    for i in range(self.quantityPercentageDownTimes):
                        newAmount = newAmount - ((self.quantityPercentageDown / 100) * newAmount)
                        newAmount = round_down(self.decimals, newAmount)
                        newToTransfer = (newAmount * price)

                        self.log(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Changing Amount to {newAmount}. Borrow Limit - {coinPairBorrowAllowed}, Required Balance - {newToTransfer}, Amount - {newAmount}")
                        self.orderLogs(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Changing Amount to {newAmount}. Borrow Limit - {coinPairBorrowAllowed}, Required Balance - {newToTransfer}, Amount - {newAmount}")

                        if coinPairBorrowAllowed >= float(newToTransfer):
                            break

                    toTransfer = (newAmount * price)
                    if coinPairBorrowAllowed <= float(toTransfer):
                        self.log(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Insufficient Balance for the trade after changing the amount. Borrow Limit - {coinPairBorrowAllowed}, Required Balance - {toTransfer}, Amount - {newAmount}")
                        self.orderLogs(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Insufficient Balance for the trade after changing the amount. Borrow Limit - {coinPairBorrowAllowed}, Required Balance - {toTransfer}, Amount - {newAmount}")
                        self.current_order["AMOUNT"] = newAmount
                        self.cross3xTradeCancelledDueToBorrowLimitLog()
                        self.checkEntryOrderPrice = False
                        return False
                    else:
                        self.log(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Got sufficient balance now after changing the amount. Borrow Limit - {coinPairBorrowAllowed}, Required Balance - {toTransfer}, Final Amount - {newAmount}")
                        self.orderLogs(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Got sufficient balance now after changing the amount. Borrow Limit - {coinPairBorrowAllowed}, Required Balance - {toTransfer}, Amount - {newAmount}")
                        self.current_order["AMOUNT"] = newAmount
                        amount = newAmount
            else:
                if assetBorrowAllowed <= float(newAmount):
                    self.log(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} CROSS Borrow Limit less then required balance. Borrow Limit - {assetBorrowAllowed}, Amount - {amount}")
                    self.orderLogs(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} CROSS Borrow Limit less then required balance. Borrow Limit - {assetBorrowAllowed}, Amount - {amount}")

                    for i in range(self.quantityPercentageDownTimes):
                        newAmount = newAmount - ((self.quantityPercentageDown / 100) * newAmount)
                        newAmount = round_down(self.decimals, newAmount)

                        self.log(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Changing Amount to {newAmount}. Borrow Limit - {assetBorrowAllowed}, Amount - {newAmount}")
                        self.orderLogs(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Changing Amount to {newAmount}. Borrow Limit - {assetBorrowAllowed}, Amount - {newAmount}")

                        if assetBorrowAllowed >= float(newAmount):
                            break

                    if assetBorrowAllowed <= float(newAmount):
                        self.log(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Insufficient Balance for the trade after changing the amount. Borrow Limit - {assetBorrowAllowed}, Amount - {newAmount}")
                        self.orderLogs(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Insufficient Balance for the trade after changing the amount. Borrow Limit - {assetBorrowAllowed}, Amount - {newAmount}")
                        self.current_order["AMOUNT"] = newAmount
                        self.cross3xTradeCancelledDueToBorrowLimitLog()
                        self.checkEntryOrderPrice = False
                        return False
                    else:
                        self.log(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Got sufficient balance now after changing the amount. Borrow Limit - {assetBorrowAllowed}, Final Amount - {newAmount}")
                        self.orderLogs(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Got sufficient balance now after changing the amount. Borrow Limit - {assetBorrowAllowed},Final Amount - {newAmount}")
                        self.current_order["AMOUNT"] = newAmount
                        amount = newAmount

        else:
            coinPairMaxBorrow = self.client.get_max_margin_loan(asset=self.coinPair, isolatedSymbol=self.marginSymbol)
            coinPairMaxTransfer = self.client.get_max_margin_transfer(asset=self.coinPair,
                                                                      isolatedSymbol=self.marginSymbol)

            coinPairMaxBorrow = float(coinPairMaxBorrow["amount"])
            coinPairMaxTransfer = float(coinPairMaxTransfer["amount"])

            coinPairBorrowAllowed = coinPairMaxBorrow + coinPairMaxTransfer

            assetMaxBorrow = self.client.get_max_margin_loan(asset=self.baseAsset, isolatedSymbol=self.marginSymbol)
            assetMaxTransfer = self.client.get_max_margin_transfer(asset=self.baseAsset,
                                                                   isolatedSymbol=self.marginSymbol)

            assetMaxBorrow = float(assetMaxBorrow["amount"])
            assetMaxTransfer = float(assetMaxTransfer["amount"])

            assetBorrowAllowed = assetMaxBorrow + assetMaxTransfer

            self.current_order["MAX_BORROW_LIMIT_COINPAIR"] = coinPairBorrowAllowed
            self.current_order["MAX_BORROW_LIMIT_ASSET"] = assetBorrowAllowed
            self.current_order["AMOUNT"] = amount

            if self.current_order["TYPE"] == "LONG":
                requiredBalance = float(amount) * float(price)
                if float(coinPairBorrowAllowed) < float(requiredBalance):
                    amount = (float(coinPairBorrowAllowed) / float(price)) * 0.99
                    self.current_order["AMOUNT"] = amount

                    self.log(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Coinpair Borrow Limit less then required balance. Changing Amount to Borrow Limit. Borrow Limit - {coinPairBorrowAllowed}, Balance Required - {requiredBalance}")
                    self.orderLogs(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Coinpair Borrow Limit less then required balance. Changing Amount to Borrow Limit. Borrow Limit - {coinPairBorrowAllowed}, Balance Required - {requiredBalance}")

                    # self.isoTradeCancelledDueToBorrowLimitLog()
                    # self.checkEntryOrderPrice = False
                    # self.transferAvailableMoneyOutOfISO(currTime=row.name, symbol=self.marginSymbol)
                    # return False
            else:
                if float(assetBorrowAllowed) < float(amount):
                    amount = (float(assetBorrowAllowed)) * 0.99
                    self.current_order["AMOUNT"] = amount

                    self.log(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Asset Borrow Limit less then required amount. Changing Amount to Borrow Limit. Borrow Limit - {assetBorrowAllowed}, Amount - {amount}")
                    self.orderLogs(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Asset Borrow Limit less then required amount. Changing Amount to Borrow Limit. Borrow Limit - {assetBorrowAllowed}, Amount - {amount}")

                    # self.isoTradeCancelledDueToBorrowLimitLog()
                    # self.checkEntryOrderPrice = False
                    # self.transferAvailableMoneyOutOfISO(currTime=row.name, symbol=self.marginSymbol)
                    # return False

        self.current_order["AMOUNT"] = amount

        self.log(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Moved Entry Order set with price - {price} and amount - {amount}")
        self.orderLogs(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Moved Entry Order set with price - {price} and amount - {amount}")
        self.movedOrderLogs()

        self.checkEntryOrderPrice = True
        return True

    def fakeEntryOrder(self, row):
        self.current_order["WALLET"] = "CROSS 3X"

        if self.current_order["TYPE"] == "LONG":
            price = row["High"] + self.entryTickOffset
        else:
            price = row["Low"] - self.entryTickOffset

        self.current_order["Original Entry Order Price"] = price
        self.current_order["Original Entry Order Amount"] = self.minPositionSizing(row)

        self.current_order["ENTRYORDER_PRICE"] = price
        self.current_order["ENTRYORDER_MOVED"] = 0

        self.current_order["MAX_BORROW_LIMIT_COINPAIR"] = 0
        self.current_order["MAX_BORROW_LIMIT_ASSET"] = 0

        self.current_order["AMOUNT"] = 0

        self.log(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Cooldown Entry Order set with price - {price} and amount - 0")
        self.orderLogs(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Cooldown Entry Order set with price - {price} and amount - 0")

        self.checkEntryOrderPrice = True
        return True

    def fakeMoveEntryOrder(self, row):
        if self.current_order["TYPE"] == "LONG":
            price = row["High"] + self.entryTickOffset
        else:
            price = row["Low"] - self.entryTickOffset

        self.current_order["ENTRYORDER_PRICE"] = price
        self.current_order["ENTRYORDER_MOVED"] = self.orderAlreadyOpenFor

        self.current_order["MAX_BORROW_LIMIT_COINPAIR"] = 0
        self.current_order["MAX_BORROW_LIMIT_ASSET"] = 0

        self.log(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Cooldown Moved Entry Order set with price - {price} and amount - 0")
        self.orderLogs(f"{row.name.strftime('%Y-%m-%d %H:%M:%S')} Cooldown Moved Entry Order set with price - {price} and amount - 0")

        self.checkEntryOrderPrice = True
        return True

    def placeMarketEntryOrder(self, closePrice):
        utcTime = datetime.datetime.utcnow()
        if self.checkEntryOrderPrice:
            if self.current_order["TYPE"] == "LONG":
                if closePrice >= self.current_order["ENTRYORDER_PRICE"]:
                    self.checkEntryOrderPrice = False

                    if self.current_order['WALLET'] == "CROSS 3X":
                        isolated = False
                    else:
                        isolated = True

                    try:
                        if self.fakeOrder:
                            self.log(f"{utcTime.strftime('%Y-%m-%d %H:%M:%S')} Placing Cooldown Long Market Entry Order with amount - {self.current_order['AMOUNT']}")
                            self.orderLogs(f"{utcTime.strftime('%Y-%m-%d %H:%M:%S')} Placing Cooldown Long Market Entry Order with amount - {self.current_order['AMOUNT']}")
                        else:
                            self.log(f"{utcTime.strftime('%Y-%m-%d %H:%M:%S')} Placing Long Market Entry Order with amount - {self.current_order['AMOUNT']}")
                            self.orderLogs(f"{utcTime.strftime('%Y-%m-%d %H:%M:%S')} Placing Long Market Entry Order with amount - {self.current_order['AMOUNT']}")


                        if self.osl == "ALL":
                            if self.trailSL == "LTF":
                                prevCandle = self.ltfData.iloc[-1]
                                prevprevCandle = self.ltfData.iloc[-2]
                            elif self.trailSL == "DTF1":
                                prevCandle = self.dtf1Data.iloc[-1]
                                prevprevCandle = self.dtf1Data.iloc[-2]
                            elif self.trailSL == "DTF2":
                                prevCandle = self.dtf2Data.iloc[-1]
                                prevprevCandle = self.dtf2Data.iloc[-2]
                            elif self.trailSL == "DTF3":
                                prevCandle = self.dtf3Data.iloc[-1]
                                prevprevCandle = self.dtf3Data.iloc[-2]
                            elif self.trailSL == "DTF4":
                                prevCandle = self.dtf4Data.iloc[-1]
                                prevprevCandle = self.dtf4Data.iloc[-2]
                            elif self.trailSL == "DTF5":
                                prevCandle = self.dtf5Data.iloc[-1]
                                prevprevCandle = self.dtf5Data.iloc[-2]
                            elif self.trailSL == "DTF6":
                                prevCandle = self.dtf6Data.iloc[-1]
                                prevprevCandle = self.dtf6Data.iloc[-2]
                            elif self.trailSL == "DTF7":
                                prevCandle = self.dtf7Data.iloc[-1]
                                prevprevCandle = self.dtf7Data.iloc[-2]
                            else:
                                prevCandle = self.dtf8Data.iloc[-1]
                                prevprevCandle = self.dtf8Data.iloc[-2]
                        else:
                            prevCandle = self.ltfData.iloc[-1]
                            prevprevCandle = self.ltfData.iloc[-2]


                        lowprevCandle = prevCandle["Low"]
                        lowprevprevCandle = prevprevCandle["Low"]

                        lowestPrev = min(lowprevCandle, lowprevprevCandle)

                        self.current_order["ORIGINAL_STOPLOSSORDER_PRICE"] = lowestPrev - (lowestPrev * self.initialSLOffset)
                        self.current_order["STOPLOSSORDER_PRICE"] = lowestPrev - (lowestPrev * self.initialSLOffset)

                        slPerc = get_change(self.current_order["STOPLOSSORDER_PRICE"], self.current_order["ENTRYORDER_PRICE"])

                        if slPerc > self.maxSL:
                            if self.fakeOrder:
                                self.log(f"{utcTime.strftime('%Y-%m-%d %H:%M:%S')} Cooldown Entry Order Cancelled due to big initial stoploss ({slPerc})")
                                self.orderLogs(f"{utcTime.strftime('%Y-%m-%d %H:%M:%S')} Cooldown Entry Order Cancelled due to big initial stoploss ({slPerc})")
                            else:
                                self.log(f"{utcTime.strftime('%Y-%m-%d %H:%M:%S')} Entry Order Cancelled due to big initial stoploss ({slPerc})")
                                self.orderLogs(f"{utcTime.strftime('%Y-%m-%d %H:%M:%S')} Entry Order Cancelled due to big initial stoploss ({slPerc})")
                            self.clearPastTrade()
                        else:
                            if not self.fakeOrder:
                                long_order = self.client.create_margin_order(symbol=self.marginSymbol,
                                                                             isIsolated=isolated,
                                                                             side=SIDE_BUY,
                                                                             type=ORDER_TYPE_MARKET,
                                                                             sideEffectType="MARGIN_BUY",
                                                                             quantity=self.current_order["AMOUNT"])

                                avgEntryPrice = 0

                                for fill in long_order["fills"]:
                                    avgEntryPrice = avgEntryPrice + (float(fill["price"]) * float(fill["qty"]))

                                self.current_order["TRADE_STATUS"] = "MARKET ENTRY ORDER FILLED"

                                self.current_order["ENTRY_TIME"] = utcTime.strftime("%Y-%m-%d %H:%M")
                                self.current_order["ENTRYORDER_AVG_PRICE"] = float(avgEntryPrice / self.current_order["AMOUNT"])
                                self.current_order["ENTRYORDER_ORDERID"] = long_order["orderId"]
                                self.entryFilled = True

                                self.log(f"{utcTime.strftime('%Y-%m-%d %H:%M:%S')} Entry Order Placed and Filled Successfully at Market Price with Avg Entry Price is {float(avgEntryPrice / self.current_order['AMOUNT'])},Order ID is {long_order['orderId']}")
                                self.orderLogs(f"{utcTime.strftime('%Y-%m-%d %H:%M:%S')} Entry Order Placed and Filled Successfully at Market Price with Avg Entry Price is {float(avgEntryPrice / self.current_order['AMOUNT'])},Order ID is {long_order['orderId']}")
                                self.filledOrderLogs()

                                if self.current_order['WALLET'] != "CROSS 3X":
                                    info = self.client.get_isolated_margin_account()
                                    assetInfo = next((item for item in info['assets'] if item["symbol"] == self.marginSymbol), None)

                                    amount = float(assetInfo["baseAsset"]["free"])
                                    amount = round_down(self.decimals, amount)

                                    self.current_order["ENTRYORDER_ORIGINAL_AMOUNT"] = self.current_order["AMOUNT"]
                                    self.current_order["AMOUNT"] = amount

                                self.stopLossLongPosition(currtime=utcTime, price=self.current_order["ORIGINAL_STOPLOSSORDER_PRICE"])
                            else:
                                self.current_order["TRADE_STATUS"] = "MARKET ENTRY ORDER FILLED"

                                self.current_order["ENTRY_TIME"] = utcTime.strftime("%Y-%m-%d %H:%M")
                                self.current_order["ENTRYORDER_AVG_PRICE"] = closePrice
                                self.entryFilled = True

                                self.log(f"{utcTime.strftime('%Y-%m-%d %H:%M:%S')} Cooldown Entry Order Placed and Filled Successfully at Market Price with Avg Entry Price is {closePrice}")
                                self.orderLogs(f"{utcTime.strftime('%Y-%m-%d %H:%M:%S')} Cooldown Entry Order Placed and Filled Successfully at Market Price with Avg Entry Price is {closePrice}")

                                self.stopLossLongPosition(currtime=utcTime, price=self.current_order["ORIGINAL_STOPLOSSORDER_PRICE"])
                    except Exception as e:
                        self.log(f"{utcTime.strftime('%Y-%m-%d %H:%M:%S')} Got a Error while placing market entry order")
                        self.orderLogs(f"{utcTime.strftime('%Y-%m-%d %H:%M:%S')} Got a Error while placing market entry order")
                        self.errorLog(f"{utcTime.strftime('%Y-%m-%d %H:%M:%S')} Got a Error while placing market entry order")

                        self.log(f"Error -: {e}")
                        self.orderLogs(f"Error -: {e}")
                        self.errorLog(f"Error -: {e}")

                        self.clearPastTrade()
                        sys.exit()

                else:
                    self.checkEntryOrderPrice = True

            elif self.current_order["TYPE"] == "SHORT":
                if closePrice <= self.current_order["ENTRYORDER_PRICE"]:
                    self.checkEntryOrderPrice = False

                    if self.current_order['WALLET'] == "CROSS 3X":
                        isolated = False
                    else:
                        isolated = True

                    try:
                        if not self.fakeOrder:
                            self.log(f"{utcTime.strftime('%Y-%m-%d %H:%M:%S')} Placing Short Market Entry Order with amount - {self.current_order['AMOUNT']}")
                            self.orderLogs(f"{utcTime.strftime('%Y-%m-%d %H:%M:%S')} Placing Short Market Entry Order with amount - {self.current_order['AMOUNT']}")
                        else:
                            self.log(f"{utcTime.strftime('%Y-%m-%d %H:%M:%S')} Placing Cooldown Short Market Entry Order with amount - {self.current_order['AMOUNT']}")
                            self.orderLogs(f"{utcTime.strftime('%Y-%m-%d %H:%M:%S')} Placing Cooldown Short Market Entry Order with amount - {self.current_order['AMOUNT']}")

                        if self.osl == "ALL":
                            if self.trailSL == "LTF":
                                prevCandle = self.ltfData.iloc[-1]
                                prevprevCandle = self.ltfData.iloc[-2]
                            elif self.trailSL == "DTF1":
                                prevCandle = self.dtf1Data.iloc[-1]
                                prevprevCandle = self.dtf1Data.iloc[-2]
                            elif self.trailSL == "DTF2":
                                prevCandle = self.dtf2Data.iloc[-1]
                                prevprevCandle = self.dtf2Data.iloc[-2]
                            elif self.trailSL == "DTF3":
                                prevCandle = self.dtf3Data.iloc[-1]
                                prevprevCandle = self.dtf3Data.iloc[-2]
                            elif self.trailSL == "DTF4":
                                prevCandle = self.dtf4Data.iloc[-1]
                                prevprevCandle = self.dtf4Data.iloc[-2]
                            elif self.trailSL == "DTF5":
                                prevCandle = self.dtf5Data.iloc[-1]
                                prevprevCandle = self.dtf5Data.iloc[-2]
                            elif self.trailSL == "DTF6":
                                prevCandle = self.dtf6Data.iloc[-1]
                                prevprevCandle = self.dtf6Data.iloc[-2]
                            elif self.trailSL == "DTF7":
                                prevCandle = self.dtf7Data.iloc[-1]
                                prevprevCandle = self.dtf7Data.iloc[-2]
                            else:
                                prevCandle = self.dtf8Data.iloc[-1]
                                prevprevCandle = self.dtf8Data.iloc[-2]
                        else:
                            prevCandle = self.ltfData.iloc[-1]
                            prevprevCandle = self.ltfData.iloc[-2]

                        highprevCandle = prevCandle["High"]
                        highprevprevCandle = prevprevCandle["High"]

                        highestPrev = max(highprevCandle, highprevprevCandle)

                        self.current_order["ORIGINAL_STOPLOSSORDER_PRICE"] = highestPrev + (highestPrev * self.initialSLOffset)
                        self.current_order["STOPLOSSORDER_PRICE"] = highestPrev + (highestPrev * self.initialSLOffset)

                        slPerc = get_change(self.current_order["STOPLOSSORDER_PRICE"], self.current_order["ENTRYORDER_PRICE"])

                        if slPerc > self.maxSL:
                            if not self.fakeOrder:
                                self.log(f"{utcTime.strftime('%Y-%m-%d %H:%M:%S')} Entry Order Cancelled due to big initial stoploss ({slPerc})")
                                self.orderLogs(f"{utcTime.strftime('%Y-%m-%d %H:%M:%S')} Entry Order Cancelled due to big initial stoploss ({slPerc})")
                            else:
                                self.log(f"{utcTime.strftime('%Y-%m-%d %H:%M:%S')} Cooldown Entry Order Cancelled due to big initial stoploss ({slPerc})")
                                self.orderLogs(f"{utcTime.strftime('%Y-%m-%d %H:%M:%S')} Cooldown Entry Order Cancelled due to big initial stoploss ({slPerc})")
                            self.clearPastTrade()
                        else:
                            if not self.fakeOrder:
                                short_order = self.client.create_margin_order(symbol=self.marginSymbol,
                                                                              isIsolated=isolated,
                                                                              side=SIDE_SELL,
                                                                              type=ORDER_TYPE_MARKET,
                                                                              sideEffectType="MARGIN_BUY",
                                                                              quantity=self.current_order["AMOUNT"])

                                avgEntryPrice = 0

                                for fill in short_order["fills"]:
                                    avgEntryPrice = avgEntryPrice + (float(fill["price"]) * float(fill["qty"]))

                                self.current_order["TRADE_STATUS"] = "MAREKT ENTRY ORDER FILLED"

                                self.current_order["ENTRY_TIME"] = utcTime.strftime("%Y-%m-%d %H:%M")
                                self.current_order["ENTRYORDER_AVG_PRICE"] = float(avgEntryPrice / self.current_order["AMOUNT"])
                                self.current_order["ENTRYORDER_ORDERID"] = short_order["orderId"]
                                self.entryFilled = True

                                self.log(f"{utcTime.strftime('%Y-%m-%d %H:%M:%S')} Entry Order Placed and Filled Successfully at Market Price with Avg Entry Price is {float(avgEntryPrice / self.current_order['AMOUNT'])},Order ID is {short_order['orderId']}")
                                self.orderLogs(f"{utcTime.strftime('%Y-%m-%d %H:%M:%S')} Entry Order Placed and Filled Successfully at Market Price with Avg Entry Price is {float(avgEntryPrice / self.current_order['AMOUNT'])},Order ID is {short_order['orderId']}")
                                self.filledOrderLogs()

                                self.stopLossShortPosition(currtime=utcTime, price=self.current_order["ORIGINAL_STOPLOSSORDER_PRICE"])
                            else:
                                self.current_order["TRADE_STATUS"] = "MARKET ENTRY ORDER FILLED"

                                self.current_order["ENTRY_TIME"] = utcTime.strftime("%Y-%m-%d %H:%M")
                                self.current_order["ENTRYORDER_AVG_PRICE"] = closePrice
                                self.entryFilled = True

                                self.log(f"{utcTime.strftime('%Y-%m-%d %H:%M:%S')} Cooldown Entry Order Placed and Filled Successfully at Market Price with Avg Entry Price is {closePrice}")
                                self.orderLogs(f"{utcTime.strftime('%Y-%m-%d %H:%M:%S')} Cooldown Entry Order Placed and Filled Successfully at Market Price with Avg Entry Price is {closePrice}")

                                self.stopLossShortPosition(currtime=utcTime, price=self.current_order["ORIGINAL_STOPLOSSORDER_PRICE"])

                    except Exception as e:
                        self.log(f"{utcTime.strftime('%Y-%m-%d %H:%M:%S')} Got a Error while placing market entry order")
                        self.orderLogs(f"{utcTime.strftime('%Y-%m-%d %H:%M:%S')} Got a Error while placing market entry order")
                        self.errorLog(f"{utcTime.strftime('%Y-%m-%d %H:%M:%S')} Got a Error while placing market entry order")

                        self.log(f"Error -: {e}")
                        self.orderLogs(f"Error -: {e}")
                        self.errorLog(f"Error -: {e}")

                        self.clearPastTrade()
                        sys.exit()
                else:
                    self.checkEntryOrderPrice = True

    def stopLossLongPosition(self, currtime, price):
        amount = self.current_order["AMOUNT"]

        prices = self.client.get_all_tickers()
        assetInfo = next((item for item in prices if item["symbol"] == self.marginSymbol), None)

        currentPrice = float(assetInfo["price"])

        if price >= currentPrice:
            self.stoplossCheck = "MORE"
        else:
            self.stoplossCheck = "LESS"

        self.current_order["STOPLOSSORDER_PRICE"] = price
        self.current_order["STOPLOSSORDER_AMOUNT"] = amount

        if not self.fakeOrder:
            self.log(f"{currtime.strftime('%Y-%m-%d %H:%M')} Setting Stoploss Order with price - {price}, amount - {amount}, stoploss check - {self.stoplossCheck}")
            self.orderLogs(f"{currtime.strftime('%Y-%m-%d %H:%M')} Setting Stoploss Order with price - {price}, amount - {amount}, stoploss check - {self.stoplossCheck}")
        else:
            self.log(f"{currtime.strftime('%Y-%m-%d %H:%M')} Setting Cooldown Stoploss Order with price - {price}, amount - {amount}, stoploss check - {self.stoplossCheck}")
            self.orderLogs(f"{currtime.strftime('%Y-%m-%d %H:%M')} Setting Cooldown Stoploss Order with price - {price}, amount - {amount}, stoploss check - {self.stoplossCheck}")

        self.checkStoplossOrderPrice = True

    def stopLossShortPosition(self, currtime, price):
        amount = self.current_order["AMOUNT"]

        prices = self.client.get_all_tickers()
        assetInfo = next((item for item in prices if item["symbol"] == self.marginSymbol), None)

        currentPrice = float(assetInfo["price"])

        if price >= currentPrice:
            self.stoplossCheck = "MORE"
        else:
            self.stoplossCheck = "LESS"

        self.current_order["STOPLOSSORDER_PRICE"] = price
        self.current_order["STOPLOSSORDER_AMOUNT"] = amount

        if not self.fakeOrder:
            self.log(f"{currtime.strftime('%Y-%m-%d %H:%M')} Setting Stoploss Order with price - {price}, amount - {amount}, stoploss check - {self.stoplossCheck}")
            self.orderLogs(f"{currtime.strftime('%Y-%m-%d %H:%M')} Setting Stoploss Order with price - {price}, amount - {amount}, stoploss check - {self.stoplossCheck}")
        else:
            self.log(f"{currtime.strftime('%Y-%m-%d %H:%M')} Setting Cooldown Stoploss Order with price - {price}, amount - {amount}, stoploss check - {self.stoplossCheck}")
            self.orderLogs(f"{currtime.strftime('%Y-%m-%d %H:%M')} Setting Cooldown Stoploss Order with price - {price}, amount - {amount}, stoploss check - {self.stoplossCheck}")

        self.checkStoplossOrderPrice = True

    def marketOrderClosePosition(self, currTime, closePrice):
        amount = self.current_order["AMOUNT"]

        if self.current_order['WALLET'] == "CROSS 3X":
            isolated = False
        else:
            isolated = True

        try:
            if not self.fakeOrder:
                self.log(f"{currTime.strftime('%Y-%m-%d %H:%M:%S')} Placing Market Order to close trade with amount - {amount}")
                self.orderLogs(f"{currTime.strftime('%Y-%m-%d %H:%M:%S')} Placing Market Order to close trade with amount - {amount}")

                if self.current_order["TYPE"] == "LONG":
                    closePosition_result = self.client.create_margin_order(symbol=self.marginSymbol,
                                                                           isIsolated=isolated,
                                                                           side=SIDE_SELL,
                                                                           type=ORDER_TYPE_MARKET,
                                                                           sideEffectType="AUTO_REPAY",
                                                                           quantity=amount)
                else:
                    closePosition_result = self.client.create_margin_order(symbol=self.marginSymbol,
                                                                           isIsolated=isolated,
                                                                           side=SIDE_BUY,
                                                                           type=ORDER_TYPE_MARKET,
                                                                           sideEffectType="AUTO_REPAY",
                                                                           quantity=amount)

                self.stoplossFilled = True

                avgExitPrice = 0

                for fill in closePosition_result["fills"]:
                    avgExitPrice = avgExitPrice + (float(fill["price"]) * float(fill["qty"]))

                self.current_order["TRADE_STATUS"] = "MARKET STOPLOSS ORDER FILLED"

                self.current_order["EXIT_TIME"] = currTime.strftime("%Y-%m-%d %H:%M")
                self.current_order["EXITORDER_AVG_PRICE"] = float(avgExitPrice / self.current_order["AMOUNT"])
                self.current_order["EXITORDER_ORDERID"] = closePosition_result["orderId"]

                exitTime = datetime.datetime.strptime(self.current_order["EXIT_TIME"], "%Y-%m-%d %H:%M")
                entryTime = datetime.datetime.strptime(self.current_order["ENTRY_TIME"], "%Y-%m-%d %H:%M")
                holdTime = exitTime - entryTime
                holdTime = holdTime / datetime.timedelta(minutes=1)
                self.current_order["HOLD_TIME"] = holdTime

                self.log(f"{currTime.strftime('%Y-%m-%d %H:%M:%S')} Trade Closed Successfully at Market Price({self.current_order['EXITORDER_AVG_PRICE']}) with Order ID is {closePosition_result['orderId']}")
                self.orderLogs(f"{currTime.strftime('%Y-%m-%d %H:%M:%S')} Trade Closed Successfully at Market Price({self.current_order['EXITORDER_AVG_PRICE']}) with Order ID is {closePosition_result['orderId']}")
                self.stoplossHitLogs()
            else:
                self.log(f"{currTime.strftime('%Y-%m-%d %H:%M:%S')} Placing Cooldown Market Order to close trade with amount - {amount}")
                self.orderLogs(f"{currTime.strftime('%Y-%m-%d %H:%M:%S')} Placing Cooldown Market Order to close trade with amount - {amount}")

                self.stoplossFilled = True

                self.current_order["TRADE_STATUS"] = "MARKET STOPLOSS ORDER FILLED"

                self.current_order["EXIT_TIME"] = currTime.strftime("%Y-%m-%d %H:%M")
                self.current_order["EXITORDER_AVG_PRICE"] = float(closePrice)

                exitTime = datetime.datetime.strptime(self.current_order["EXIT_TIME"], "%Y-%m-%d %H:%M")
                entryTime = datetime.datetime.strptime(self.current_order["ENTRY_TIME"], "%Y-%m-%d %H:%M")
                holdTime = exitTime - entryTime
                holdTime = holdTime / datetime.timedelta(minutes=1)
                self.current_order["HOLD_TIME"] = holdTime

                self.log(f"{currTime.strftime('%Y-%m-%d %H:%M:%S')} Cooldown Trade Closed Successfully at Market Price({self.current_order['EXITORDER_AVG_PRICE']})")
                self.orderLogs(f"{currTime.strftime('%Y-%m-%d %H:%M:%S')} Cooldown Trade Closed Successfully at Market Price({self.current_order['EXITORDER_AVG_PRICE']})")

        except Exception as e:
            self.log(f"{currTime.strftime('%Y-%m-%d %H:%M')} Got a Error while closing trade with market order")
            self.orderLogs(f"{currTime.strftime('%Y-%m-%d %H:%M')} Got a Error while closing trade with market order")
            self.errorLog(f"{currTime.strftime('%Y-%m-%d %H:%M')} Got a Error while closing trade with market order")

            self.log(f"Error -: {e}")
            self.orderLogs(f"Error -: {e}")
            self.errorLog(f"Error -: {e}")

            self.clearPastTrade()
            sys.exit()

    def placeStoplossMarketEntryOrder(self, closePrice):
        utcTime = datetime.datetime.utcnow()

        if self.checkStoplossOrderPrice:
            price = self.current_order["STOPLOSSORDER_PRICE"]

            if self.stoplossCheck == "MORE" and closePrice >= price:
                self.checkStoplossOrderPrice = False
                self.marketOrderClosePosition(currTime=utcTime, closePrice=closePrice)
            elif self.stoplossCheck == "LESS" and closePrice <= price:
                self.checkStoplossOrderPrice = False
                self.marketOrderClosePosition(currTime=utcTime, closePrice=closePrice)
            else:
                self.checkStoplossOrderPrice = True

    def isSymbolActive(self):
        activatedPairsCollection = self.db["activatedPairs"]
        result = list(activatedPairsCollection.find({"symbol": self.marginSymbol}))

        if len(result) > 0:
            return True, result[0]
        else:
            return False, {}

    def addSymbolToActivePair(self, wallet):
        activatedPairsCollection = self.db["activatedPairs"]
        offTime = datetime.datetime.utcnow() + datetime.timedelta(hours=25)

        data = {
            'symbol': self.marginSymbol,
            'wallet': wallet,
            'offTime': offTime
        }

        activatedPairsCollection.insert_one(data)

        payload = {
            "username": f"Active Pair Script",
            "content": f"Added {self.marginSymbol} to active pair"
        }

        requests.post(self.ACTIVEPAIR_LOGS_URL, json=payload)

    def noOfActivePairs(self):
        activatedPairsCollection = self.db["activatedPairs"]
        result = list(activatedPairsCollection.find({}))

        return len(result)

    def extendSymbolActivePairOffTime(self):
        activatedPairsCollection = self.db["activatedPairs"]
        offTime = datetime.datetime.utcnow() + datetime.timedelta(hours=25)

        colfilter = {
            'symbol': self.marginSymbol,
        }

        newvalues = {"$set":
            {
                'offTime': offTime,
            }
        }

        activatedPairsCollection.update_one(colfilter, newvalues)

    def findWallet(self, alwaysCross=False):
        if alwaysCross:
            if self.onlyISO:
                isActive, r = self.isSymbolActive()
                if isActive:
                    self.log("Symbol already activated")
                    self.extendSymbolActivePairOffTime()
                    self.current_order['WALLET'] = r["wallet"]

                    self.transferSPOTtoISOLATEDMARGIN(self.coinPair, self.marginSymbol, 0.000001)
                    self.transferISOLATEDMARGINtoSPOT(asset=self.coinPair, symbol=self.marginSymbol, amount=0.000001)
                else:
                    if self.noOfActivePairs() < 20:
                        info = self.client.get_isolated_margin_account()
                        symbolInfo = [_ for _ in info['assets'] if _['symbol'] == self.marginSymbol]

                        if len(symbolInfo) > 0:
                            self.log("Symbol exists in Iso Account, Enabling it")
                            self.rawClient.enableIsolatedWallet(symbol=self.marginSymbol)
                            self.current_order['WALLET'] = int(symbolInfo[0]['marginRatio'])

                            self.transferSPOTtoISOLATEDMARGIN(self.coinPair, self.marginSymbol, 0.000001)
                            self.transferISOLATEDMARGINtoSPOT(asset=self.coinPair, symbol=self.marginSymbol, amount=0.000001)

                        else:
                            self.log("Symbol do not exists in Iso Account, Transferring from spot to activate it")
                            self.transferSPOTtoISOLATEDMARGIN(self.coinPair, self.marginSymbol, 0.000001)
                            info = self.client.get_isolated_margin_account()
                            symbolInfo = next((item for item in info['assets'] if item["symbol"] == self.marginSymbol), None)
                            self.current_order['WALLET'] = int(symbolInfo['marginRatio'])
                            self.transferISOLATEDMARGINtoSPOT(asset=self.coinPair, symbol=self.marginSymbol, amount=0.000001)

                        self.addSymbolToActivePair(self.current_order['WALLET'])
                        self.log("ISO Wallet activated and added to database")
                    else:
                        self.log("Maximum 20 ISO Wallet are already activated")
                        return False
            else:
                self.current_order["WALLET"] = "CROSS 3X"
        else:
            if self.coinPair == "USDT" and self.usdtPairWallet != "BOTH":
                self.current_order['WALLET'] = "CROSS 3X"
            elif self.coinPair == "ETH":
                self.current_order['WALLET'] = "CROSS 3X"
            else:
                isActive, r = self.isSymbolActive()
                if isActive:
                    self.log("Symbol already activated")
                    self.extendSymbolActivePairOffTime()
                    self.current_order['WALLET'] = r["wallet"]

                    self.transferSPOTtoISOLATEDMARGIN(self.coinPair, self.marginSymbol, 0.000001)
                    self.transferISOLATEDMARGINtoSPOT(asset=self.coinPair, symbol=self.marginSymbol, amount=0.000001)
                else:
                    if self.noOfActivePairs() < 20:
                        info = self.client.get_isolated_margin_account()
                        symbolInfo = [_ for _ in info['assets'] if _['symbol'] == self.marginSymbol]

                        if len(symbolInfo) > 0:
                            self.log("Symbol exists in Iso Account, Enabling it")
                            self.rawClient.enableIsolatedWallet(symbol=self.marginSymbol)
                            self.current_order['WALLET'] = int(symbolInfo[0]['marginRatio'])

                            self.transferSPOTtoISOLATEDMARGIN(self.coinPair, self.marginSymbol, 0.000001)
                            self.transferISOLATEDMARGINtoSPOT(asset=self.coinPair, symbol=self.marginSymbol, amount=0.000001)

                        else:
                            self.log("Symbol do not exists in Iso Account, Transferring from spot to activate it")
                            self.transferSPOTtoISOLATEDMARGIN(self.coinPair, self.marginSymbol, 0.000001)
                            info = self.client.get_isolated_margin_account()
                            symbolInfo = next((item for item in info['assets'] if item["symbol"] == self.marginSymbol), None)
                            self.current_order['WALLET'] = int(symbolInfo['marginRatio'])
                            self.transferISOLATEDMARGINtoSPOT(asset=self.coinPair, symbol=self.marginSymbol, amount=0.000001)

                        self.addSymbolToActivePair(self.current_order['WALLET'])
                        self.log("ISO Wallet activated and added to database")
                    else:
                        self.log("Maximum 20 ISO Wallet are already activated")
                        return False

        return True

    def minPositionSizing(self, row):
        self.current_order["Price Risk Ratio"] = 0
        self.current_order["RISK TIER"] = "None"
        self.current_order["Risk Per Trade Percentage"] = 0
        self.current_order["Risk Per Trade"] = 0

        return 0

    def positionSizing(self, row):
        priceRiskRatio = self.current_order["STARTBAR_CLOSE"] / self.current_order["STARTBAR_ATR"]
        self.current_order["Price Risk Ratio"] = priceRiskRatio

        if priceRiskRatio <= 250:
            self.current_order["RISK TIER"] = "TIER 1"

            if self.current_order['WALLET'] == "CROSS 3X":
                riskPerTrade = self.tier1_cross3x
            elif self.current_order['WALLET'] == 3:
                riskPerTrade = self.tier1_3x
            elif self.current_order['WALLET'] == 5:
                riskPerTrade = self.tier1_5x
            else:
                riskPerTrade = self.tier1_10x

        elif 251 <= priceRiskRatio <= 400:
            self.current_order["RISK TIER"] = "TIER 2"

            if self.current_order['WALLET'] == "CROSS 3X":
                riskPerTrade = self.tier2_cross3x
            elif self.current_order['WALLET'] == 3:
                riskPerTrade = self.tier2_3x
            elif self.current_order['WALLET'] == 5:
                riskPerTrade = self.tier2_5x
            else:
                riskPerTrade = self.tier2_10x

        elif 401 <= priceRiskRatio <= 550:
            self.current_order["RISK TIER"] = "TIER 3"

            if self.current_order['WALLET'] == "CROSS 3X":
                riskPerTrade = self.tier3_cross3x
            elif self.current_order['WALLET'] == 3:
                riskPerTrade = self.tier3_3x
            elif self.current_order['WALLET'] == 5:
                riskPerTrade = self.tier3_5x
            else:
                riskPerTrade = self.tier3_10x

        elif 551 <= priceRiskRatio <= 700:
            self.current_order["RISK TIER"] = "TIER 4"

            if self.current_order['WALLET'] == "CROSS 3X":
                riskPerTrade = self.tier4_cross3x
            elif self.current_order['WALLET'] == 3:
                riskPerTrade = self.tier4_3x
            elif self.current_order['WALLET'] == 5:
                riskPerTrade = self.tier4_5x
            else:
                riskPerTrade = self.tier4_10x

        else:
            # priceRiskRatio >= 701
            self.current_order["RISK TIER"] = "TIER 5"

            if self.current_order['WALLET'] == "CROSS 3X":
                riskPerTrade = self.tier5_cross3x
            elif self.current_order['WALLET'] == 3:
                riskPerTrade = self.tier5_3x
            elif self.current_order['WALLET'] == 5:
                riskPerTrade = self.tier5_5x
            else:
                riskPerTrade = self.tier5_10x

        self.current_order["Risk Per Trade Percentage"] = riskPerTrade

        tickerPrices = self.client.get_all_tickers()
        isoAccountDetails = self.client.get_isolated_margin_account()
        crossAccountDetails = self.client.get_margin_account()

        isoBalanceBTC = float(isoAccountDetails["totalAssetOfBtc"])
        crossBalanceBTC = float(crossAccountDetails["totalAssetOfBtc"])
        btcBalance = crossBalanceBTC + isoBalanceBTC

        if self.current_order["TRADE_TYPE"] == "POSTCLOSE DIVENTRY":
            riskPerTrade = riskPerTrade * self.postCloseCheckTillNow * self.postCloseDCA
        elif self.current_order["TRADE_TYPE"] == "POSTCLOSE REENTRY":
            riskPerTrade = riskPerTrade * self.reEntryCyclesCheckTillNow * self.reEntryDCA

        if self.coinPair == "USDT":
            btcusdtPrice = next((float(item['price']) for item in tickerPrices if item["symbol"] == "BTCUSDT"), None)

            isoBalanceUSDT = float(isoBalanceBTC * btcusdtPrice)
            crossBalanceUSDT = float(crossBalanceBTC * btcusdtPrice)

            usdtBalance = crossBalanceUSDT + isoBalanceUSDT

            maxRiskPerTrade = usdtBalance * riskPerTrade
        elif self.coinPair == "ETH":
            btcethPrice = next((float(item['price']) for item in tickerPrices if item["symbol"] == "ETHBTC"), None)
            btcethPrice = 1.00 / btcethPrice

            isoBalanceETH = float(isoBalanceBTC * btcethPrice)
            crossBalanceETH = float(crossBalanceBTC * btcethPrice)

            ethBalance = crossBalanceETH + isoBalanceETH

            maxRiskPerTrade = ethBalance * riskPerTrade
        else:
            # params.get("coinPair") == "BTC"
            maxRiskPerTrade = btcBalance * riskPerTrade

        self.current_order["Risk Per Trade"] = maxRiskPerTrade

        coinsToBuy = maxRiskPerTrade / row["atr"]

        self.log(f"Price Risk Ratio -: {priceRiskRatio}")
        self.log(f"Risk Per Trade -: {riskPerTrade}")
        self.log(f"Max Risk Per Trade -: {maxRiskPerTrade}")
        self.log(f"Row ATR -: {row['atr']}")
        self.log(f"Amount Calculated -: {coinsToBuy}")

        return coinsToBuy

    def disableTradesDueToLoss(self):
        disableTradeCol = self.db["disableTrades"]
        colfilter = {
            'settingName': "disabledTrades",
        }

        if self.disableStartbarTrades:
            newvalues = {"$set":
                {
                    'startBar-Disable': True,
                }
            }

            disableTradeCol.update_one(colfilter, newvalues)

        if self.disablePostCloseDivEntryTrades:
            newvalues = {"$set":
                {
                    'postCloseDivEntry-Disable': True,
                }
            }

            disableTradeCol.update_one(colfilter, newvalues)

        if self.disablePostCloseReEntryTrades:
            newvalues = {"$set":
                {
                    'postCloseReEntry-Disable': True,
                }
            }

            disableTradeCol.update_one(colfilter, newvalues)

        cooldownTill = datetime.datetime.utcnow() + datetime.timedelta(minutes=30)

        newvalues = {"$set":
            {
                'timerRunning': 'On',
                'type': 'mute',
                'timer': cooldownTill
            }
        }

        disableTradeCol.update_one(colfilter, newvalues)

        payload = {
            "username": f"Cooldown V1 Script-:",
            "content": f"Turning on cooldown due to {self.marginSymbol} till {cooldownTill}"
        }

        requests.post(self.COOLDOWN_LOGS_URL, json=payload)

    def disableTradeOnAsset(self):
        disablePairsCol = self.db["disablePairs"]
        cooldownTill = datetime.datetime.utcnow() + datetime.timedelta(minutes=60)

        newvalues = {
            "asset": self.baseAsset,
            "timer": cooldownTill
        }

        disablePairsCol.insert_one(newvalues)

        payload = {
            "username": f"Cooldown V3 Script-:",
            "content": f"Turning on cooldown v3 on {self.baseAsset} till {cooldownTill}"
        }

        requests.post(self.COOLDOWN_LOGS_URL, json=payload)

    def enableTradeOnAsset(self):
        disablePairsCol = self.db["disablePairs"]

        payload = {
            "username": f"Cooldown V3 Script-:",
            "content": f"Turning off cooldown on {self.baseAsset}"
        }

        requests.post(self.COOLDOWN_LOGS_URL, json=payload)

        disablePairsCol.delete_one({"asset": self.baseAsset})

    def checkCooldownType(self):
        disableTradeCol = self.db["disableTrades"]
        disablePairsCol = self.db["disablePairs"]

        assetDisableResult = disablePairsCol.find_one({"asset": self.baseAsset})
        tradeDisableResult = disableTradeCol.find_one()["type"]

        if assetDisableResult:
            return "v3disable"
        else:
            return tradeDisableResult

    def checkStartBarTradesDisable(self):
        disableTradeCol = self.db["disableTrades"]
        disablePairsCol = self.db["disablePairs"]

        assetDisableResult = disablePairsCol.find_one({"asset": self.baseAsset})
        tradeDisableResult = disableTradeCol.find_one()["startBar-Disable"]

        if assetDisableResult:
            return True
        else:
            return tradeDisableResult

    def checkDivEntryTradesDisable(self):
        disableTradeCol = self.db["disableTrades"]
        return disableTradeCol.find_one()["postCloseDivEntry-Disable"]

    def checkReEntryTradesDisable(self):
        disableTradeCol = self.db["disableTrades"]
        return disableTradeCol.find_one()["postCloseReEntry-Disable"]

    def test(self):
        # row = self.ltfData.iloc[-1]

        print(f"{self.marginSymbol} - {self.onlyISO}")

        # info = self.client.get_isolated_margin_account()
        # symbolInfo = [_ for _ in info['assets'] if _['symbol'] == self.marginSymbol]
        # if len(symbolInfo) > 0:
        #     pprint(symbolInfo[0])
        # else:
        #     print("Symbol info do not exists")

        # self.transferSPOTtoISOLATEDMARGIN(asset=self.coinPair, symbol=self.marginSymbol, amount=0.0000001)
        # print("Transfered")

        walletFound = self.findWallet(alwaysCross=True)
        print(walletFound)

        ##DTF Test
        # self.current_order["TYPE"] = "SHORT"
        # self.dtfTest(row.name)

        ##HTF Testing
        # passed, noShort, htfResult = self.htfTest(row.name, "SHORT")

    def run(self):
        row = self.ltfData.iloc[-1]

        if len(self.ltfData) < (self.atrParameter + 1) or math.isnan(row["stoch"]):
            return False

        self.prevRow = self.ltfData.iloc[-2]
        index = row.name
        checkStopLossStatus = False

        if self.currentStatus == 0:
            if row["stoch"] > self.ltfStochKOB and row["cci"] > self.ltfCCIShortLimit:
                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Startbar found - Short Type Trade")
                self.discordLog(f"{index.strftime('%Y-%m-%d %H:%M')} Startbar found - Short Type Trade")
                # SHORT TYPE TRADE POSSIBLE
                passed, noShort, htfResult = self.htfTest(index, "SHORT")
                htf1Result, htf2Result, htf3Result, htf4Result, htf5Result, htf6Result, htf7Result, htf8Result, htf9Result = htfResult
                if passed:
                    self.current_order["TYPE"] = "SHORT"
                    self.current_order["TRADE_TYPE"] = "STARTBAR ENTRY"
                    self.current_order["STARTBAR_TIME"] = index.strftime("%Y-%m-%d %H:%M")
                    self.current_order["STARTBAR_STOCH"] = row["stoch"]
                    self.current_order["STARTBAR_CCI"] = row["cci"]
                    self.current_order["STARTBAR_ATR"] = row["atr"]
                    self.current_order["STARTBAR_CLOSE"] = row["Close"]
                    self.current_order["HTF1_TREND"] = htf1Result
                    self.current_order["HTF2_TREND"] = htf2Result
                    self.current_order["HTF3_TREND"] = htf3Result
                    self.current_order["HTF4_TREND"] = htf4Result
                    self.current_order["HTF5_TREND"] = htf5Result
                    self.current_order["HTF6_TREND"] = htf6Result
                    self.current_order["HTF7_TREND"] = htf7Result
                    self.current_order["HTF8_TREND"] = htf8Result
                    self.current_order["HTF9_TREND"] = htf9Result
                    self.current_order["NO_OF_HTF_CONFIRMATION"] = noShort
                    self.current_order["DIV_COMPLETED"] = False
                    self.current_order["DIVBAR_TREND"] = []

                    if self.tradeType == "Both" or self.tradeType == "Short":
                        if row["atr"] != 0:
                            self.log(f"{index.strftime('%Y-%m-%d %H:%M')} HTF Test Passed")
                            self.discordLog(f"{index.strftime('%Y-%m-%d %H:%M')} HTF Test Passed")
                            self.currentStatus = 1

            elif row["stoch"] < self.ltfStochKOS and row["cci"] < self.ltfCCILongLimit:
                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Startbar found - Long Type Trade")
                self.discordLog(f"{index.strftime('%Y-%m-%d %H:%M')} Startbar found - Long Type Trade")
                # LONG TYPE TRADE POSSIBLE
                passed, noLong, htfResult = self.htfTest(index, "LONG")
                htf1Result, htf2Result, htf3Result, htf4Result, htf5Result, htf6Result, htf7Result, htf8Result, htf9Result = htfResult
                if passed:
                    self.current_order["TYPE"] = "LONG"
                    self.current_order["TRADE_TYPE"] = "STARTBAR ENTRY"
                    self.current_order["STARTBAR_TIME"] = index.strftime("%Y-%m-%d %H:%M")
                    self.current_order["STARTBAR_STOCH"] = row["stoch"]
                    self.current_order["STARTBAR_CCI"] = row["cci"]
                    self.current_order["STARTBAR_ATR"] = row["atr"]
                    self.current_order["STARTBAR_CLOSE"] = row["Close"]
                    self.current_order["HTF1_TREND"] = htf1Result
                    self.current_order["HTF2_TREND"] = htf2Result
                    self.current_order["HTF3_TREND"] = htf3Result
                    self.current_order["HTF4_TREND"] = htf4Result
                    self.current_order["HTF5_TREND"] = htf5Result
                    self.current_order["HTF6_TREND"] = htf6Result
                    self.current_order["HTF7_TREND"] = htf7Result
                    self.current_order["HTF8_TREND"] = htf8Result
                    self.current_order["HTF9_TREND"] = htf9Result
                    self.current_order["NO_OF_HTF_CONFIRMATION"] = noLong
                    self.current_order["DIV_COMPLETED"] = False
                    self.current_order["DIVBAR_TREND"] = []

                    if self.tradeType == "Both" or self.tradeType == "Long":
                        if row["atr"] != 0:
                            self.log(f"{index.strftime('%Y-%m-%d %H:%M')} HTF Test Passed")
                            self.discordLog(f"{index.strftime('%Y-%m-%d %H:%M')} HTF Test Passed")
                            self.currentStatus = 1

        elif self.currentStatus == 1:
            if self.successfulDivCount == self.divBarRequired:
                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Successful Div Count Reached")
                self.current_order["BARS_REQUIRED_FROM_STARTBAR_TO_REACH_MINBAR_REQUIREMENT"] = self.divCountTillNow

                self.current_order["DIV_PASSED"] = True
                self.current_order["DIV_COMPLETED"] = True

            elif self.divCountTillNow < self.divBarWindow:
                self.divCountTillNow = self.divCountTillNow + 1

                restartStartbar, cancelStartbar, prevBarResult, startBarResult = self.divTest(row, self.prevRow, self.searchDivOnly, self.current_order["STARTBAR_CCI"], self.current_order["STARTBAR_CLOSE"])

                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Checking Divergence on this candle, Count {self.divCountTillNow} out of {self.divBarWindow}. Successful Count - {self.successfulDivCount}")
                self.discordLog(f"{index.strftime('%Y-%m-%d %H:%M')} Checking Divergence on this candle, Count {self.divCountTillNow} out of {self.divBarWindow}. Successful Count - {self.successfulDivCount}")

                if prevBarResult:
                    self.successfulDivCount = self.successfulDivCount + 1
                    self.current_order[f"DIVBAR_TREND"].append((self.successfulDivCount, "1 Bar Back"))

                elif startBarResult:
                    self.successfulDivCount = self.successfulDivCount + 1
                    self.current_order[f"DIVBAR_TREND"].append((self.successfulDivCount, "Start Bar"))

                elif cancelStartbar:
                    self.log(f"{index.strftime('%Y-%m-%d %H:%M')} - Canceling Startup bar")
                    self.discordLog(f"{index.strftime('%Y-%m-%d %H:%M')} - Canceling Startup bar")
                    self.clearPastTrade()
                    self.current_order["DIV_COMPLETED"] = False

                elif restartStartbar:
                    self.log(f"{index.strftime('%Y-%m-%d %H:%M')} - Restarting Startup bar")
                    self.discordLog(f"{index.strftime('%Y-%m-%d %H:%M')} - Restarting Startup bar")

                    self.currentStatus = 1

                    self.setupBarNo = 0
                    self.orderAlreadyOpenFor = 0
                    self.trailSTL = self.TSLBars

                    self.divCountTillNow = 0
                    self.successfulDivCount = 0

                    self.current_order["STARTBAR_TIME"] = index.strftime("%Y-%m-%d %H:%M")
                    self.current_order["STARTBAR_STOCH"] = row["stoch"]
                    self.current_order["STARTBAR_CCI"] = row["cci"]
                    self.current_order["STARTBAR_CLOSE"] = row["Close"]

                    self.current_order["DIVBAR_TREND"] = []

                if cancelStartbar or restartStartbar:
                    self.divCountTillNow = 0
                    self.successfulDivCount = 0

                if self.successfulDivCount == self.divBarRequired:
                    if self.current_order['TYPE'] == "LONG":
                        if row["stoch"] > self.lastDivStochKOS:
                            self.log(f"{index.strftime('%Y-%m-%d %H:%M')} - Canceling Trade Because Last Div Bar Stoch More then LTF Stoch OS")
                            self.clearPastTrade()
                            self.current_order["DIV_COMPLETED"] = False
                        elif self.dcCheckTROnLastDivBar == "On":
                            self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Successful Div Count Reached")
                            self.current_order["BARS_REQUIRED_FROM_STARTBAR_TO_REACH_MINBAR_REQUIREMENT"] = self.divCountTillNow

                            self.current_order["DIV_PASSED"] = True
                            self.current_order["DIV_COMPLETED"] = True
                    else:
                        if row["stoch"] < self.lastDivStochKOB:
                            self.log(f"{index.strftime('%Y-%m-%d %H:%M')} - Canceling Trade Because Last Div Bar Stoch Less then LTF Stoch OB")
                            self.clearPastTrade()
                            self.current_order["DIV_COMPLETED"] = False
                        elif self.dcCheckTROnLastDivBar == "On":
                            self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Successful Div Count Reached")
                            self.current_order[
                                "BARS_REQUIRED_FROM_STARTBAR_TO_REACH_MINBAR_REQUIREMENT"] = self.divCountTillNow

                            self.current_order["DIV_PASSED"] = True
                            self.current_order["DIV_COMPLETED"] = True
                elif self.divCountTillNow == self.divBarWindow and self.cancelFailedDivOnLastDivCandle == "On":
                    self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Div window reached, not able to get enough successfully divergence")
                    self.discordLog(f"{index.strftime('%Y-%m-%d %H:%M')} Div window reached, not able to get enough successfully divergence")
                    self.current_order["DIVBAR_FOUND"] = self.successfulDivCount

                    self.current_order["DIV_PASSED"] = False
                    self.current_order["DIV_COMPLETED"] = True

            elif self.divCountTillNow == self.divBarWindow and self.cancelFailedDivOnLastDivCandle == "Off":
                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Div window reached, not able to get enough successfully divergence")
                self.discordLog(f"{index.strftime('%Y-%m-%d %H:%M')} Div window reached, not able to get enough successfully divergence")
                self.current_order["DIVBAR_FOUND"] = self.successfulDivCount

                self.current_order["DIV_PASSED"] = False
                self.current_order["DIV_COMPLETED"] = True

            if self.current_order["DIV_COMPLETED"]:
                self.current_order["DIVBAR_FOUND"] = self.successfulDivCount
                if self.current_order["DIV_PASSED"]:
                    ### Target Recongination Test ###
                    self.divergencePassedLog()

                    if self.checkDTF == "On":
                        dtfPassed, dtfResult = self.dtfTest(index)

                        self.current_order["DTF_RESULT"] = dtfResult
                        if dtfPassed:
                            self.dtfPassedLog()
                            self.current_order["TARGETRECOGINATION_PASSED"] = self.targetReconginitionTest(row, self.setupBarNo)

                            if self.current_order["TARGETRECOGINATION_PASSED"]:
                                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Target Recogination passed")
                                self.targetRecognitionPassedLog()

                                if not self.checkStartBarTradesDisable():
                                    placed = self.placeEntryOrder(row)

                                    if placed:
                                        self.disableTradeOnAsset()
                                        self.currentStatus = 3  ##start looking for entry order and stoploss
                                    else:
                                        self.clearPastTrade()
                                else:
                                    self.fakeEntryOrder(row)
                                    self.currentStatus = 3
                                    self.fakeOrder = True
                                    self.fakeType = self.checkCooldownType()

                            else:
                                self.setupBarNo = self.setupBarNo + 1
                                self.currentStatus = 2  ##recheck for setup bar

                        else:
                            self.dtfFailedLog()
                            self.clearPastTrade()

                    else:
                        self.current_order["TARGETRECOGINATION_PASSED"] = self.targetReconginitionTest(row, self.setupBarNo)

                        if self.current_order["TARGETRECOGINATION_PASSED"]:
                            self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Target Recogination passed")
                            self.targetRecognitionPassedLog()

                            if not self.checkStartBarTradesDisable():
                                placed = self.placeEntryOrder(row)

                                if placed:
                                    self.disableTradeOnAsset()
                                    self.currentStatus = 3  ##start looking for entry order and stoploss
                                    self.fakeOrder = False
                                else:
                                    self.clearPastTrade()
                            else:
                                self.fakeEntryOrder(row)
                                self.currentStatus = 3
                                self.fakeOrder = True
                                self.fakeType = self.checkCooldownType()

                        else:
                            self.setupBarNo = self.setupBarNo + 1
                            self.currentStatus = 2  ##recheck for setup bar


                elif not self.current_order["DIV_PASSED"]:
                    ###Divergence test failed###
                    self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Divergence Test failed")
                    self.divergenceFailedLog(self.current_order['DIVBAR_FOUND'])
                    self.clearPastTrade()

        elif self.currentStatus == 2:
            ###Recheck for setup bar###
            self.log(f"{index.strftime('%Y-%m-%d %H:%M')} DC Setup Bar Recheck - {self.dcSetupBarLeft}")
            if self.dcSetupBarLeft > 0:
                self.current_order["TR_CANCELLED"] = False
                isInsideCandle = row["Low"] > self.prevRow["Low"] and row["High"] < self.prevRow["High"]
                longKeyReversal = row["Low"] < self.prevRow["Low"] and row["Close"] > self.prevRow["Close"]
                shortKeyReversal = row["High"] > self.prevRow["High"] and row["Close"] < self.prevRow["Close"]

                if self.checkTRIfInside == "On":
                    if isInsideCandle:
                        self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Rechecking Target Recoginition (Inside Candle)")
                        self.current_order["TARGETRECOGINATION_PASSED"] = self.targetReconginitionTest(row, self.setupBarNo)

                elif self.checkTRIfKeyReversal == "On":
                    if self.current_order['TYPE'] == "LONG" and longKeyReversal:
                        self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Rechecking Target Recoginition (Long Reversal Candle)")
                        self.current_order["TARGETRECOGINATION_PASSED"] = self.targetReconginitionTest(row, self.setupBarNo)
                    elif self.current_order['TYPE'] == "SHORT" and shortKeyReversal:
                        self.log(f" {index.strftime('%Y-%m-%d %H:%M')} Rechecking Target Recoginition (Short Reversal Candle)")
                        self.current_order["TARGETRECOGINATION_PASSED"] = self.targetReconginitionTest(row, self.setupBarNo)

                elif self.checkTRIfDivBarBoth == "On":
                    if self.current_order['TYPE'] == "LONG":
                        if row["cci"] > self.prevRow["cci"] and row["Close"] < self.prevRow["Close"]:
                            self.log(f" {index.strftime('%Y-%m-%d %H:%M')} Rechecking Target Recoginition (Div bar 1 bar back)")
                            self.current_order["TARGETRECOGINATION_PASSED"] = self.targetReconginitionTest(row, self.setupBarNo)
                        elif row["cci"] > self.current_order["STARTBAR_CCI"] and row["Close"] < self.current_order["STARTBAR_CLOSE"]:
                            self.log(f" {index.strftime('%Y-%m-%d %H:%M')} Rechecking Target Recoginition (Div bar Start Bar)")
                            self.current_order["TARGETRECOGINATION_PASSED"] = self.targetReconginitionTest(row, self.setupBarNo)
                    else:
                        if row["cci"] < self.prevRow["cci"] and row["Close"] > self.prevRow["Close"]:
                            self.log(f" {index.strftime('%Y-%m-%d %H:%M')} Rechecking Target Recoginition (Div bar 1 bar back)")
                            self.current_order["TARGETRECOGINATION_PASSED"] = self.targetReconginitionTest(row, self.setupBarNo)
                        elif row["cci"] < self.current_order["STARTBAR_CCI"] and row["Close"] > self.current_order["STARTBAR_CLOSE"]:
                            self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Rechecking Target Recoginition (Div bar Start Bar)")
                            self.current_order["TARGETRECOGINATION_PASSED"] = self.targetReconginitionTest(row, self.setupBarNo)

                self.dcSetupBarLeft = self.dcSetupBarLeft - 1
                self.setupBarNo = self.setupBarNo + 1
            else:
                self.current_order["TR_CANCELLED"] = True

            if self.current_order["TARGETRECOGINATION_PASSED"]:
                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Target Recogination passed")
                self.targetRecognitionPassedLog()
                if not self.checkStartBarTradesDisable():
                    placed = self.placeEntryOrder(row)

                    if placed:
                        self.disableTradeOnAsset()
                        self.currentStatus = 3  ##start looking for entry order and stoploss
                        self.fakeOrder = False
                    else:
                        self.clearPastTrade()
                else:
                    self.fakeEntryOrder(row)
                    self.currentStatus = 3
                    self.fakeOrder = True
                    self.fakeType = self.checkCooldownType()

            if self.current_order["TR_CANCELLED"]:
                ###Target Recogination failed###
                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Target Recogination failed")
                self.targetRecognitionFailedLog()

                try:
                    new_row = [self.marginSymbol,
                               self.current_order['TYPE'],
                               self.current_order['STARTBAR_TIME'],
                               self.current_order['STARTBAR_STOCH'],
                               self.current_order['STARTBAR_CCI'],
                               self.current_order['STARTBAR_CLOSE'],
                               self.current_order['HTF1_TREND'],
                               self.current_order['HTF2_TREND'],
                               self.current_order['HTF3_TREND'],
                               self.current_order['HTF4_TREND'],
                               self.current_order['HTF5_TREND'],
                               self.current_order['HTF6_TREND'],
                               self.current_order['NO_OF_HTF_CONFIRMATION'],
                               self.current_order['DIVBAR_FOUND'],
                               ]

                    for i in self.current_order[f"DIVBAR_TREND"]:
                        new_row.append(i[1])

                    cells = self.targetRecognitionSheet.get_all_values(include_tailing_empty_rows=False,
                                                                       include_tailing_empty=False, returnas='matrix')
                    last_row = len(cells)
                    self.targetRecognitionSheet.insert_rows(last_row, number=1, values=new_row)

                except Exception as e:
                    self.log(f"{self.marginSymbol} - Error in writing target recoginition failed in google sheet -: {e}")
                    self.errorLog(f"Error in writing target recoginition failed in google sheet -: {e}")
                    sys.exit(0)

                self.clearPastTrade()

        elif self.currentStatus == 3:
            ###Check if entry order cleared and place stop loss###
            if self.entryFilled or self.stoplossFilled:
                checkStopLossStatus = True
                self.currentStatus = 4
            else:
                if self.fakeOrder:
                    self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Checking Cooldown Entry Order Status")
                    self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} Checking Cooldown Entry Order Status")
                else:
                    self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Checking Entry Order Status")
                    self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} Checking Entry Order Status")

                if self.orderAlreadyOpenFor < self.keepOrderOpen:
                    self.orderAlreadyOpenFor = self.orderAlreadyOpenFor + 1
                    self.current_order["ENTRYORDER_CANCELLED"] = False

                    isInsideCandle = row["Low"] > self.prevRow["Low"] and row["High"] < self.prevRow["High"]
                    longKeyReversal = row["Low"] < self.prevRow["Low"] and row["Close"] > self.prevRow["Close"]
                    shortKeyReversal = row["High"] > self.prevRow["High"] and row["Close"] < self.prevRow["Close"]

                    self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Keep Order Open = {self.orderAlreadyOpenFor}")

                    if self.alwaysMoveForward == "On":
                        if self.current_order["TYPE"] == "LONG":
                            if self.entryFilled:
                                checkStopLossStatus = True
                                self.currentStatus = 4
                            else:
                                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Entry Order not filled")
                                self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} Entry Order not filled")

                                newPrice = row["High"] + self.entryTickOffset

                                if newPrice < self.current_order["ENTRYORDER_PRICE"]:
                                    if not self.fakeOrder:
                                        moved = self.moveEntryOrder(row)

                                        if not moved:
                                            self.clearPastTrade()
                                    else:
                                        self.fakeMoveEntryOrder(row)
                                else:
                                    self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} Entry Order Not Moved because New Entry Price ({newPrice}) is more then current entry price({self.current_order['ENTRYORDER_PRICE']})")
                                    self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Entry Order Not Moved because New Entry Price ({newPrice}) is more then current entry price({self.current_order['ENTRYORDER_PRICE']})")

                        elif self.current_order["TYPE"] == "SHORT":
                            if self.entryFilled:
                                checkStopLossStatus = True
                                self.currentStatus = 4
                            else:
                                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Entry Order not filled")
                                self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} Entry Order not filled")

                                newPrice = row["Low"] - self.entryTickOffset

                                if newPrice > self.current_order["ENTRYORDER_PRICE"]:
                                    if not self.fakeOrder:
                                        moved = self.moveEntryOrder(row)

                                        if not moved:
                                            self.clearPastTrade()
                                    else:
                                        self.fakeMoveEntryOrder(row)
                                else:
                                    self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} Entry Order Not Moved because New Entry Price ({newPrice}) is less then current entry price({self.current_order['ENTRYORDER_PRICE']})")
                                    self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Entry Order Not Moved because New Entry Price ({newPrice}) is less then current entry price({self.current_order['ENTRYORDER_PRICE']})")

                    elif self.alwaysMoveForward == "Off":
                        if self.current_order["TYPE"] == "LONG":
                            if self.entryFilled:
                                checkStopLossStatus = True
                                self.currentStatus = 4
                            else:
                                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Entry Order not filled")
                                self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} Entry Order not filled")
                                oneTimeMove = False

                                if self.forwardIfInside == "On" and oneTimeMove == False:
                                    if isInsideCandle:
                                        newPrice = row["High"] + self.entryTickOffset

                                        if newPrice < self.current_order["ENTRYORDER_PRICE"]:
                                            oneTimeMove = True
                                            if not self.fakeOrder:
                                                moved = self.moveEntryOrder(row)

                                                if not moved:
                                                    self.clearPastTrade()

                                                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Entry Order Moved due to Inside Bar Found")
                                                self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} Entry Order Moved due to Inside Bar Found")
                                            else:
                                                self.fakeMoveEntryOrder(row)
                                                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Cooldown Entry Order Moved due to Inside Bar Found")
                                                self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} Cooldown Entry Order Moved due to Inside Bar Found")

                                            self.checkEntryOrderPrice = True
                                        else:
                                            self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} (Inside Bar) Entry Order Not Moved because New Entry Price ({newPrice}) is more then current entry price({self.current_order['ENTRYORDER_PRICE']})")
                                            self.log(f"{index.strftime('%Y-%m-%d %H:%M')} (Inside Bar) Entry Order Not Moved because New Entry Price ({newPrice}) is more then current entry price({self.current_order['ENTRYORDER_PRICE']})")

                                if self.forwardIfDivBar1BarBack == "On" and oneTimeMove == False:
                                    if row["cci"] > self.prevRow["cci"] and row["Close"] < self.prevRow["Close"]:
                                        newPrice = row["High"] + self.entryTickOffset

                                        if newPrice < self.current_order["ENTRYORDER_PRICE"]:
                                            oneTimeMove = True
                                            if not self.fakeOrder:
                                                moved = self.moveEntryOrder(row)

                                                if not moved:
                                                    self.clearPastTrade()

                                                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Entry Order Moved due to Div Bar 1 Bar Back")
                                                self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} Entry Order Moved due to Div Bar 1 Bar Back")
                                            else:
                                                self.fakeMoveEntryOrder(row)
                                                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Cooldown Entry Order Moved due to Div Bar 1 Bar Back")
                                                self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} Cooldown Entry Order Moved due to Div Bar 1 Bar Back")

                                            self.checkEntryOrderPrice = True
                                        else:
                                            self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} (Div Bar 1 Bar Back) Entry Order Not Moved because New Entry Price ({newPrice}) is more then current entry price({self.current_order['ENTRYORDER_PRICE']})")
                                            self.log(f"{index.strftime('%Y-%m-%d %H:%M')} (Div Bar 1 Bar Back) Entry Order Not Moved because New Entry Price ({newPrice}) is more then current entry price({self.current_order['ENTRYORDER_PRICE']})")

                                if self.forwardIfDivBarBoth == "On" and oneTimeMove == False:
                                    if row["cci"] > self.prevRow["cci"] and row["Close"] < self.prevRow["Close"]:
                                        newPrice = row["High"] + self.entryTickOffset

                                        if newPrice < self.current_order["ENTRYORDER_PRICE"]:
                                            oneTimeMove = True
                                            if not self.fakeOrder:
                                                moved = self.moveEntryOrder(row)

                                                if not moved:
                                                    self.clearPastTrade()

                                                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Entry Order Moved due to Div Bar 1 Bar Back")
                                                self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} Entry Order Moved due to Div Bar 1 Bar Back")
                                            else:
                                                self.fakeMoveEntryOrder(row)
                                                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Cooldown Entry Order Moved due to Div Bar 1 Bar Back")
                                                self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} Cooldown Entry Order Moved due to Div Bar 1 Bar Back")

                                            self.checkEntryOrderPrice = True
                                        else:
                                            self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} (Div Bar 1 Bar Back) Entry Order Not Moved because New Entry Price ({newPrice}) is more then current entry price({self.current_order['ENTRYORDER_PRICE']})")
                                            self.log(f"{index.strftime('%Y-%m-%d %H:%M')} (Div Bar 1 Bar Back) Entry Order Not Moved because New Entry Price ({newPrice}) is more then current entry price({self.current_order['ENTRYORDER_PRICE']})")

                                    elif row["cci"] > self.current_order["STARTBAR_CCI"] and row["Close"] < self.current_order["STARTBAR_CLOSE"]:
                                        newPrice = row["High"] + self.entryTickOffset

                                        if newPrice < self.current_order["ENTRYORDER_PRICE"]:
                                            oneTimeMove = True
                                            if not self.fakeOrder:
                                                moved = self.moveEntryOrder(row)

                                                if not moved:
                                                    self.clearPastTrade()

                                                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Entry Order Moved due to Div Bar Start Bar")
                                                self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} Entry Order Moved due to Div Bar Start Bar")
                                            else:
                                                self.fakeMoveEntryOrder(row)
                                                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Cooldown Entry Order Moved due to Div Bar Start Bar")
                                                self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} Cooldown Entry Order Moved due to Div Bar Start Bar")

                                            self.checkEntryOrderPrice = True
                                        else:
                                            self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} (Div Bar Start Bar) Entry Order Not Moved because New Entry Price ({newPrice}) is more then current entry price({self.current_order['ENTRYORDER_PRICE']})")
                                            self.log(f"{index.strftime('%Y-%m-%d %H:%M')} (Div Bar Start Bar) Entry Order Not Moved because New Entry Price ({newPrice}) is more then current entry price({self.current_order['ENTRYORDER_PRICE']})")

                                if self.forwardIfKeyReversal == "On" and oneTimeMove == False:
                                    if longKeyReversal:
                                        newPrice = row["High"] + self.entryTickOffset

                                        if newPrice < self.current_order["ENTRYORDER_PRICE"]:
                                            oneTimeMove = True
                                            if not self.fakeOrder:
                                                moved = self.moveEntryOrder(row)

                                                if not moved:
                                                    self.clearPastTrade()

                                                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Entry Order Moved due to Long Key Reversal")
                                                self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} Entry Order Moved due to Long Key Reversal")
                                            else:
                                                self.fakeMoveEntryOrder(row)
                                                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Cooldown Entry Order Moved due to Long Key Reversal")
                                                self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} Cooldown Entry Order Moved due to Long Key Reversal")

                                            self.checkEntryOrderPrice = True
                                        else:
                                            self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} (Long Key Reversal) Entry Order Not Moved because New Entry Price ({newPrice}) is more then current entry price({self.current_order['ENTRYORDER_PRICE']})")
                                            self.log(f"{index.strftime('%Y-%m-%d %H:%M')} (Long Key Reversal) Entry Order Not Moved because New Entry Price ({newPrice}) is more then current entry price({self.current_order['ENTRYORDER_PRICE']})")

                                if self.forwardIfLowerHigher == "On" and oneTimeMove == False:
                                    if row["High"] < self.prevRow["High"]:
                                        newPrice = row["High"] + self.entryTickOffset

                                        if newPrice < self.current_order["ENTRYORDER_PRICE"]:
                                            oneTimeMove = True
                                            if not self.fakeOrder:
                                                moved = self.moveEntryOrder(row)

                                                if not moved:
                                                    self.clearPastTrade()

                                                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Entry Order Moved due to Lower High")
                                                self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} Entry Order Moved due to Lower High")
                                            else:
                                                self.fakeMoveEntryOrder(row)
                                                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Cooldown Entry Order Moved due to Lower High")
                                                self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} Cooldown Entry Order Moved due to Lower High")

                                            self.checkEntryOrderPrice = True
                                        else:
                                            self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} (Lower High) Entry Order Not Moved because New Entry Price ({newPrice}) is more then current entry price({self.current_order['ENTRYORDER_PRICE']})")
                                            self.log(f"{index.strftime('%Y-%m-%d %H:%M')} (Lower High) Entry Order Not Moved because New Entry Price ({newPrice}) is more then current entry price({self.current_order['ENTRYORDER_PRICE']})")

                                if not oneTimeMove:
                                    if self.keepOrderOpen == 1:
                                        self.current_order["ENTRYORDER_CANCELLED"] = True
                                    else:
                                        self.checkEntryOrderPrice = False

                        elif self.current_order["TYPE"] == "SHORT":
                            if self.entryFilled:
                                checkStopLossStatus = True
                                self.currentStatus = 4
                            else:
                                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Entry Order not filled")
                                self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} Entry Order not filled")
                                oneTimeMove = False

                                if self.forwardIfInside == "On" and oneTimeMove == False:
                                    if isInsideCandle:
                                        newPrice = row["Low"] - self.entryTickOffset

                                        if newPrice > self.current_order["ENTRYORDER_PRICE"]:
                                            oneTimeMove = True
                                            self.checkEntryOrderPrice = True

                                            if not self.fakeOrder:
                                                moved = self.moveEntryOrder(row)

                                                if not moved:
                                                    self.clearPastTrade()

                                                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Entry Order Moved due to Inside Bar Found")
                                                self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} Entry Order Moved due to Inside Bar Found")
                                            else:
                                                self.fakeMoveEntryOrder(row)
                                                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Cooldown Entry Order Moved due to Inside Bar Found")
                                                self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} Cooldown Entry Order Moved due to Inside Bar Found")

                                        else:
                                            self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} (Inside Bar) Entry Order Not Moved because New Entry Price ({newPrice}) is less then current entry price({self.current_order['ENTRYORDER_PRICE']})")
                                            self.log(f"{index.strftime('%Y-%m-%d %H:%M')} (Inside Bar) Entry Order Not Moved because New Entry Price ({newPrice}) is less then current entry price({self.current_order['ENTRYORDER_PRICE']})")

                                if self.forwardIfDivBar1BarBack == "On" and oneTimeMove == False:
                                    if row["cci"] < self.prevRow["cci"] and row["Close"] > self.prevRow["Close"]:
                                        newPrice = row["Low"] - self.entryTickOffset

                                        if newPrice > self.current_order["ENTRYORDER_PRICE"]:
                                            oneTimeMove = True
                                            self.checkEntryOrderPrice = True
                                            if self.fakeOrder:
                                                moved = self.moveEntryOrder(row)

                                                if not moved:
                                                    self.clearPastTrade()

                                                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Entry Order Moved due to  Div Bar 1 Bar Back Found")
                                                self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} Entry Order Moved due to  Div Bar 1 Bar Back Found")
                                            else:
                                                self.fakeMoveEntryOrder(row)
                                                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Cooldown Entry Order Moved due to  Div Bar 1 Bar Back Found")
                                                self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} Cooldown Entry Order Moved due to  Div Bar 1 Bar Back Found")
                                        else:
                                            self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} ( Div Bar 1 Bar Back) Entry Order Not Moved because New Entry Price ({newPrice}) is less then current entry price({self.current_order['ENTRYORDER_PRICE']})")
                                            self.log(f"{index.strftime('%Y-%m-%d %H:%M')} ( Div Bar 1 Bar Back) Entry Order Not Moved because New Entry Price ({newPrice}) is less then current entry price({self.current_order['ENTRYORDER_PRICE']})")

                                if self.forwardIfDivBarBoth == "On" and oneTimeMove == False:
                                    if row["cci"] < self.prevRow["cci"] and row["Close"] > self.prevRow["Close"]:
                                        newPrice = row["Low"] - self.entryTickOffset

                                        if newPrice > self.current_order["ENTRYORDER_PRICE"]:
                                            oneTimeMove = True
                                            self.checkEntryOrderPrice = True
                                            if not self.fakeOrder:
                                                moved = self.moveEntryOrder(row)

                                                if not moved:
                                                    self.clearPastTrade()

                                                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Entry Order Moved due to  Div Bar 1 Bar Back Found")
                                                self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} Entry Order Moved due to  Div Bar 1 Bar Back Found")
                                            else:
                                                self.fakeMoveEntryOrder(row)
                                                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Cooldown Entry Order Moved due to  Div Bar 1 Bar Back Found")
                                                self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} Cooldown Entry Order Moved due to  Div Bar 1 Bar Back Found")
                                        else:
                                            self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} ( Div Bar 1 Bar Back) Entry Order Not Moved because New Entry Price ({newPrice}) is less then current entry price({self.current_order['ENTRYORDER_PRICE']})")
                                            self.log(f"{index.strftime('%Y-%m-%d %H:%M')} ( Div Bar 1 Bar Back) Entry Order Not Moved because New Entry Price ({newPrice}) is less then current entry price({self.current_order['ENTRYORDER_PRICE']})")

                                    elif row["cci"] < self.current_order["STARTBAR_CCI"] and row["Close"] > self.current_order["STARTBAR_CLOSE"]:
                                        newPrice = row["Low"] - self.entryTickOffset

                                        if newPrice > self.current_order["ENTRYORDER_PRICE"]:
                                            oneTimeMove = True
                                            self.checkEntryOrderPrice = True
                                            if not self.fakeOrder:
                                                moved = self.moveEntryOrder(row)

                                                if not moved:
                                                    self.clearPastTrade()

                                                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Entry Order Moved due to  Div Bar Start Bar Found")
                                                self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} Entry Order Moved due to  Div Bar Start Bar Found")
                                            else:
                                                self.fakeMoveEntryOrder(row)
                                                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Cooldown Entry Order Moved due to  Div Bar Start Bar Found")
                                                self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} Cooldown Entry Order Moved due to  Div Bar Start Bar Found")
                                        else:
                                            self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} (Start Bar) Entry Order Not Moved because New Entry Price ({newPrice}) is less then current entry price({self.current_order['ENTRYORDER_PRICE']})")
                                            self.log(f"{index.strftime('%Y-%m-%d %H:%M')} (Start Bar) Entry Order Not Moved because New Entry Price ({newPrice}) is less then current entry price({self.current_order['ENTRYORDER_PRICE']})")

                                if self.forwardIfKeyReversal == "On" and oneTimeMove == False:
                                    if shortKeyReversal:
                                        newPrice = row["Low"] - self.entryTickOffset

                                        if newPrice > self.current_order["ENTRYORDER_PRICE"]:
                                            oneTimeMove = True
                                            self.checkEntryOrderPrice = True
                                            if not self.fakeOrder:
                                                moved = self.moveEntryOrder(row)

                                                if not moved:
                                                    self.clearPastTrade()

                                                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Entry Order Moved due to Short Reversal")
                                                self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} Entry Order Moved due to Short Reversal")
                                            else:
                                                self.fakeMoveEntryOrder(row)
                                                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Cooldown Entry Order Moved due to Short Reversal")
                                                self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} Cooldown Entry Order Moved due to Short Reversal")
                                        else:
                                            self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} (Short Reversal) Entry Order Not Moved because New Entry Price ({newPrice}) is less then current entry price({self.current_order['ENTRYORDER_PRICE']})")
                                            self.log(f"{index.strftime('%Y-%m-%d %H:%M')} (Short Reversal) Entry Order Not Moved because New Entry Price ({newPrice}) is less then current entry price({self.current_order['ENTRYORDER_PRICE']})")

                                if self.forwardIfLowerHigher == "On" and oneTimeMove == False:
                                    if row["Low"] > self.prevRow["Low"]:
                                        newPrice = row["Low"] - self.entryTickOffset

                                        if newPrice > self.current_order["ENTRYORDER_PRICE"]:
                                            oneTimeMove = True
                                            self.checkEntryOrderPrice = True
                                            if not self.fakeOrder:
                                                moved = self.moveEntryOrder(row)

                                                if not moved:
                                                    self.clearPastTrade()

                                                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Entry Order Moved due to Higher Low")
                                                self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} Entry Order Moved due to Higher Low")
                                            else:
                                                self.fakeMoveEntryOrder(row)
                                                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Cooldown Entry Order Moved due to Higher Low")
                                                self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} Cooldown Entry Order Moved due to Higher Low")
                                        else:
                                            self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} (Higher Low) Entry Order Not Moved because New Entry Price ({newPrice}) is less then current entry price({self.current_order['ENTRYORDER_PRICE']})")
                                            self.log(f"{index.strftime('%Y-%m-%d %H:%M')} (Higher Low) Entry Order Not Moved because New Entry Price ({newPrice}) is less then current entry price({self.current_order['ENTRYORDER_PRICE']})")

                                if not oneTimeMove:
                                    if self.keepOrderOpen == 1:
                                        self.current_order["ENTRYORDER_CANCELLED"] = True
                                    else:
                                        self.checkEntryOrderPrice = False

                else:
                    self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Keep Order Open = {self.orderAlreadyOpenFor}")

                    if self.entryFilled:
                        checkStopLossStatus = True
                        self.currentStatus = 4
                    else:
                        self.current_order["ENTRYORDER_CANCELLED"] = True

                if self.current_order["ENTRYORDER_CANCELLED"]:
                    self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Entry order not triggered. Cancelling the trade")
                    self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} Entry order not triggered. Cancelling the trade")

                    self.enableTradeOnAsset()
                    self.notTriggeredLogs()

                    if self.current_order['WALLET'] != "CROSS 3X":
                        self.transferAvailableMoneyOutOfISO(currTime=row.name, symbol=self.marginSymbol)

                    self.clearPastTrade()

        elif self.currentStatus == 4:
            checkStopLossStatus = True

        elif self.currentStatus == 5:
            check = True

            # if self.reEntryBarsCheckTillNow >= self.reEntryBars and self.postCloseDivCountTillNow >= self.postCloseDivBarWindow:
            #     self.clearPastTrade()
            #     check = False

            ##Re-Entry If Negative ROI
            if check and self.reEntryActive == "On":
                if self.reEntryBarsCheckTillNow < self.reEntryBars:
                    self.reEntryBarsCheckTillNow = self.reEntryBarsCheckTillNow + 1
                    # self.yprint(f"{index.strftime('%Y-%m-%d %H:%M')} Checking for Re-Entry {self.reEntryBarsCheckTillNow}")

                    if self.current_order["TYPE"] == "LONG":
                        if row["Close"] > self.closeOutBarCheck:
                            if self.reEntryStochFilterLong == 0 or (self.reEntryStochFilterLong != 0 and row["stoch"] < self.reEntryStochFilterLong):
                                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Re-Entry Condition Fulfilled")

                                if self.reEntryCheckTR == "On":
                                    self.current_order["TARGETRECOGINATION_PASSED"] = self.targetReconginitionTest(row, self.setupBarNo)

                                    if self.current_order["TARGETRECOGINATION_PASSED"]:
                                        self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Re-Entry, Target Recogination passed, order placed")
                                        self.current_order["TRADE_TYPE"] = "POSTCLOSE REENTRY"

                                        if self.fakeOrder:
                                            self.fakeEntryOrder(row)
                                            self.currentStatus = 3
                                            self.fakeOrder = True
                                            self.fakeType = self.checkCooldownType()
                                        else:
                                            if not self.checkReEntryTradesDisable():
                                                placed = self.placeEntryOrder(row)

                                                if placed:
                                                    self.disableTradeOnAsset()
                                                    self.currentStatus = 3  ##start looking for entry order and stoploss
                                                else:
                                                    self.clearPastTrade()
                                            else:
                                                self.fakeEntryOrder(row)
                                                self.currentStatus = 3
                                                self.fakeOrder = True
                                                self.fakeType = self.checkCooldownType()
                                    else:
                                        self.setupBarNo = self.setupBarNo + 1
                                        self.currentStatus = 2  ##recheck for setup bar
                                else:
                                    self.current_order["TRADE_TYPE"] = "POSTCLOSE REENTRY"
                                    if self.fakeOrder:
                                        self.fakeEntryOrder(row)
                                        self.currentStatus = 3
                                        self.fakeOrder = True
                                        self.fakeType = self.checkCooldownType()
                                    else:
                                        if not self.checkReEntryTradesDisable():
                                            placed = self.placeEntryOrder(row)

                                            if placed:
                                                self.disableTradeOnAsset()
                                                self.currentStatus = 3  ##start looking for entry order and stoploss
                                            else:
                                                self.clearPastTrade()
                                        else:
                                            self.fakeEntryOrder(row)
                                            self.currentStatus = 3
                                            self.fakeOrder = True
                                            self.fakeType = self.checkCooldownType()

                                check = False
                    elif self.current_order["TYPE"] == "SHORT":
                        if row["Close"] < self.closeOutBarCheck:
                            if self.reEntryStochFilterShort == 0 or (self.reEntryStochFilterShort != 0 and row["stoch"] > self.reEntryStochFilterShort):
                                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Re-Entry Condition Fulfilled")

                                if self.reEntryCheckTR == "On":
                                    self.current_order["TARGETRECOGINATION_PASSED"] = self.targetReconginitionTest(row, self.setupBarNo)

                                    if self.current_order["TARGETRECOGINATION_PASSED"]:
                                        self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Target Recogination passed, order placed")
                                        self.current_order["TRADE_TYPE"] = "POSTCLOSE REENTRY"
                                        if self.fakeOrder:
                                            self.fakeEntryOrder(row)
                                            self.currentStatus = 3
                                            self.fakeOrder = True
                                            self.fakeType = self.checkCooldownType()
                                        else:
                                            if not self.checkReEntryTradesDisable():
                                                placed = self.placeEntryOrder(row)

                                                if placed:
                                                    self.disableTradeOnAsset()
                                                    self.currentStatus = 3  ##start looking for entry order and stoploss
                                                else:
                                                    self.clearPastTrade()
                                            else:
                                                self.fakeEntryOrder(row)
                                                self.currentStatus = 3
                                                self.fakeOrder = True
                                                self.fakeType = self.checkCooldownType()
                                    else:
                                        self.setupBarNo = self.setupBarNo + 1
                                        self.currentStatus = 2  ##recheck for setup bar
                                else:
                                    self.current_order["TRADE_TYPE"] = "POSTCLOSE REENTRY"
                                    if self.fakeOrder:
                                        self.fakeEntryOrder(row)
                                        self.currentStatus = 3
                                        self.fakeOrder = True
                                        self.fakeType = self.checkCooldownType()
                                    else:
                                        if not self.checkReEntryTradesDisable():
                                            placed = self.placeEntryOrder(row)

                                            if placed:
                                                self.disableTradeOnAsset()
                                                self.currentStatus = 3  ##start looking for entry order and stoploss
                                            else:
                                                self.clearPastTrade()
                                        else:
                                            self.fakeEntryOrder(row)
                                            self.currentStatus = 3
                                            self.fakeOrder = True
                                            self.fakeType = self.checkCooldownType()

                                check = False

            if check and self.postCloseActive == "On":
                self.current_order["DIV_COMPLETED"] = False

                if self.postCloseSuccessfulDivCount == self.postCloseDivBarRequired and self.dcCheckTROnLastDivBar == "Off":
                    self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Post Close, Successful Div Count Reached")
                    self.current_order["BARS_REQUIRED_FROM_STARTBAR_TO_REACH_MINBAR_REQUIREMENT"] = self.postCloseDivCountTillNow

                    self.current_order["DIV_PASSED"] = True
                    self.current_order["DIV_COMPLETED"] = True

                elif self.postCloseDivCountTillNow < self.postCloseDivBarWindow:
                    self.postCloseDivCountTillNow = self.postCloseDivCountTillNow + 1

                    restartStartbar, cancelStartbar, prevBarResult, startBarResult = self.divTest(row, self.prevRow, self.postCloseSearchDivOnly, self.current_order["STARTBAR_CCI"], self.current_order["STARTBAR_CLOSE"])
                    self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Post Close, Checking Divergence on this candle, Count {self.postCloseDivCountTillNow} out of {self.postCloseDivBarWindow}. Successful Count - {self.postCloseSuccessfulDivCount}")

                    if prevBarResult:
                        self.postCloseSuccessfulDivCount = self.postCloseSuccessfulDivCount + 1
                        self.current_order[f"DIVBAR_TREND"].append((self.postCloseSuccessfulDivCount, "1 Bar Back"))

                    elif startBarResult:
                        self.postCloseSuccessfulDivCount = self.postCloseSuccessfulDivCount + 1
                        self.current_order[f"DIVBAR_TREND"].append((self.postCloseSuccessfulDivCount, "Start Bar"))

                    if self.postCloseSuccessfulDivCount == self.postCloseDivBarRequired:
                        if self.current_order['TYPE'] == "LONG":
                            if row["stoch"] > self.postCloseLastDivStochKOS:
                                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} - Post Close, Canceling Trade Because Last Div Bar Stoch ({row['stoch']}) More then Post Close LTF Stoch OS ({self.postCloseLastDivStochKOS})")
                                self.clearPastTrade()
                                self.current_order["DIV_COMPLETED"] = False
                            elif self.dcCheckTROnLastDivBar == "On":
                                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} - Post Close, Successful Div Count Reached")
                                self.current_order["BARS_REQUIRED_FROM_STARTBAR_TO_REACH_MINBAR_REQUIREMENT"] = self.postCloseDivCountTillNow

                                self.current_order["DIV_PASSED"] = True
                                self.current_order["DIV_COMPLETED"] = True
                        else:
                            if row["stoch"] < self.postCloseLastDivStochKOB:
                                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} - Post Close, Canceling Trade Because Last Div Bar Stoch ({row['stoch']}) Less then Post Close LTF Stoch OB ({self.postCloseLastDivStochKOB})")
                                self.clearPastTrade()
                                self.current_order["DIV_COMPLETED"] = False
                            elif self.dcCheckTROnLastDivBar == "On":
                                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} - Post Close, Successful Div Count Reached")
                                self.current_order["BARS_REQUIRED_FROM_STARTBAR_TO_REACH_MINBAR_REQUIREMENT"] = self.postCloseDivCountTillNow

                                self.current_order["DIV_PASSED"] = True
                                self.current_order["DIV_COMPLETED"] = True

                    elif self.postCloseDivCountTillNow == self.postCloseDivBarWindow and self.cancelFailedDivOnLastDivCandle == "On":
                        self.log(f"{index.strftime('%Y-%m-%d %H:%M')} - Post Close, Div window reached, not able to get enough successfully divergence")
                        self.current_order["DIVBAR_FOUND"] = self.postCloseSuccessfulDivCount

                        self.current_order["DIV_PASSED"] = False
                        self.current_order["DIV_COMPLETED"] = True

                elif self.postCloseDivCountTillNow == self.postCloseDivBarWindow and self.cancelFailedDivOnLastDivCandle == "Off":
                    self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Post Close, Div window reached, not able to get enough successfully divergence")
                    self.current_order["DIVBAR_FOUND"] = self.postCloseSuccessfulDivCount

                    self.current_order["DIV_PASSED"] = False
                    self.current_order["DIV_COMPLETED"] = True

                if self.current_order["DIV_COMPLETED"]:
                    if self.current_order["DIV_PASSED"]:
                        self.current_order["TARGETRECOGINATION_PASSED"] = self.targetReconginitionTest(row, self.setupBarNo)

                        if self.current_order["TARGETRECOGINATION_PASSED"]:
                            self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Post Close, Target Recogination passed, order placed")
                            self.current_order["TRADE_TYPE"] = "POSTCLOSE DIVENTRY"
                            if self.fakeOrder:
                                self.fakeEntryOrder(row)
                                self.currentStatus = 3
                                self.fakeOrder = True
                                self.fakeType = self.checkCooldownType()
                            else:
                                if not self.checkDivEntryTradesDisable():
                                    placed = self.placeEntryOrder(row)

                                    if placed:
                                        self.disableTradeOnAsset()
                                        self.currentStatus = 3  ##start looking for entry order and stoploss
                                    else:
                                        self.clearPastTrade()
                                else:
                                    self.fakeEntryOrder(row)
                                    self.currentStatus = 3
                                    self.fakeOrder = True
                                    self.fakeType = self.checkCooldownType()

                            check = False
                        else:
                            self.setupBarNo = self.setupBarNo + 1
                            self.currentStatus = 2  ##recheck for setup bar

                    elif not self.current_order["DIV_PASSED"]:
                        ###Divergence test failed###
                        self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Divergence Test failed")
                        self.divergenceFailedLog(self.current_order['DIVBAR_FOUND'])

            if check:
                if row["stoch"] > self.ltfStochKOB and row["cci"] > self.ltfCCIShortLimit:
                    # SHORT TYPE TRADE POSSIBLE
                    if self.tradeType == "Both" or self.tradeType == "Short":
                        passed, noShort, htfResult = self.htfTest(index, "SHORT")
                        htf1Result, htf2Result, htf3Result, htf4Result, htf5Result, htf6Result, htf7Result, htf8Result, htf9Result = htfResult
                        if passed:
                            self.clearPastTrade()

                            self.current_order["TYPE"] = "SHORT"
                            self.current_order["TRADE_TYPE"] = "STARTBAR ENTRY"
                            self.current_order["STARTBAR_TIME"] = index.strftime("%Y-%m-%d %H:%M")
                            self.current_order["STARTBAR_STOCH"] = row["stoch"]
                            self.current_order["STARTBAR_CCI"] = row["cci"]
                            self.current_order["STARTBAR_ATR"] = row["atr"]
                            self.current_order["STARTBAR_CLOSE"] = row["Close"]
                            self.current_order["HTF1_TREND"] = htf1Result
                            self.current_order["HTF2_TREND"] = htf2Result
                            self.current_order["HTF3_TREND"] = htf3Result
                            self.current_order["HTF4_TREND"] = htf4Result
                            self.current_order["HTF5_TREND"] = htf5Result
                            self.current_order["HTF6_TREND"] = htf6Result
                            self.current_order["HTF7_TREND"] = htf7Result
                            self.current_order["HTF8_TREND"] = htf8Result
                            self.current_order["HTF9_TREND"] = htf9Result
                            self.current_order["NO_OF_HTF_CONFIRMATION"] = noShort
                            self.current_order["DIV_COMPLETED"] = False
                            self.current_order["DIVBAR_TREND"] = []

                            if row["atr"] != 0:
                                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Startbar found - Short Type Trade")
                                self.discordLog(f"{index.strftime('%Y-%m-%d %H:%M')} Startbar found - Short Type Trade")
                                self.currentStatus = 1
                                check = False

                elif row["stoch"] < self.ltfStochKOS and row["cci"] < self.ltfCCILongLimit:
                    # LONG TYPE TRADE POSSIBLE
                    if self.tradeType == "Both" or self.tradeType == "Long":
                        passed, noLong, htfResult = self.htfTest(index, "LONG")
                        htf1Result, htf2Result, htf3Result, htf4Result, htf5Result, htf6Result, htf7Result, htf8Result, htf9Result = htfResult
                        if passed:
                            self.clearPastTrade()

                            self.current_order["TYPE"] = "LONG"
                            self.current_order["TRADE_TYPE"] = "STARTBAR ENTRY"
                            self.current_order["STARTBAR_TIME"] = index.strftime("%Y-%m-%d %H:%M")
                            self.current_order["STARTBAR_STOCH"] = row["stoch"]
                            self.current_order["STARTBAR_CCI"] = row["cci"]
                            self.current_order["STARTBAR_ATR"] = row["atr"]
                            self.current_order["STARTBAR_CLOSE"] = row["Close"]
                            self.current_order["HTF1_TREND"] = htf1Result
                            self.current_order["HTF2_TREND"] = htf2Result
                            self.current_order["HTF3_TREND"] = htf3Result
                            self.current_order["HTF4_TREND"] = htf4Result
                            self.current_order["HTF5_TREND"] = htf5Result
                            self.current_order["HTF6_TREND"] = htf6Result
                            self.current_order["HTF7_TREND"] = htf7Result
                            self.current_order["HTF8_TREND"] = htf8Result
                            self.current_order["HTF9_TREND"] = htf9Result
                            self.current_order["NO_OF_HTF_CONFIRMATION"] = noLong
                            self.current_order["DIV_COMPLETED"] = False
                            self.current_order["DIVBAR_TREND"] = []

                            if row["atr"] != 0:
                                self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Startbar found - Long Type Trade")
                                self.discordLog(f"{index.strftime('%Y-%m-%d %H:%M')} Startbar found - Long Type Trade")
                                self.currentStatus = 1
                                check = False

            if check:
                if self.postCloseActive == "On" and self.reEntryActive == "On":
                    if self.reEntryBarsCheckTillNow >= self.reEntryBars and self.postCloseDivCountTillNow >= self.postCloseDivBarWindow:
                        self.clearPastTrade()

                elif self.postCloseActive == "On" and self.reEntryActive == "Off":
                    if self.postCloseDivCountTillNow >= self.postCloseDivBarWindow:
                        self.clearPastTrade()

                elif self.postCloseActive == "Off" and self.reEntryActive == "On":
                    if self.reEntryBarsCheckTillNow >= self.reEntryBars:
                        self.clearPastTrade()

        if checkStopLossStatus:
            if self.stoplossFilled:
                self.current_order["TRADE_STATUS"] = "COMPLETE"

                self.current_order["TSL_STOCHK"] = row["stoch"]
                self.current_order["TSL_BARS"] = self.trailSTL

                self.log(f"{index.strftime('%Y-%m-%d %H:%M:%S')} Stoploss order got hit at {self.current_order['EXITORDER_AVG_PRICE']}")
                self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M:%S')} Stoploss order got hit at {self.current_order['EXITORDER_AVG_PRICE']}")

                if self.current_order['WALLET'] != "CROSS 3X":
                    self.transferAvailableMoneyOutOfISO(currTime=row.name, symbol=self.marginSymbol)

                if self.current_order["TYPE"] == "LONG":
                    roi = ((float(self.current_order["EXITORDER_AVG_PRICE"]) - float(self.current_order["ENTRYORDER_AVG_PRICE"])) / float(self.current_order["ENTRYORDER_AVG_PRICE"])) * 100
                else:
                    roi = ((float(self.current_order["ENTRYORDER_AVG_PRICE"]) - float(self.current_order["EXITORDER_AVG_PRICE"])) / float(self.current_order["ENTRYORDER_AVG_PRICE"])) * 100

                if self.fakeOrder:
                    fakeSheet = self.cooldownV1StartbarSheet

                    if self.fakeType == "mute":
                        if self.current_order["TRADE_TYPE"] == "STARTBAR ENTRY":
                            fakeSheet = self.cooldownV1StartbarSheet
                        elif self.current_order["TRADE_TYPE"] == "POSTCLOSE DIVENTRY":
                            fakeSheet = self.cooldownV1DivEntrySheet
                            roi = 2 * roi
                        elif self.current_order["TRADE_TYPE"] == "POSTCLOSE REENTRY":
                            fakeSheet = self.cooldownV1ReEntrySheet
                            roi = 2 * roi
                    elif self.fakeType == "v3disable":
                        if self.current_order["TRADE_TYPE"] == "STARTBAR ENTRY":
                            fakeSheet = self.cooldownV3StartbarSheet
                        elif self.current_order["TRADE_TYPE"] == "POSTCLOSE DIVENTRY":
                            fakeSheet = self.cooldownV3DivEntrySheet
                            roi = 2 * roi
                        elif self.current_order["TRADE_TYPE"] == "POSTCLOSE REENTRY":
                            fakeSheet = self.cooldownV3ReEntrySheet
                            roi = 2 * roi
                    else:
                        if self.current_order["TRADE_TYPE"] == "STARTBAR ENTRY":
                            fakeSheet = self.cooldownV2StartbarSheet
                        elif self.current_order["TRADE_TYPE"] == "POSTCLOSE DIVENTRY":
                            fakeSheet = self.cooldownV2DivEntrySheet
                            roi = 2 * roi
                        elif self.current_order["TRADE_TYPE"] == "POSTCLOSE REENTRY":
                            fakeSheet = self.cooldownV2ReEntrySheet
                            roi = 2 * roi

                    new_row = [self.marginSymbol,
                               self.current_order['TYPE'],
                               str(self.current_order["ENTRY_TIME"]),
                               str(self.current_order["EXIT_TIME"]),
                               str(self.current_order["ENTRYORDER_AVG_PRICE"]),
                               str(self.current_order["EXITORDER_AVG_PRICE"]),
                               roi
                               ]

                    cells = fakeSheet.get_all_values(include_tailing_empty_rows=False, include_tailing_empty=False, returnas='matrix')
                    last_row = len(cells)
                    fakeSheet.insert_rows(last_row, number=1, values=new_row)

                if roi < 0:
                    if self.reEntryActive == "On" and self.reEntryCyclesCheckTillNow < self.reEntryCycles:
                        self.reEntryCyclesCheckTillNow = self.reEntryCyclesCheckTillNow + 1
                        self.postCloseCheckTillNow = self.postCloseCheckTillNow + 1

                        self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Re-Entry Cycle - {self.reEntryCyclesCheckTillNow}")

                        self.setupBarNo = 0
                        self.orderAlreadyOpenFor = 0
                        self.trailSTL = self.TSLBars
                        self.dcSetupBarLeft = self.dcSetupBarRechecks

                        self.reEntryBarsCheckTillNow = 0
                        self.closeOutBarCheck = row["Low"]

                        self.postCloseSuccessfulDivCount = 0
                        self.postCloseDivCountTillNow = 0

                        self.checkStoplossOrderPrice = False
                        self.checkEntryOrderPrice = False
                        self.entryFilled = False
                        self.stoplossFilled = False

                        self.currentStatus = 5
                    elif self.postCloseActive == "On" and self.postCloseCheckTillNow < self.postCloseCylces:
                        self.reEntryCyclesCheckTillNow = self.reEntryCyclesCheckTillNow + 1
                        self.postCloseCheckTillNow = self.postCloseCheckTillNow + 1

                        self.log(f"{index.strftime('%Y-%m-%d %H:%M')} Post Close Cycle - {self.postCloseCheckTillNow}")

                        self.setupBarNo = 0
                        self.orderAlreadyOpenFor = 0
                        self.trailSTL = self.TSLBars
                        self.dcSetupBarLeft = self.dcSetupBarRechecks

                        self.reEntryBarsCheckTillNow = 0
                        self.closeOutBarCheck = row["Low"]

                        self.postCloseSuccessfulDivCount = 0
                        self.postCloseDivCountTillNow = 0

                        self.checkStoplossOrderPrice = False
                        self.checkEntryOrderPrice = False
                        self.entryFilled = False
                        self.stoplossFilled = False

                        self.currentStatus = 5
                    else:
                        self.clearPastTrade()
                else:
                    self.clearPastTrade()
            else:
                if self.tsl == "STOP":
                    if self.trailSL == "LTF":
                        prevCandle = self.ltfData.iloc[self.ltfData.index.get_loc(index)]
                        prevprevCandle = self.ltfData.iloc[self.ltfData.index.get_loc(index) - 1]
                        prevprevprevCandle = self.ltfData.iloc[self.ltfData.index.get_loc(index) - 2]
                    elif self.trailSL == "DTF1":
                        prevCandle = self.dtf1Data.iloc[-1]
                        prevprevCandle = self.dtf1Data.iloc[-2]
                        prevprevprevCandle = self.dtf1Data.iloc[-3]
                    elif self.trailSL == "DTF2":
                        prevCandle = self.dtf2Data.iloc[-1]
                        prevprevCandle = self.dtf2Data.iloc[-2]
                        prevprevprevCandle = self.dtf2Data.iloc[-3]
                    elif self.trailSL == "DTF3":
                        prevCandle = self.dtf3Data.iloc[-1]
                        prevprevCandle = self.dtf3Data.iloc[-2]
                        prevprevprevCandle = self.dtf3Data.iloc[-3]
                    elif self.trailSL == "DTF4":
                        prevCandle = self.dtf4Data.iloc[-1]
                        prevprevCandle = self.dtf4Data.iloc[-2]
                        prevprevprevCandle = self.dtf4Data.iloc[-3]
                    elif self.trailSL == "DTF5":
                        prevCandle = self.dtf5Data.iloc[-1]
                        prevprevCandle = self.dtf5Data.iloc[-2]
                        prevprevprevCandle = self.dtf5Data.iloc[-3]
                    elif self.trailSL == "DTF6":
                        prevCandle = self.dtf6Data.iloc[-1]
                        prevprevCandle = self.dtf6Data.iloc[-2]
                        prevprevprevCandle = self.dtf6Data.iloc[-3]
                    elif self.trailSL == "DTF7":
                        prevCandle = self.dtf7Data.iloc[-1]
                        prevprevCandle = self.dtf7Data.iloc[-2]
                        prevprevprevCandle = self.dtf7Data.iloc[-3]
                    else:
                        prevCandle = self.dtf8Data.iloc[-1]
                        prevprevCandle = self.dtf8Data.iloc[-2]
                        prevprevprevCandle = self.dtf8Data.iloc[-3]

                    if self.current_order["TYPE"] == "LONG":
                        if row["stoch"] >= self.STLstochKOB and self.trailSTL != 1:
                            self.log(f"{index.strftime('%Y-%m-%d %H:%M')} ShochK({str(row['stoch'])}) more than ShochK OB Level({str(self.STLstochKOB)}), Changing to 1 bar stop")
                            self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} ShochK({str(row['stoch'])}) more than ShochK OB Level({str(self.STLstochKOB)}), Changing to 1 bar stop")
                            self.trailSTL = 1

                        lowprevCandle = prevCandle["Low"]
                        lowprevprevCandle = prevprevCandle["Low"]
                        lowprevprevprevCandle = prevprevprevCandle["Low"]

                        if self.trailSTL == 1:
                            lowest = lowprevCandle
                        elif self.trailSTL == 2:
                            lowest = min(lowprevCandle, lowprevprevCandle)
                        else:
                            lowest = min(lowprevCandle, lowprevprevCandle)
                            lowest = min(lowest, lowprevprevprevCandle)

                        newStoploss = lowest - (lowest * self.TSLOffset)

                        if newStoploss > self.current_order["STOPLOSSORDER_PRICE"] and newStoploss <= row['Close']:
                            self.current_order["STOPLOSSORDER_PRICE"] = newStoploss
                            self.stopLossLongPosition(currtime=row.name, price=self.current_order["STOPLOSSORDER_PRICE"])

                    elif self.current_order["TYPE"] == "SHORT":
                        if row["stoch"] <= self.STLstochKOS and self.trailSTL != 1:
                            self.log(f"{index.strftime('%Y-%m-%d %H:%M')} ShochK({str(row['stoch'])}) less than ShochK OS Level({str(self.STLstochKOB)}), Changing to 1 bar stop")
                            self.orderLogs(f"{index.strftime('%Y-%m-%d %H:%M')} ShochK({str(row['stoch'])}) less than ShochK OS Level({str(self.STLstochKOB)}), Changing to 1 bar stop")
                            self.trailSTL = 1

                        highprevCandle = prevCandle["High"]
                        highprevprevCandle = prevprevCandle["High"]
                        highprevprevprevCandle = prevprevprevCandle["High"]

                        if self.trailSTL == 1:
                            highest = highprevCandle
                        elif self.trailSTL == 2:
                            highest = max(highprevCandle, highprevprevCandle)
                        else:
                            highest = max(highprevCandle, highprevprevCandle)
                            highest = max(highest, highprevprevprevCandle)

                        newStoploss = highest + (highest * self.TSLOffset)

                        if newStoploss < self.current_order["STOPLOSSORDER_PRICE"] and newStoploss >= row['Close']:
                            self.current_order["STOPLOSSORDER_PRICE"] = newStoploss
                            self.stopLossShortPosition(currtime=row.name, price=self.current_order["STOPLOSSORDER_PRICE"])

                elif self.tsl == "ATR":
                    if self.trailSL == "DTF1":
                        prevCandle = self.dtf1Data.iloc[-1]
                    elif self.trailSL == "DTF2":
                        prevCandle = self.dtf2Data.iloc[-1]
                    elif self.trailSL == "DTF3":
                        prevCandle = self.dtf3Data.iloc[-1]
                    elif self.trailSL == "DTF4":
                        prevCandle = self.dtf4Data.iloc[-1]
                    elif self.trailSL == "DTF5":
                        prevCandle = self.dtf5Data.iloc[-1]
                    elif self.trailSL == "DTF6":
                        prevCandle = self.dtf6Data.iloc[-1]
                    elif self.trailSL == "DTF7":
                        prevCandle = self.dtf7Data.iloc[-1]
                    else:
                        prevCandle = self.dtf8Data.iloc[-1]

                    atrStoploss = prevCandle["atr"] * (self.tslAtrPerc / 100)
                    ltfCandle = self.ltfData.iloc[-1]

                    if self.current_order["TYPE"] == "LONG":
                        newStoploss = ltfCandle["High"] - atrStoploss

                        if newStoploss > self.current_order["STOPLOSSORDER_PRICE"] and newStoploss <= row['Close']:
                            self.current_order["STOPLOSSORDER_PRICE"] = newStoploss
                            self.stopLossLongPosition(currtime=row.name, price=self.current_order["STOPLOSSORDER_PRICE"])

                    elif self.current_order["TYPE"] == "SHORT":
                        newStoploss = ltfCandle["Low"] + atrStoploss

                        if newStoploss < self.current_order["STOPLOSSORDER_PRICE"] and newStoploss >= row['Close']:
                            self.current_order["STOPLOSSORDER_PRICE"] = newStoploss
                            self.stopLossShortPosition(currtime=row.name, price=self.current_order["STOPLOSSORDER_PRICE"])

        self.checkSwing(index)