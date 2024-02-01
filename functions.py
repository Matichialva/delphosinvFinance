import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

def cleaning_dataframe(df):
    df.sort_index(ascending=True, inplace=True)
    df.index.name = "Date"
    df.ffill(inplace=True)
    df.dropna(how="all", inplace=True)

def find_closest_date(current_date, df):
    closest_date = None
    min_difference = float('inf')

    for date in df.index:
        difference = abs((date - current_date).total_seconds())
        if difference < min_difference:
            min_difference = difference
            closest_date = date

    return closest_date
