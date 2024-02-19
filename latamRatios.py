import os
import yfinance as yf
import pandas as pd
import numpy as np
from functions_etfReturns import *
from datetime import datetime
from functions_latamRatios import *

def main():

    #create pricesDF
    '''pricesDF = pd.DataFrame(index=pd.date_range(start=datetime(1800, 1, 1), end=datetime.today().replace(hour=0, minute=0, second=0, microsecond=0), freq="B"))  # freq B -> business days
    pricesDF = add_data_dataframe(stocks, pricesDF, "max")  # lleno el df con data de cada stock
    pricesDF = cleaning_dataframe(pricesDF)  # función que limpia datos
    pricesDF.to_excel(os.path.join("latamReturns&Ratios", "latamPrices.xlsx"), index=True)  # lo paso a un excel'''

    #read pricesDF to avoid running it again.
    prices_file_path = os.path.join("latamReturns&Ratios", "latamPrices.xlsx")
    pricesDF = pd.read_excel(prices_file_path, index_col="Date", engine="openpyxl")

    #read latamTickers
    latam_files_path = os.path.join("latamReturns&Ratios", "latamTickers.xlsx")
    latamTickers = pd.read_excel(latam_files_path, "openpyxl")

    #lista de tickers
    tickers = latamTickers['TICKER'].tolist()


    #diccionario pais-ticker
    country_ticker_dict = create_country_tickers_dict(latamTickers)
    # DF con ratios y cotizaciones en el último año
    latam_ratios_prices = create_ratios_dataframe_every_combination(country_ticker_dict, pricesDF)
    latam_ratios_prices.to_excel(os.path.join("latamReturns&Ratios", "latamRatiosPrices.xlsx"))
    #lista de ratios
    country_ratios = latam_ratios_prices.columns.tolist()
    latam_countries_ratios = create_ratios_desvios(latam_ratios_prices, country_ratios)
    latam_countries_ratios = elimina_filas_fuera_limite(latam_countries_ratios, "Desvio1Y", -2, 2)
    latam_countries_ratios = filter_by_country_and_appearances_combinations(latam_countries_ratios, country_ticker_dict, {'Brazil': 5, 'Argentina': 3, 'Mexico': 3})
    latam_countries_ratios = style_by_ticker(latam_countries_ratios)
    latam_countries_ratios.to_excel(os.path.join("latamReturns&Ratios", "latamCountriesRatios.xlsx"), engine='openpyxl', index=True)

    #diccionario industria-ticker
    industry_ticker_dict = create_industry_tickers_dict(latamTickers)
    #df con ratios y cotizaciones en el último año
    industry_ratios_prices = create_ratios_dataframe_every_combination(industry_ticker_dict, pricesDF)
    industry_ratios_prices.to_excel(os.path.join("latamReturns&Ratios", "industryRatiosPrices.xlsx"))
    #lista de ratios
    industry_ratios = industry_ratios_prices.columns.tolist()
    latam_industry_ratios = create_ratios_desvios(industry_ratios_prices, industry_ratios)
    latam_industry_ratios = elimina_filas_fuera_limite(latam_industry_ratios, "Desvio1Y", -2, 2)

    industry_tickers = pd.DataFrame(latam_industry_ratios, index=latam_industry_ratios.index)
    industry_tickers['Ticker1'], industry_tickers['Ticker2'] = industry_tickers.index.str.split('/').str
    latam_industry_ratios = industry_tickers[['Ticker1', 'Desvio1Y']]
    latam_industry_ratios = style_by_ticker(latam_industry_ratios)
    latam_industry_ratios.to_excel(os.path.join("latamReturns&Ratios", "latamIndustryRatios.xlsx"), engine='openpyxl', index=True)



if __name__ == "__main__":
    main()