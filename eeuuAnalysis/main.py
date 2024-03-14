import yfinance as yf
import pandas as pd
import numpy as np
from eeuuFinance import functions_etfReturns

def fetch_ticker_data(ticker, period):
    ticker_data = yf.download(ticker, period=period, auto_adjust=True) #adjust by dividends/stocksplits
    return ticker_data

def cleaning_dataframe(df):
    '''clean the dataframe'''
    df.sort_index(ascending=True, inplace=True) #lo dejo sorteado con la última fecha abajo.
    df.index.name = "Date" #index column llamada "Date"
    df.ffill(inplace=True) #relleno los vacios con el valor del de arriba
    df.dropna(how="all", inplace=True) #si hay filas completamente vacias, funalas
    df.index = df.index.strftime("%Y-%m-%d")
    df.index = pd.to_datetime(df.index)

    return df

def calculate_rsi(df, amount, period, price_column, stock):
    df[f'RSI{period}{amount}'] = np.nan

    for date in df.index:
        current_day = df.index[-1].day_name()[:3]  # nombre de dia de semana, primeras 3 letras

        # resample weekly and take the last value, so it only appears the price of the last day of each particular week.
        weekly_returns = df[price_column][:date].resample('W-' + current_day, closed='right').last()
        delta = weekly_returns.diff()

        up = delta.copy()
        up[up < 0] = 0
        up = pd.Series.ewm(up, alpha=1 / amount).mean()

        down = delta.copy()
        down[down > 0] = 0
        down *= -1
        down = pd.Series.ewm(down, alpha=1 / amount).mean()

        rsi_values = np.where(up == 0, 0, np.where(down == 0, 100, 100 - (100 / (1 + up / down))))

        # en la última fecha, guardo el último rsi de la tabla de valores
        df.loc[date, f'RSI{period}{amount}'] = rsi_values[-1]

    return df

def calculate_current_over_media(df, ticker, rounds, price_column):

    df[f'$/{rounds}M'] = np.nan

    for date in df.index:
        current_price = df.loc[date, price_column]
        media200 = find_media_rounds(df[:date], price_column, rounds)

        df.loc[date, f'$/{rounds}M'] = current_price/media200

    return df

def find_media_rounds(df, price_column, rounds):
    last_values = df[price_column][-rounds:]
    mean_last_values = last_values.mean()
    return mean_last_values

def main():
    tickers = ['AAPL', 'IBM', 'AMZN']

    #column names
    price_200_media_column = "$/200media"
    desvio_column = "desvio ($/200media)"
    rsi_column = "RSI14W"

    #armo dataframe
    df = pd.DataFrame(index=tickers, columns=[price_200_media_column, desvio_column, rsi_column])
    df.index.name = "Ticker"

    #para cada ticker
    for ticker in tickers:
        ticker_data = fetch_ticker_data(ticker, '10y')
        ticker_data = cleaning_dataframe(ticker_data)

        #parameters
        rounds = 200
        rsi_amount = 14
        rsi_period = 'weekly'
        price_column = 'Close'

        ticker_data = calculate_rsi(ticker_data, rsi_amount, rsi_period, price_column, ticker) #agrego columna con rsi de 14 semanas al momento
        ticker_data = calculate_current_over_media(ticker_data, ticker, rounds, price_column) #columna del ratio al momento

        #estandarizo ratio sobre serie histórica
        mean = ticker_data[f'$/{rounds}M'].mean()
        std = ticker_data[f'$/{rounds}M'].std()
        current_price = ticker_data.loc[ticker_data.index[-1], price_column]
        ratio = ticker_data[f'$/{rounds}M'].iloc[-1]
        standarized = (ratio - mean) / std

        #add to dataframe
        df.loc[ticker, price_200_media_column] = ticker_data[f'$/{rounds}M'].iloc[-1]
        df.loc[ticker, desvio_column] = ticker_data[f'RSI{rsi_period}{rsi_amount}'].iloc[-1]
        df.loc[ticker, rsi_column] = standarized

    df.to_excel('eeuuAnalysis.xlsx')



if __name__ == '__main__':
    main()