import os
import yfinance as yf
import pandas as pd
import numpy as np
from functions_etfReturns import *
from functions_indicators import *
from datetime import datetime


def main():
    #lista de acciones
    stocks = ["UUP", "UDN", "CEW", "DBP", "GLD", "SLV", "PPLT", "DBE", "DBO", "UNG", "DBB", "CPER", "PALL", "DBA", "NIB", "WEAT", "CANE", "JO", "CORN", "SOYB", "BAL", "COW", "SPY", "EWC", "EWO", "EWK", "EDEN", "EFNL", "EWQ", "EWG", "GREK", "EIRL", "EWI", "EWN", "ENOR", "PGAL", "EWP", "EWD", "EWL", "EWU", "EIS", "EWA", "EWH", "EWJ", "ENZL", "EWS", "EWW", "EWZ", "ECH", "GXG", "EPU", "INDA", "MCHI", "CNYA", "EIDO", "EWY", "EWM", "EPHE", "EWT", "THD", "EPOL", "TUR", "EZA", "XLE", "OIH", "XOP", "XLU", "XLP", "FTXG", "XLY", "XHB", "XRT", "XLRE", "XTL", "XLI", "ITA", "XTN", "XLV", "XHE", "XHS", "BBH", "PPH", "XLK", "SMH", "XSW", "XTH", "XLB", "XME", "GDX", "SIL", "SLX", "XLF", "KCE", "KBE", "KRE", "IAK", "DIA", "XLG", "IWB", "IWM", "IWC", "SPYG", "SPYD", "SPYV", "SDY", "VIG", "PFF", "QUAL", "MTUM", "ESGU", "SUSL", "ESML", "SPHB", "BTAL", "SPLV", "BNDD", "INFL", "EMB", "LEMB", "LQD", "LQDH", "HYG", "HYGH"]


    #DF vacío, índice = date, donde va desde 1800 hasta hoy.
    hoy = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    df = pd.DataFrame(index=pd.date_range(start=datetime(1800, 1, 1), end=hoy, freq="B")) #freq B -> business days

    df = add_data_dataframe(stocks, df, "5y") #lleno el df con data de cada stock
    cleaning_dataframe(df) #función que limpia datos

    prices_file_path = os.path.join("technicalIndicatorsExcel", "etfPrices.xlsx")
    df.to_excel(prices_file_path, index=True) #lo paso a un excel

    #-----------------dataframe con porcentajes----------------------
    df = pd.read_excel(prices_file_path, index_col="Date", engine="openpyxl")

    indicatorsDF = pd.DataFrame(index=df.columns, columns=["current/200media", "50media/200media", "current/min(52 weeks)", "current/max(52 weeks)", "RSI7d", "RSI14d", "RSI21d", "RSI70d", "MACD", "signal"])
    indicatorsDF.index.name = "Stock"

    for stock in df.columns:
        currentDate = df.index[-1] #última fecha
        current = df[stock].loc[currentDate]

        #extraigo toda la data usando funciones de functions_indicators.py
        media200 = find_media_rounds(df, stock, 200)
        media50 = find_media_rounds(df, stock, 50)

        min_52_weeks = min_price(df, stock, 52)
        max_52_weeks = max_price(df, stock, 52)

        RSI7d = rsi_tradingview(df, stock, 7)
        RSI14d = rsi_tradingview(df, stock, 14)
        RSI21d = rsi_tradingview(df, stock, 21)
        RSI70d = rsi_tradingview(df, stock, 70)

        macd, signal = calculate_macd(df, stock)


        #meto la información en el dataframe en respectivo lugar
        indicatorsDF.loc[stock, "current/200media"] = round(((current / media200)-1)*100, 2)
        indicatorsDF.loc[stock, "50media/200media"] = round(((media50 / media200)-1)*100, 2)
        indicatorsDF.loc[stock, "current/min(52 weeks)"] = round(((current / min_52_weeks)-1)*100, 2)
        indicatorsDF.loc[stock, "current/max(52 weeks)"] = round(((current / max_52_weeks)-1)*100, 2)
        indicatorsDF.loc[stock, "RSI7d"] = round(RSI7d, 2)
        indicatorsDF.loc[stock, "RSI14d"] = round(RSI14d, 2)
        indicatorsDF.loc[stock, "RSI21d"] = round(RSI21d, 2)
        indicatorsDF.loc[stock, "RSI70d"] = round(RSI70d, 2)
        indicatorsDF.loc[stock, "MACD"] = round(macd, 2)
        indicatorsDF.loc[stock, "signal"] = round(signal, 2)

    #background gradient para cada columns
    columnsExcluded = ["Stock"]
    columnsIncluded = indicatorsDF.columns.difference(columnsExcluded)
    styledIndicatorsDF = style_dataframe(indicatorsDF, columnsIncluded)

    indicators_file_path = os.path.join("technicalIndicatorsExcel", "etfIndicators.xlsx")
    styledIndicatorsDF.to_excel(indicators_file_path, index=True)


if __name__ == "__main__":
    main()


