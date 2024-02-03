import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

def add_data_dataframe(stocks, df):
    '''given a list of stocks and a dataframe, downloads the "Close" price
     of each stock everyday and concatenates it to the dataframe.'''
    for stock in stocks:
        stockDataframe = yf.download(stock, period="max")["Close"]  # columna de cotización de la stock
        stockDataframe.name = stock  # column name is the stock name
        df = pd.concat([df, stockDataframe], axis=1)  # mergeo data de cada stock al df
    return df

def cleaning_dataframe(df):
    '''clean the dataframe'''
    df.sort_index(ascending=True, inplace=True) #lo dejo sorteado con la última fecha abajo.
    df.index.name = "Date" #index column llamada "Date"
    df.ffill(inplace=True) #relleno los vacios con el valor del de arriba
    df.dropna(how="all", inplace=True) #si hay filas completamente vacias, funalas
    df.index = df.index.strftime("%Y-%m-%d")

def add_price_changes(df, percentageDF):
    '''given a dataframe with dates as index and columns for stocks, uses that information
    to compare each stock value to its previous values and adds the price change to percentageDF.'''

    for stock in df.columns:  # para cada stock
        currentDate = df.index[-1]
        current = df[stock].loc[currentDate]  # last price in the stock column

        period_dict_days = {"1D": 1, "5D": 5}
        for periodKey, periodValue in period_dict_days.items():  # para cada período
            pastDate = find_closest_date(currentDate - pd.DateOffset(days=periodValue), df)
            past = df[stock].loc[pastDate]  # calculo valor en ese momento
            priceChange = (current - past) / past * 100  # calculo el porcentaje de cambio de precio
            percentageDF.loc[stock, periodKey] = round(priceChange, 2)  # agrego al dataframe

        period_dict_months = {"1M": 1, "3M": 3, "6M": 6}
        for periodKey, periodValue in period_dict_months.items():  # para cada período
            pastDate = find_closest_date(currentDate - pd.DateOffset(months=periodValue), df)
            past = df[stock].loc[pastDate]  # calculo valor en ese momento
            priceChange = (current - past) / past * 100  # calculo el porcentaje de cambio de precio
            percentageDF.loc[stock, periodKey] = round(priceChange, 2)  # agrego al dataframe

        period_dict_years = {"1Y": 1, "2Y": 2, "5Y": 5, "10Y": 10}
        for periodKey, periodValue in period_dict_years.items():  # para cada período
            pastDate = find_closest_date(currentDate - pd.DateOffset(years=periodValue), df)
            past = df[stock].loc[pastDate]  # calculo valor en ese momento
            priceChange = (current - past) / past * 100  # calculo el porcentaje de cambio de precio
            percentageDF.loc[stock, periodKey] = round(priceChange, 2)  # agrego al dataframe

    return percentageDF

def add_sectors(sectorStockDict, percentageDF):
    for sector, stock in sectorStockDict.items():
        percentageDF.loc[stock, "Sector"] = sector
    return percentageDF

def style_dataframe(notStyledDF, columnsIncluded):
    '''applyies gradient to the dataframe and columns given'''
    stylePercentageDF = notStyledDF.style.background_gradient(subset=columnsIncluded, cmap='RdYlGn',
                                                               axis=0)  # applied by column not row
    return stylePercentageDF


def find_closest_date(current_date, df):
    closest_date = None
    min_difference = float('inf')

    for date in df.index:
        difference = abs((date - current_date).total_seconds())
        if difference < min_difference:
            min_difference = difference
            closest_date = date

    return closest_date
