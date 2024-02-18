import os
import yfinance as yf
import pandas as pd
import numpy as np
from functions_etfReturns import *
from datetime import datetime
from itertools import permutations
import random

def create_country_tickers_dict(tickers):
    """given a dataframe with tickers associated to country and gics."""
    country_tickers_dict = {}

    for index, row in tickers.iterrows():
        ticker = row['TICKER']
        country = row['Country']

        if country not in country_tickers_dict:
            country_tickers_dict[country] = [ticker]
        else:
            country_tickers_dict[country].append(ticker)

    return country_tickers_dict

def create_ratios_dataframe(dictionary, pricesDF):
    """given a dictionary with tickers associated to country and
    a dataframe with historical prices of the tickers."""

    #paso pricesDF index a dataframe
    pricesDF.index = pd.to_datetime(pricesDF.index)
    pricesDF = pricesDF.iloc[-252:] #agarro últimos 252 datos

    # creo dataframe a rellenar
    ratios_dataframe = pd.DataFrame(index=pricesDF.index)

    for country, tickers in dictionary.items():

        for i in range(len(tickers)):
            for j in range(i+1, len(tickers)):
                #nombro 2 tickers a comparar
                ticker1 = tickers[i]
                ticker2 = tickers[j]

                #agarro 2 series de precios del último año
                prices_ticker1 = pricesDF[ticker1]
                prices_ticker2 = pricesDF[ticker2]

                #calculo ratio
                ratio = prices_ticker1 / prices_ticker2

                #creo columna para el ratio
                nombre_columna = f"{ticker1}/{ticker2}"
                ratios_dataframe[nombre_columna] = ratio

    return ratios_dataframe

def create_ratios_dataframe_every_combination(dictionary, pricesDF):
    """given a dictionary with tickers associated to country and
    a dataframe with historical prices of the tickers."""

    #paso pricesDF index a dataframe
    pricesDF.index = pd.to_datetime(pricesDF.index)
    pricesDF = pricesDF.iloc[-252:] #agarro últimos 252 datos

    # creo dataframe a rellenar
    ratios_dataframe = pd.DataFrame(index=pricesDF.index)

    for country, tickers in dictionary.items():
        ticker_combinations = permutations(tickers, 2)

        for ticker1, ticker2 in ticker_combinations:

            #agarro 2 series de precios del último año
            prices_ticker1 = pricesDF[ticker1]
            prices_ticker2 = pricesDF[ticker2]

            #calculo ratio
            ratio = prices_ticker1 / prices_ticker2

            #creo columna para el ratio
            nombre_columna = f"{ticker1}/{ticker2}"
            ratios_dataframe[nombre_columna] = ratio

    return ratios_dataframe

def create_ratios_desvios(ratios_date_dataframe, ratios):
    ratios_desvio_dataframe = pd.DataFrame(index=ratios, columns=["Desvio1Y"])

    for ratio in ratios:
        ratio_data = ratios_date_dataframe[ratio].iloc[:-1]
        current_data = ratios_date_dataframe[ratio].iloc[-1]

        mean = ratio_data.mean()
        std = ratio_data.std()

        zValue = (current_data - mean) / std

        ratios_desvio_dataframe.loc[ratio, "Desvio1Y"] = round(zValue, 2)

    return ratios_desvio_dataframe

def elimina_filas_fuera_limite(dataframe, nombre_columna, limite_inferior, limite_superior):
    for index, row in dataframe.iterrows():
        value = row[nombre_columna]
        if limite_inferior < value < limite_superior:
            dataframe.drop(index, inplace=True)
    return dataframe

