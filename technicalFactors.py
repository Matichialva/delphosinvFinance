import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from functions_etfReturns import *
from functions_factors import *

def main():
    # dataframe with balance sheet data
    balanceDF = pd.read_excel("sp500balanceSheet.xlsx", sheet_name="Hoja1", index_col="Ticker")

    # list of tickers
    sp500tickers = balanceDF.index.tolist()

    #create pricesDF, fetch stock prices and add it to pricesDF. Save it in excel file.
    pricesDF = fetch_stock_prices(sp500tickers)
    pricesDF.to_excel("sp500stocks_test.xlsx", index=True)  # lo paso a un excelprint(pricesDF)
    pricesDF = pd.read_excel("sp500stocks_test.xlsx", index_col="Date")

    #create percentageDF and save the percentage dataframe
    percentageDF = calculate_percentage_dataframe(sp500tickers, pricesDF)
    percentageDF.to_excel("sp500PercentageDataframe.xlsx", index=True)
    percentageDF = pd.read_excel("sp500PercentageDataframe.xlsx", index_col="Stock")

    #create and save factors dataframe
    factorsDF = calculate_factors_dataframe(sp500tickers, pricesDF, percentageDF, balanceDF)
    factorsDF.to_excel("sp500factorsDF.xlsx", index=True)
    factorsDF = pd.read_excel("sp500factorsDF.xlsx", index_col="Ticker")

    topDownFactorsDF = calculate_top_down_factors(factorsDF, pricesDF, percentageDF)
    topDownFactorsDF.to_excel("sp500topDownFactorsDF.xlsx", index=True)

if __name__ == "__main__":
    main()