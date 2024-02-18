import os
import yfinance as yf
import pandas as pd
import numpy as np
from functions_etfReturns import *
from datetime import datetime

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials

def main():
    latam_files_path = os.path.join("latamReturns&Ratios", "latamTickers.xlsx")
    latamTickers = pd.read_excel(latam_files_path)

    stocks = latamTickers['TICKER'].tolist() #lista de tickers

    pricesDF = pd.DataFrame(index=pd.date_range(start=datetime(1800, 1, 1), end=datetime.today().replace(hour=0, minute=0, second=0, microsecond=0), freq="B")) #freq B -> business days
    pricesDF = add_data_dataframe(stocks, pricesDF, "max") #lleno el df con data de cada stock
    pricesDF = cleaning_dataframe(pricesDF) #función que limpia datos

    prices_file_path = os.path.join("latamReturns&Ratios", "latamPrices.xlsx")
    pricesDF.to_excel(prices_file_path, index=True) #lo paso a un excel
    pricesDF = pd.read_excel(prices_file_path, index_col="Date")

    percentageDF = pd.DataFrame(index = pricesDF.columns, columns=["1D", "1Ddesvios", "1W", "1Wdesvios", "1M", "1Mdesvios", "3M", "MTD", "QTD", "YTD", "6M", "1Y", "2Y", "3Y", "2022/12/9", "Sector"]) #quiero las stocks a la izquierda
    percentageDF.index.name = "Stock"
    percentageDF = add_price_changes(pricesDF, percentageDF) #add price changes

    #aplico gradiente colorido
    columnsExcluded = ["Stock"]
    columnsIncluded = percentageDF.columns.difference(columnsExcluded)
    stylePercentageDF = style_dataframe(percentageDF, columnsIncluded)

    returns_file_path = os.path.join("latamReturns&Ratios", "latamReturns.xlsx")
    stylePercentageDF.to_excel(returns_file_path, index=True) #lo paso a un excel

if __name__ == "__main__":
    main()