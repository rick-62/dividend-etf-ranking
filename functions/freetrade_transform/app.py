import pandas as pd
from typing import Dict


def lambda_handler(ft: pd.DataFrame, params: Dict):
    """transform Freetrade data"""

    # cleanse columns
    ft.columns = ft.columns.str.lower()
    ft.fractional_enabled.fillna(False, inplace=True)
    ft.symbol = ft.symbol.str.replace(".", "", regex=True)
    ft.currency = ft.currency.str.upper()

    # convert mic to exchange e.g. XLON: London (for joining to investpy)
    ft["stock_exchange"] = [params["freetrade_mic_remap"].get(x) for x in ft.mic]

    # concatenate suffix e.g. "XLON" -> ".LON" (for joining to alpha vantage)
    ft["symbol_alphavantage"] = ft.symbol.str.cat(
        [params["alpha_vantage_symbol_suffix"].get(x, "") for x in ft.mic]
    )

    # concatenate suffix e.g. "XLON" -> ".L" (for joining to Yahoo data) & some corrections
    ft["symbol_yahoo"] = ft.symbol.str.cat(
        [params["yahoo_symbol_suffix"].get(x, "") for x in ft.mic]
    ).replace(params["yahoo_symbol_correction"])

    # create description column for later searching/filtering
    ft["description"] = (ft.title + " " + ft.long_title + " " + ft.subtitle).str.upper()

    # flag ETF stock
    ft["ETF_flag"] = ft["description"].str.contains(" ETF")

    # apply index
    ft.set_index('isin', inplace=True)

    return ft