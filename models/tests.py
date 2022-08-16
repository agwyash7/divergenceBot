from mongoengine import Document, StringField, IntField, FloatField, BooleanField


class Tests(Document):
    symbol = StringField(required=True)
    historicalSymbol = StringField(required=True)
    marginSymbol = StringField(required=True)
    coinPair = StringField(required=True)
    baseAsset = StringField(required=True)

    htf1TimeFrame = StringField(required=True)
    htf2TimeFrame = StringField(required=True)
    htf3TimeFrame = StringField(required=True)

    htf4StochKOB = IntField(required=True)
    htf4StochKOS = IntField(required=True)
    htf5StochKOB = IntField(required=True)
    htf5StochKOS = IntField(required=True)
    htf6StochKOB = IntField(required=True)
    htf6StochKOS = IntField(required=True)
    htf7StochKOB = IntField(required=True)
    htf7StochKOS = IntField(required=True)
    htf8StochKOB = IntField(required=True)
    htf8StochKOS = IntField(required=True)
    htf9StochKOB = IntField(required=True)
    htf9StochKOS = IntField(required=True)

    dtfCCILongLimit = IntField(required=True)
    dtfCCIShortLimit = IntField(required=True)
    dtfStochKOB = IntField(required=True)
    dtfStochKOS = IntField(required=True)

    dtf1Timeframe = StringField(required=True)
    dtf1DivWindow = IntField(required=True)
    dtf1DivRequired = IntField(required=True)
    dtf1LastDivStochKOB = IntField(required=True)
    dtf1LastDivStochKOS = IntField(required=True)

    dtf2Timeframe = StringField(required=True)
    dtf2DivWindow = IntField(required=True)
    dtf2DivRequired = IntField(required=True)
    dtf2LastDivStochKOB = IntField(required=True)
    dtf2LastDivStochKOS = IntField(required=True)

    dtf3Timeframe = StringField(required=True)
    dtf3DivWindow = IntField(required=True)
    dtf3DivRequired = IntField(required=True)
    dtf3LastDivStochKOB = IntField(required=True)
    dtf3LastDivStochKOS = IntField(required=True)

    dtf4Timeframe = StringField(required=True)
    dtf4DivWindow = IntField(required=True)
    dtf4DivRequired = IntField(required=True)
    dtf4LastDivStochKOB = IntField(required=True)
    dtf4LastDivStochKOS = IntField(required=True)

    dtf5Timeframe = StringField(required=True)
    dtf5DivWindow = IntField(required=True)
    dtf5DivRequired = IntField(required=True)
    dtf5LastDivStochKOB = IntField(required=True)
    dtf5LastDivStochKOS = IntField(required=True)

    dtf6Timeframe = StringField(required=True)
    dtf6DivWindow = IntField(required=True)
    dtf6DivRequired = IntField(required=True)
    dtf6LastDivStochKOB = IntField(required=True)
    dtf6LastDivStochKOS = IntField(required=True)

    dtf7Timeframe = StringField(required=True)
    dtf7DivWindow = IntField(required=True)
    dtf7DivRequired = IntField(required=True)
    dtf7LastDivStochKOB = IntField(required=True)
    dtf7LastDivStochKOS = IntField(required=True)

    dtf8Timeframe = StringField(required=True)
    dtf8DivWindow = IntField(required=True)
    dtf8DivRequired = IntField(required=True)
    dtf8LastDivStochKOB = IntField(required=True)
    dtf8LastDivStochKOS = IntField(required=True)
    checkDTF8 = StringField(required=True)

    ltfTimeFrame = StringField(required=True)
    ltfStochKOB = IntField(required=True)
    ltfStochKOS = IntField(required=True)
    ltfCCILongLimit = IntField(required=True)
    ltfCCIShortLimit = IntField(required=True)

    divBarWindow = IntField(required=True)
    divBarRequired = IntField(required=True)
    startBarRecheck = StringField(required=True)
    searchDivOnly = StringField(required=True)
    lastDivStochKOB = IntField(required=True)
    lastDivStochKOS = IntField(required=True)

    dcSetupBarRechecks = IntField(required=True)
    swingStrength = IntField(required=True)
    targetRecognitionAllowance = FloatField(required=True)

    initialSLOffset = FloatField(required=True)
    maxSL = FloatField(required=True)
    trailSL = StringField(required=True)

    keepOrderOpen = IntField(required=True)
    entryTickOffset = FloatField(required=True)

    STLstochKOB = IntField(required=True)
    STLstochKOS = IntField(required=True)

    reEntryActive = StringField(required=True)
    reEntryBars = IntField(required=True)
    reEntryStochFilterShort = IntField(required=True)
    reEntryStochFilterLong = IntField(required=True)

    postCloseActive = StringField(required=True)
    postCloseDivBarWindow = IntField(required=True)
    postCloseDivBarRequired = IntField(required=True)
    postCloseLastDivStochKOB = IntField(required=True)
    postCloseLastDivStochKOS = IntField(required=True)

    isActive = BooleanField(required=True)
    onlyISO = BooleanField(required=True)
    sheetNo = IntField(required=True)
    logSheet = StringField(required=True)
