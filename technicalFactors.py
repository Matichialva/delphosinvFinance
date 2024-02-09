import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from functions_dataframe import *
from functions_factors import *

#dataframe with balance sheet data
balanceDF = pd.read_excel("sp500balanceSheet.xlsx",sheet_name="Hoja1", index_col="Ticker")

#list of tickers
sp500tickers = balanceDF.index.tolist()

'''
#ARMO PRICESDF
sp500tickers.insert(0, "^SPX")
#dataframe con precios de tickers del sp500
hoy = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
pricesDF = pd.DataFrame(index=pd.date_range(start=datetime(2022, 1, 1), end=hoy, freq="B")) #freq B -> business days

pricesDF = add_data_dataframe(sp500tickers, pricesDF, "5y") #lleno el df con data de cada stock
cleaning_dataframe(pricesDF) #función que limpia datos
pricesDF.to_excel("sp500stocks_test.xlsx", index=True) #lo paso a un excelprint(pricesDF)
sp500tickers.remove('^SPX')
'''

pricesDF = pd.read_excel("sp500stocks_test.xlsx",index_col = "Date")

'''
#ARMO PERCENTAGEDF
#dataframe con retornos de empresas del sp500 (en la lista)
percentageDF = pd.DataFrame(index = sp500tickers, columns=["1D", "1W", "1M", "3M", "6M", "YTD"])
percentageDF.index.name = "Stock"

for stock in pricesDF.columns:  # para cada stock
    if stock == '^SPX':
        continue
    pricesDF.index = pd.to_datetime(pricesDF.index)
    currentDate = pricesDF.index[-1]
    current = pricesDF[stock].loc[currentDate]  #last price in the stock column

    period_dict_days = {"1D": 1, "1W": 7, "1M": 28, "3M": 91}
    for periodKey, periodValue in period_dict_days.items():  # para cada período
        pastDate = find_previous_closest_date(currentDate - pd.DateOffset(days=periodValue), pricesDF)
        past = pricesDF[stock].loc[pastDate]  # calculo valor en ese momento
        priceChange = (current - past) / past * 100  # calculo el porcentaje de cambio de precio
        if priceChange == 0:  # caso donde la bolsa todavia no operó hoy, comparo ayer con anteayer
            pastDate = find_previous_closest_date(currentDate - pd.DateOffset(days=2), pricesDF)
            past = pricesDF[stock].loc[pastDate]  # calculo valor en ese momento
            priceChange = (current - past) / past * 100  # calculo el porcentaje de cambio de precio
        percentageDF.loc[stock, periodKey] = round(priceChange, 1)  # agrego al dataframe

    period_dict_months = {"6M": 6}
    for periodKey, periodValue in period_dict_months.items():  # para cada período
        pastDate = find_previous_closest_date(currentDate - pd.DateOffset(months=periodValue), pricesDF)
        past = pricesDF[stock].loc[pastDate]  # calculo valor en ese momento
        priceChange = (current - past) / past * 100  # calculo el porcentaje de cambio de precio
        percentageDF.loc[stock, periodKey] = round(priceChange, 1)  # agrego al dataframe

    # grab the day before the first day of the actual year
    ytdDate = datetime(currentDate.year - 1, 12, 31)
    ytdValue = pricesDF[stock].loc[find_previous_closest_date(ytdDate, pricesDF)]
    ytdPriceChange = (current - ytdValue) / ytdValue * 100
    percentageDF.loc[stock, "YTD"] = round(ytdPriceChange, 1)

percentageDF.to_excel("sp500PercentageDataframe.xlsx", index=True)
'''

percentageDF = pd.read_excel("sp500PercentageDataframe.xlsx", index_col="Stock")

#################################armo factorsDF##########################################
factorsDF = pd.DataFrame(index=sp500tickers, columns=["DividendYield (%)", "netDebt/EV (%)", "marketCap (M)", "volatility20r (%)", "Momentum (1m vs 4m)", "Beta (3y)"])
factorsDF.index.name = "Ticker"
factorsDF = add_factors(factorsDF, pricesDF, percentageDF, balanceDF)

factorsDF.to_excel("sp500factorsDF.xlsx", index=True)
