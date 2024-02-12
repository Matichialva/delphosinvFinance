import yfinance as yf
import pandas as pd
import numpy as np
import os
from datetime import datetime
from functions_etfReturns import *
from functions_factors import *

def main():
    # dataframe with balance sheet data
    balance_file_path = os.path.join("technicalFactorsExcel", "sp500balanceSheet.xlsx")
    balanceDF = pd.read_excel(balance_file_path, sheet_name="Hoja1", index_col="Ticker")

    # list of tickers
    sp500tickers = balanceDF.index.tolist()

    #create pricesDF, fetch stock prices and add it to pricesDF. Save it in excel file.
    pricesDF = fetch_stock_prices(sp500tickers)
    prices_file_path = os.path.join("technicalFactorsExcel", "sp500Prices.xlsx")
    pricesDF.to_excel(prices_file_path, index=True)  # lo paso a un excelprint(pricesDF)
    pricesDF = pd.read_excel(prices_file_path, index_col="Date")

    #create percentageDF and save the percentage dataframe
    percentageDF = calculate_percentage_dataframe(sp500tickers, pricesDF)
    returns_file_path = os.path.join("technicalFactorsExcel", "sp500Returns.xlsx")
    percentageDF.to_excel(returns_file_path, index=True)
    percentageDF = pd.read_excel(returns_file_path, index_col="Stock")

    #create and save factors dataframe
    factorsDF = calculate_factors_dataframe(sp500tickers, pricesDF, percentageDF, balanceDF)
    factors_file_path = os.path.join("technicalFactorsExcel", "sp500Factors.xlsx")
    factorsDF.to_excel(factors_file_path, index=True)
    factorsDF = pd.read_excel(factors_file_path, index_col="Ticker")

    topDownFactorsDF = calculate_top_down_factors(factorsDF, pricesDF, percentageDF)
    topDownFactors_file_path = os.path.join("technicalFactorsExcel", "sp500topDownFactors.xlsx")
    topDownFactorsDF = style_dataframe(topDownFactorsDF, ["1D", "1W", "1M", "3M", "6M", "YTD"])
    topDownFactorsDF.to_excel(topDownFactors_file_path, index=True, options={'autosize':True})


if __name__ == "__main__":
    main()