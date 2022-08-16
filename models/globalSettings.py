from mongoengine import Document, StringField, IntField, FloatField


class GlobalSettings(Document):
    tradeType = StringField(required=True)
    minHTFConfirmedRequired = IntField(required=True)

    htf1Manual = StringField(required=True)
    htf1Method = StringField(required=True)
    htf1StochKOB = IntField(required=True)
    htf1StochKOS = IntField(required=True)
    htf1MACDfastLength = IntField(required=True)
    htf1MACDslowLength = IntField(required=True)
    htf1MACDSmoothing = IntField(required=True)
    htf1EMA = IntField(required=True)

    htf2Method = StringField(required=True)
    htf2StochKOB = IntField(required=True)
    htf2StochKOS = IntField(required=True)
    htf2MACDfastLength = IntField(required=True)
    htf2MACDslowLength = IntField(required=True)
    htf2MACDSmoothing = IntField(required=True)
    htf2EMA = IntField(required=True)

    htf3Method = StringField(required=True)
    htf3StochKOB = IntField(required=True)
    htf3StochKOS = IntField(required=True)
    htf3MACDfastLength = IntField(required=True)
    htf3MACDslowLength = IntField(required=True)
    htf3MACDSmoothing = IntField(required=True)
    htf3EMA = IntField(required=True)

    htf4Button = StringField(required=True)
    htf4Method = StringField(required=True)
    htf4TimeFrame = StringField(required=True)

    htf5Button = StringField(required=True)
    htf5Method = StringField(required=True)
    htf5TimeFrame = StringField(required=True)

    htf6Button = StringField(required=True)
    htf6Method = StringField(required=True)
    htf6TimeFrame = StringField(required=True)

    htf7Button = StringField(required=True)
    htf7Method = StringField(required=True)
    htf7TimeFrame = StringField(required=True)

    htf8Button = StringField(required=True)
    htf8Method = StringField(required=True)
    htf8TimeFrame = StringField(required=True)

    htf9Button = StringField(required=True)
    htf9Method = StringField(required=True)
    htf9TimeFrame = StringField(required=True)

    ltfStochKLength = IntField(required=True)
    ltfCCILength = IntField(required=True)

    countSameAsDiv = StringField(required=True)
    cancelFailedDivOnLastDivCandle = StringField(required=True)

    dcLevelMultiplier = IntField(required=True)
    dcLookbackPeriod = IntField(required=True)
    dcSwingRedraws = IntField(required=True)
    dcCheckTROnLastDivBar = StringField(required=True)
    checkTRIfInside = StringField(required=True)
    checkTRIfDivBarBoth = StringField(required=True)
    checkTRIfKeyReversal = StringField(required=True)

    alwaysMoveForward = StringField(required=True)
    forwardIfInside = StringField(required=True)
    forwardIfDivBar1BarBack = StringField(required=True)
    forwardIfDivBarBoth = StringField(required=True)
    forwardIfKeyReversal = StringField(required=True)
    forwardIfLowerHigher = StringField(required=True)

    STLbars = IntField(required=True)
    TSLOffset = FloatField(required=True)

    reEntryCycles = IntField(required=True)
    reEntryCheckTR = StringField(required=True)

    postCloseSearchDivOnly = StringField(required=True)

    dtfMinPass = IntField(required=True)
    checkDTF = StringField(required=True)
    checkDTF1 = StringField(required=True)
    checkDTF2 = StringField(required=True)
    checkDTF3 = StringField(required=True)
    checkDTF4 = StringField(required=True)
    checkDTF5 = StringField(required=True)
    checkDTF6 = StringField(required=True)
    checkDTF7 = StringField(required=True)

    atrParameter = IntField(required=True)
    quantityPercentageDown = IntField(required=True)
    quantityPercentageDownTimes = IntField(required=True)

    usdtPair = StringField(required=True)

    tier1_cross3x = FloatField(required=True)
    tier1_3x = FloatField(required=True)
    tier1_5x = FloatField(required=True)
    tier1_10x = FloatField(required=True)

    tier2_cross3x = FloatField(required=True)
    tier2_3x = FloatField(required=True)
    tier2_5x = FloatField(required=True)
    tier2_10x = FloatField(required=True)

    tier3_cross3x = FloatField(required=True)
    tier3_3x = FloatField(required=True)
    tier3_5x = FloatField(required=True)
    tier3_10x = FloatField(required=True)

    tier4_cross3x = FloatField(required=True)
    tier4_3x = FloatField(required=True)
    tier4_5x = FloatField(required=True)
    tier4_10x = FloatField(required=True)

    tier5_cross3x = FloatField(required=True)
    tier5_3x = FloatField(required=True)
    tier5_5x = FloatField(required=True)
    tier5_10x = FloatField(required=True)

    wallet_iso10 = FloatField(required=True)
    wallet_iso5 = FloatField(required=True)
    wallet_iso3 = FloatField(required=True)
    wallet_cross3 = FloatField(required=True)
    wallet_spot = FloatField(required=True)
