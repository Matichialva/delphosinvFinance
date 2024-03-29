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
    latamTickers = pd.read_excel(latam_files_path, engine="openpyxl")

    #lista de tickers
    tickers = latamTickers['TICKER'].tolist()

###########################################################################################################################
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

    # multiindex created
    multi_index_df = latamTickers.set_index(['Country', 'TICKER'])  # seteo multiindex
    multi_index_df.sort_index(level=['Country', 'TICKER'],
                              inplace=True)  # sorteo en el orden q me interesa, en base a cual no quiero q se repita
    multi_index_df.drop(columns=['BBG', 'GICS 1', 'GICS 2'], inplace=True)


    latam_countries_ratios.reset_index(inplace=True)
    latam_countries_ratios.columns = ['ratios', 'ticker', 'desvio']
    latam_countries_ratios.set_index('ticker', inplace=True)

    result_df = pd.merge(multi_index_df, latam_countries_ratios, left_on=['TICKER'], right_index = True, how='inner')
    result_df.reset_index(inplace=True)
    result_df = style_by_ticker(result_df, 'TICKER')
    result_df = result_df.background_gradient(cmap='RdYlGn', subset=['desvio'], vmin=-4, vmax=4)

    last_date= pricesDF.index.strftime("%Y-%m-%d")[-1]
    result_df.to_excel(os.path.join("latamReturns&Ratios", f"latamCountriesRatios-{last_date}.xlsx"), engine='openpyxl', index=False)
#########################################################################################################################3

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

    #latam_industry_ratios.drop(columns=['ratios', 'Ticker2'])
    latam_industry_ratios.reset_index(inplace=True)
    latam_industry_ratios.columns = ['ratios', 'ticker', 'desvio']
    latam_industry_ratios.set_index('ticker', inplace=True)

    # multiindex created
    multi_index_df2 = latamTickers.set_index(['GICS 1',  'TICKER'])  # seteo multiindex
    multi_index_df2.sort_index(level=['GICS 1', 'TICKER'],
                              inplace=True)  # sorteo en el orden q me interesa, en base a cual no quiero q se repita
    multi_index_df2.drop(columns=['BBG', 'GICS 2', 'Country'], inplace=True)

    result_df2 = pd.merge(multi_index_df2, latam_industry_ratios, left_on=['TICKER'], right_index = True, how='inner')
    #result_df2['desvio'] = result_df2['desvio'].map("{:%}".format)

    result_df2.reset_index(inplace=True)
    result_df2 = style_by_ticker(result_df2, 'TICKER')
    styled = result_df2.background_gradient(cmap='RdYlGn', subset=['desvio'], vmin=-4, vmax=4)

    styled.to_excel(os.path.join("latamReturns&Ratios", f"latamIndustryRatios-{last_date}.xlsx"), engine='openpyxl', index=False)




if __name__ == "__main__":
    main()