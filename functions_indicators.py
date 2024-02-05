import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from datetime import datetime, timedelta
from functions_dataframe import *


def find_media_rounds(df, stock, rounds):
    last_values = df[stock][-rounds:]
    mean_last_values = last_values.mean()
    return mean_last_values

def min_price(df, stock, weeks):
    df.index= pd.to_datetime(df.index)
    #set range of days
    end_date = df.index[-1]
    start_date = end_date - timedelta(weeks=weeks)
    start_date = find_closest_date(start_date, df) #look for closest if start day doesn't exist in df

    df_period = df.loc[start_date:end_date]
    min_last_values = df_period[stock].min()

    return min_last_values

def max_price(df, stock, weeks):
    df.index= pd.to_datetime(df.index)

    # set range of days
    end_date = df.index[-1]
    start_date = end_date - timedelta(weeks=weeks)
    start_date = find_closest_date(start_date, df)  # look for closest if start day doesn't exist in df

    df_period = df.loc[start_date:end_date]

    max_last_values = df_period[stock].max()
    return max_last_values

def calculate_rsi(df, stock, days):
    #stores in pd series, date:delta. variación porcentual diaria en comparación a ayer
    df.index = pd.to_datetime(df.index)
    # set range of days
    end_date = df.index[-1]
    start_date = end_date - timedelta(days=days)
    start_date = find_closest_date(start_date, df)  # look for closest if start day doesn't exist in df

    df_period = df.loc[start_date:end_date]

    delta = df_period[stock].diff()

    #voy guardando en una serie todas las +- diarias.
    ganancias = delta.where(delta > 0, 0)
    perdidas = (-1) * delta.where(delta <= 0, 0)

    #obtengo la media de los últimos x días deseados.
    ganancia_media = ganancias.sum()
    perdida_media = perdidas.sum()

    #ganancia_media = ganancias.ewm(span=days, min_periods=1, adjust=False).mean().iloc[-1]
    #perdida_media = perdidas.ewm(span=days, min_periods=1, adjust=False).mean().iloc[-1]

    #if pd.isna(perdida_media) or pd.isna(ganancia_media):
    #    return 50

    if (perdida_media == 0):
        return 100
    elif (ganancia_media == 0):
        return 0

    rs = ganancia_media / perdida_media

    #calculo rsi.
    rsi = 100 - (100 / (1 + rs))
    return rsi
def calculate_rsi_weeks(df, stock, weeks):
    #stores in pd series, date:delta. variación porcentual diaria en comparación a ayer
    df.index = pd.to_datetime(df.index)
    # set range of days
    end_date = df.index[-1]
    start_date = end_date - timedelta(weeks=weeks)
    start_date = find_closest_date(start_date, df)  # look for closest if start day doesn't exist in df

    df_period = df.loc[start_date:end_date]

    delta = df_period[stock].diff()

    #voy guardando en una serie todas las +- diarias.
    ganancias = delta.where(delta > 0, 0)
    perdidas = (-1) * delta.where(delta <= 0, 0)

    #obtengo la media de los últimos x días deseados.
    ganancia_media = ganancias.sum()
    perdida_media = perdidas.sum()

    #ganancia_media = ganancias.ewm(span=days, min_periods=1, adjust=False).mean().iloc[-1]
    #perdida_media = perdidas.ewm(span=days, min_periods=1, adjust=False).mean().iloc[-1]

    #if pd.isna(perdida_media) or pd.isna(ganancia_media):
    #    return 50

    if (perdida_media == 0):
        return 100
    elif (ganancia_media == 0):
        return 0

    rs = ganancia_media / perdida_media

    #calculo rsi.
    rsi = 100 - (100 / (1 + rs))
    return rsi
def rsi_tradingview(df: pd.DataFrame, stock, period_days):
    """
    :param df:
    :param stock:
    :param period_days:
    :return: RSI
    """

    delta = df[stock].diff()

    up = delta.copy()
    up[up < 0] = 0
    up = pd.Series.ewm(up, alpha=1/period_days).mean()

    down = delta.copy()
    down[down > 0] = 0
    down *= -1
    down = pd.Series.ewm(down, alpha=1/period_days).mean()

    rsi = np.where(up == 0, 0, np.where(down == 0, 100, 100 - (100 / (1 + up / down))))

    return rsi[-1]

def calculate_macd(df: pd.DataFrame, stock):
    '''given df with stock info and the stock, calculate its macd'''
    ema12 = df[stock].ewm(span=12, adjust=False).mean() #adjust False -> exponentially weighted function recursive
    ema26 = df[stock].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26 #macd series

    return macd.iloc[-1]