def filter_by_country_and_appearances(dataframe, country_ticker_dict: dict, min_count_by_country: dict):
    '''filter dataframe including only the rows that have ticker with the min_count'''

    #df -> columns: ticker1, ticker2
    all_tickers = pd.DataFrame(dataframe, index=dataframe.index)
    all_tickers['Ticker1'], all_tickers['Ticker2'] = all_tickers.index.str.split('/').str
    all_tickers = all_tickers[['Ticker1', 'Ticker2']] #dejo columnas q me importan
    all_tickers = all_tickers.reset_index(drop=True) #reseteo el indice con números

    ticker_list = []
    for index, row in all_tickers.iterrows():
        ticker_list.extend([row['Ticker1'], row['Ticker2']]) #.extend used to add many elements to a list
    ticker_df = pd.DataFrame(ticker_list, columns=['Tickers']) #lista a dataframe

    #add count column
    ticker_df = ticker_df.groupby('Tickers').size().reset_index(name='count')

    #add country column. .map -> dictionary ticker:country
    ticker_df['Country'] = ticker_df['Tickers'].map({ticker: country for country, tickers in country_ticker_dict.items() for ticker in tickers})

    #filter based on min_count_by_country
    ticker_df = ticker_df[ticker_df['count'] >= ticker_df['Country'].map(min_count_by_country).fillna(0)] #if NAN in map, fillna(0)

    filtered_dataframe = pd.DataFrame(columns=dataframe.columns)
    for index, row in dataframe.iterrows():
        if any(ticker in index for ticker in ticker_df['Tickers']):
            filtered_dataframe = pd.concat([filtered_dataframe, pd.DataFrame([row])])

    return filtered_dataframe

def filter_by_country_and_appearances_combinations(dataframe, country_ticker_dict: dict, min_count_by_country: dict):
    '''filter dataframe including only the rows that have ticker with the min_count'''

    #df -> columns: ticker1
    all_tickers = pd.DataFrame(dataframe, index=dataframe.index)
    all_tickers['Ticker1'], all_tickers['Ticker2'] = all_tickers.index.str.split('/').str

    #me quedo con todos los tickers que están arriba en el ratio
    up_tickers = all_tickers['Ticker1']
    up_tickers = up_tickers.reset_index(drop=True) #reseteo el indice con números

    #lista de los up_tickers, y desp paso a dataframe los tickers
    ticker_list = []
    for ticker in up_tickers:
        ticker_list.append(ticker)
    ticker_df = pd.DataFrame(ticker_list, columns=['Tickers']) #lista a dataframe

    #add count column
    ticker_df = ticker_df.groupby('Tickers').size().reset_index(name='count')

    #add country column. .map -> dictionary ticker:country
    ticker_df['Country'] = ticker_df['Tickers'].map({ticker: country for country, tickers in country_ticker_dict.items() for ticker in tickers})

    #filter based on min_count_by_country -> saco los q aparecen poco. solo quedan en ticker_df los q quiero.
    ticker_df = ticker_df[ticker_df['count'] >= ticker_df['Country'].map(min_count_by_country).fillna(0)] #if NAN in map, fillna(0)

    #filtro los ratios, solo dejo los q están en ticker_df
    filtered_dataframe = pd.DataFrame(columns=dataframe.columns)
    for index, row in dataframe.iterrows():
        ticker_found = False
        for ticker in ticker_df['Tickers']:
            if ticker in row['Ticker1']:
                ticker_found = True
                break
        if ticker_found:
            filtered_dataframe = pd.concat([filtered_dataframe, pd.DataFrame([row])])

    #solo quiero ver el desvio de los ratios q quedaron filtrados.
    filtered_dataframe = filtered_dataframe[['Ticker1', "Desvio1Y"]]

    return filtered_dataframe

def style_by_ticker(df):
    def apply_ticker_color(value):
        ticker = value.split('/')[0]
        return f'background-color: {color_map.get(ticker, "FFFFFF")}'

    # Extract unique tickers and assign random colors
    unique_tickers = df.index.str.split('/').str[0].unique().tolist()
    color_map = {ticker: f'#{random.randint(0, 0xFFFFFF):06X}' for ticker in unique_tickers}

    # Apply styling to the DataFrame
    styled_df = df.style.applymap(apply_ticker_color, subset=['Ticker1'])
    return styled_df

def create_industry_tickers_dict(tickers):
    """given a dataframe with tickers associated to country and gics."""
    industry_tickers_dict = {}

    for index, row in tickers.iterrows():
        ticker = row['TICKER']
        country = row['GICS 1']

        if country not in industry_tickers_dict:
            industry_tickers_dict[country] = [ticker]
        else:
            industry_tickers_dict[country].append(ticker)

    return industry_tickers_dict


