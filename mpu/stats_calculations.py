from typing import Dict, Any

import pandas as pd

AFTER_AGG_NAMES = {
    "Amount/sum": "TNb",
    "Amount/median": "MedNb",
    "PriceXAmount/sum": "TVal",
    "Price/median": "MedVal",
}
AGGS = {
    "Amount": ["sum", "median"],
    "PriceXAmount": "sum",
    "Price": "median"
}


def transformations(grp: pd.DataFrame, data: pd.DataFrame) -> Dict[str, pd.Series]:
    return {
        "AvgVal": grp["PriceXAmount/sum"] / grp["Amount/sum"],
        "%(Nb)": grp["Amount/sum"] / data["Amount"].sum() * 100,
        "%(Val)": grp["PriceXAmount/sum"] / data["PriceXAmount"].sum() * 100
    }


def aggregate_data(data: pd.DataFrame, index_name: str, group_name: str = None, index: Any = None):
    if group_name is not None:
        _stats_series = data.groupby(by=group_name)
    else:
        _stats_series = data

    _stats_series = _stats_series.agg(AGGS)

    if group_name is None:
        _stats_series = _stats_series.unstack().dropna()
        _stats_series.index = [f"{label}/{agg}" for label, agg in _stats_series.index]
    else:
        _stats_series.columns = [f"{label}/{agg}" for label, agg in _stats_series.columns]

    for col_name, value in transformations(_stats_series, data).items():
        _stats_series[col_name] = value

    if isinstance(_stats_series, pd.Series):
        _stats_series = _stats_series.rename(index=AFTER_AGG_NAMES)
        _stats_series.index = pd.MultiIndex.from_product([[index_name], [index_name], _stats_series.index])
    else:
        _stats_series = _stats_series.rename(columns=AFTER_AGG_NAMES).stack()
        _stats_series.index = pd.MultiIndex.from_product(
            [
                [index_name],
                _stats_series.index.get_level_values(level=0).unique(),
                _stats_series.index.get_level_values(level=1).unique()
            ]
        )

    _stats_series = _stats_series.to_frame().T

    if index is not None:
        _stats_series.index = index

    return _stats_series
