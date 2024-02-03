import yfinance as yf
import pandas as pd
import numpy as np
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


