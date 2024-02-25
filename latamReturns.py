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
    latamTickers = pd.read_excel(latam_files_path, engine="openpyxl")

    stocks = latamTickers['TICKER'].tolist() #lista de tickers

    #pricesDF = pd.DataFrame(index=pd.date_range(start=datetime(1800, 1, 1), end=datetime.today().replace(hour=0, minute=0, second=0, microsecond=0), freq="B")) #freq B -> business days
    #pricesDF = add_data_dataframe(stocks, pricesDF, "max") #lleno el df con data de cada stock
    #pricesDF = cleaning_dataframe(pricesDF) #función que limpia datos

    prices_file_path = os.path.join("latamReturns&Ratios", "latamPrices.xlsx")
    #pricesDF.to_excel(prices_file_path, index=True) #lo paso a un excel
    pricesDF = pd.read_excel(prices_file_path, index_col="Date", engine="openpyxl")

    #multiindex created
    multi_index_df = latamTickers.set_index(['GICS 1', 'GICS 2', 'Country', 'TICKER']) #seteo multiindex
    multi_index_df.sort_index(level=['GICS 1', 'GICS 2', 'Country', 'TICKER'],inplace=True) #sorteo en el orden q me interesa, en base a cual no quiero q se repita
    #multi_index_df = multi_index_df.reorder_levels(['GICS 1', 'GICS 2', 'Country', 'TICKER'])
    multi_index_df.drop(columns='BBG', inplace=True)
    multi_index_df.to_excel("multiindex.xlsx", index=True)

    #percentageDF created
    percentageDF = pd.DataFrame(index = pricesDF.columns, columns=["1D", "1Ddesvios", "1W", "1Wdesvios", "1M", "1Mdesvios", "3M", "MTD", "QTD", "YTD", "6M", "1Y", "2Y", "3Y", "2022/12/9"]) #quiero las stocks a la izquierda
    percentageDF.index.name = "TICKER"
    percentageDF = add_price_changes(pricesDF, percentageDF) #add price changes

    result_df = pd.merge(multi_index_df, percentageDF, left_on=['TICKER'], right_index=True, how='left')

    #aplico gradiente colorido
    columnsExcluded = ["Stock"]
    columnsIncluded = percentageDF.columns.difference(columnsExcluded)

    #harcodeado para q quede el cero como midpoint.
    stylePercentageDF = (result_df.style
                         .background_gradient(subset=["1D"], cmap='RdYlGn', axis=0, vmin=-3, vmax=3)
                         .background_gradient(subset=["1D", "1W", "1M"], cmap='RdYlGn', axis=0, vmin=-7, vmax=7)
                         .background_gradient(subset=["1Ddesvios", "1Wdesvios", "1Mdesvios"], cmap='RdYlGn', axis=0,
                                              vmin=-3, vmax=3)
                         .background_gradient(subset=["3M", "MTD", "QTD", "YTD"], cmap='RdYlGn', axis=0, vmin=-15,
                                              vmax=15)
                         .background_gradient(subset=["6M", "1Y", "2Y", "3Y", "2022/12/9"], cmap='RdYlGn', axis=0,
                                              vmin=-50, vmax=50)
                         )
    returns_file_path = os.path.join("latamReturns&Ratios", "latamReturns.xlsx")
    stylePercentageDF.to_excel(returns_file_path, index=True, engine='openpyxl') #lo paso a un excel

if __name__ == "__main__":
    main()