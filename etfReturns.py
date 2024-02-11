import yfinance as yf
import pandas as pd
import numpy as np
from functions_etfReturns import *
from datetime import datetime

def main():
    stocks = ["UUP", "UDN", "CEW", "DBP", "GLD", "SLV", "PPLT", "DBE", "DBO", "UNG", "DBB", "CPER", "PALL", "DBA", "WEAT", "CANE", "CORN", "SOYB", "SPY", "EWC", "EWO", "EWK", "EDEN", "EFNL", "EWQ", "EWG", "GREK", "EIRL", "EWI", "EWN", "ENOR", "PGAL", "EWP", "EWD", "EWL", "EWU", "EIS", "EWA", "EWH", "EWJ", "ENZL", "EWS", "EWW", "EWZ", "ECH", "GXG", "EPU", "INDA", "MCHI", "CNYA", "EIDO", "EWY", "EWM", "EPHE", "EWT", "THD", "EPOL", "TUR", "EZA", "XLE", "OIH", "XOP", "XLU", "XLP", "FTXG", "XLY", "XHB", "XRT", "XLRE", "XTL", "XLI", "ITA", "XTN", "XLV", "XHE", "XHS", "BBH", "PPH", "XLK", "SMH", "XSW", "XLB", "XME", "GDX", "SIL", "SLX", "XLF", "KCE", "KBE", "KRE", "IAK", "DIA", "XLG", "IWB", "IWM", "IWC", "SPYG", "SPYD", "SPYV", "SDY", "VIG", "PFF", "QUAL", "MTUM", "ESGU", "SUSL", "ESML", "SPHB", "BTAL", "SPLV", "BNDD", "INFL", "EMB", "LEMB", "LQD", "LQDH", "HYG", "HYGH"]
    sectorStockDict = {
        "Coins" : ["UUP", "UDN", "CEW"],
        "Commodities" : ["DBP", "GLD", "SLV", "PPLT", "DBE", "DBO", "UNG", "DBB", "CPER", "PALL", "DBA", "WEAT", "CANE", "CORN", "SOYB"],
        "Equity DMs" : ["SPY", "EWC", "EWO", "EWK", "EDEN", "EFNL", "EWQ", "EWG", "GREK", "EIRL", "EWI", "EWN", "ENOR", "PGAL", "EWP", "EWD", "EWL", "EWU", "EIS", "EWA", "EWH", "EWJ", "ENZL", "EWS"],
        "Equity EMs" : ["EWW", "EWZ", "ECH", "GXG", "EPU", "INDA", "MCHI", "CNYA", "EIDO", "EWY", "EWM", "EPHE", "EWT", "THD", "EPOL", "TUR", "EZA"],
        "Equity EEUU industries" : ["XLE", "OIH", "XOP", "XLU", "XLP", "FTXG", "XLY", "XHB", "XRT", "XLRE", "XTL", "XLI", "ITA", "XTN", "XLV", "XHE", "XHS", "BBH", "PPH", "XLK", "SMH", "XSW", "XLB", "XME", "GDX", "SIL", "SLX", "XLF", "KCE", "KBE", "KRE", "IAK"],
        "Equity EEUU factores" : ["DIA", "XLG", "IWB", "IWM", "IWC", "SPYG", "SPYD", "SPYV", "SDY", "VIG", "PFF", "QUAL", "MTUM", "ESGU", "SUSL", "ESML", "SPHB", "BTAL", "SPLV"],
        "EEUU infla/defla" : ["BNDD", "INFL"],
        "ETF bonos" : ["EMB", "LEMB", "LQD", "LQDH", "HYG", "HYGH"],
    }

    #-----------------dataframe con precios diarios----------------------
    #DF vacío, índice = date, donde va desde 1800 hasta hoy.
    df = pd.DataFrame(index=pd.date_range(start=datetime(1800, 1, 1), end=datetime.today().replace(hour=0, minute=0, second=0, microsecond=0), freq="B")) #freq B -> business days
    df = add_data_dataframe(stocks, df, max) #lleno el df con data de cada stock
    df = cleaning_dataframe(df) #función que limpia datos

    df.to_excel("stocks_test.xlsx", index=True) #lo paso a un excel
    df = pd.read_excel("stocks_test.xlsx", index_col="Date")

    #-----------------dataframe con retornos----------------------
    #creo percentageDF
    percentageDF = pd.DataFrame(index = df.columns, columns=["1D", "1Ddesvios", "1W", "1Wdesvios", "1M", "1Mdesvios", "3M", "MTD", "QTD", "YTD", "6M", "1Y", "2Y", "3Y", "2022/12/9", "Sector"]) #quiero las stocks a la izquierda
    percentageDF.index.name = "Stock"

    percentageDF = add_sectors(sectorStockDict, percentageDF) #add stock's sectors
    percentageDF = add_price_changes(df, percentageDF) #add price changes

    #aplico gradiente colorido
    columnsExcluded = ["Stock", "Sector"]
    columnsIncluded = percentageDF.columns.difference(columnsExcluded)
    stylePercentageDF = style_dataframe(percentageDF, columnsIncluded)
    stylePercentageDF.to_excel("styledStocksPercentage.xlsx", index=True) #lo paso a un excel

if __name__ == "__main__":
    main()