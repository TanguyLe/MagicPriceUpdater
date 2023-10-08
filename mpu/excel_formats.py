INDEX_NAME = "datetime"

SHORT_STATS_COLUMNS_FORMAT = {
    INDEX_NAME: {"width": 8},
    "NbCards": {"width": 2.2},
    "NbFoil": {"width": 2.65},
    "NbNotFoil": {"width": 3},
    "FoilPercentage": {"width": 4},
    "NbCardsSup5": {"width": 3.5},
    "NbCardsInf0.30": {"width": 4},
    "AvgCardPrice": {"width": 4.25},
    "StockTotalValue": {"width": 4.25},
}

LARGE_STATS_COLUMNS_FORMAT = {
    INDEX_NAME: {"width": 6},
    "TNb": {"width": 2.3},
    "TVal": {"width": 2.3},
    "AvgVal": {"width": 2.3},
    "%(Nb)": {"width": 2},
    "%(Val)": {"width": 2},
    ("Condition", "EX", None): {"color": "FFFF00"},
    ("Condition", "LP", None): {"color": "FFFF00"},
    ("Condition", "PL", None): {"color": "FFFF00"},
    ("Foil?", "N", None): {"color": "FFFF00"},
    ("Global", "Global", None): {"color": "FFFF00"},
    ("Language", "French", None): {"color": "FFFF00"},
    ("PriceCategories", "10to20", None): {"color": "FFFF00"},
    ("PriceCategories", "0.30to2", None): {"color": "FFFF00"},
    ("Signed?", "N", None): {"color": "FFFF00"},
}

STOCK_COLUMNS_FORMAT = {
    "idArticle": {"hidden": True},
    "Local Name": {"hidden": True},
    "English Name": {"width": 7.5},
    "Exp. Name": {"hidden": True},
    "Signed?": {"hidden": True},
    "Playset?": {"hidden": True},
    "Altered?": {"hidden": True},
    "idCurrency": {"hidden": True},
    "Currency Code": {"hidden": True},
    "Price": {"color": "949494E8"},
}

STOCK_WITH_NEW_PRICE_COLUMNS_FORMAT = {
    **STOCK_COLUMNS_FORMAT,
    **{
        "SuggestedPrice": {"color": "949494E8"},
        "PriceApproval": {"color": "FFF0F8FF"},
    },
}
