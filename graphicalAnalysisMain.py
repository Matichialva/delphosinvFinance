import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import mplfinance as mpf
import talib
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime

def fetch_ticker_data(ticker, start_time):
    ticker_data = yf.download(ticker, start= start_time)
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

def calculate_mama_fama(data, fast=0.25, slow=0.05):
    mama, fama = talib.MAMA(data['Close'], fastlimit=fast, slowlimit=slow)
    return pd.Series(mama, index=data.index), pd.Series(fama, index=data.index)

def rsi_tradingview(df: pd.DataFrame, stock, period_days):
    """
    :param df:
    :param stock:
    :param period_days:
    :return: RSI
    """
    delta = df['Close'].diff()

    up = delta.copy()
    up[up < 0] = 0
    up = pd.Series.ewm(up, alpha=1/period_days).mean()

    down = delta.copy()
    down[down > 0] = 0
    down *= -1
    down = pd.Series.ewm(down, alpha=1/period_days).mean()

    rsi_values = np.where(up == 0, 0, np.where(down == 0, 100, 100 - (100 / (1 + up / down))))

    rsi_df = pd.DataFrame({'RSI': rsi_values}, index=df.index)
    return rsi_df #return date as index, and rsi value as another column.

###########
def calculate_volatility(df, lookback):
    returns = np.log(df['Close'] / df['Close'].shift(1))
    volatility = returns.rolling(window=lookback).std() * np.sqrt(252)
    #print("Volatility:", volatility)
    return volatility


def calculate_skewness(df, skew_length):
    true_range = df.apply(lambda row: max(row['High'] - row['Low'], abs(row['High'] - row['Close']), abs(row['Low'] - row['Close'])), axis=1)
    deviation_max = pd.Series(1., index=df.index)
    deviation_min = pd.Series(1., index=df.index)

    alpha = 2.0 / (1.0 + skew_length)

    for i in range(1, len(df)):
        deviation_max[i] = alpha * (true_range[i] if df['Close'][i] > df['Close'][i-1] else 0) + (1.0 - alpha) * deviation_max[i-1]
        deviation_min[i] = alpha * (true_range[i] if df['Close'][i] < df['Close'][i-1] else 0) + (1.0 - alpha) * deviation_min[i-1]

    skewness = deviation_max / deviation_min
    #print("Skewness:", skewness)
    return skewness

def calculate_kurtosis(series, lookback):
    avg = series.ewm(span=lookback).mean()
    stdv = series.rolling(window=lookback).std()
    kurtosis = ((series - avg).pow(4).ewm(span=lookback).mean()) / (lookback * stdv.pow(4)) - 3
    #print("Kurtosis:", kurtosis)
    return kurtosis

def cornish_fisher_quantile(q, skew, kurtosis):
    second_term = (q**2 - 1) / 6 * skew
    third_term = (q**3 - 3 * q) / 24 * kurtosis
    fourth_term = (2 * q**3 - 5 * q) / 36 * skew**2
    return q + second_term + third_term + fourth_term

def calculate_risk_ranges(df, lookback, skew_length, choiceMidPoint):
    #calculate 3 parameters to calculate the risk ranges
    volatility = calculate_volatility(df, lookback)
    skewness = calculate_skewness(df, skew_length)
    kurtosis_val = calculate_kurtosis(df['Close'], lookback)

    upskew = cornish_fisher_quantile(1.645, skewness, kurtosis_val)
    downskew = cornish_fisher_quantile(-1.645, skewness, kurtosis_val)

    if choiceMidPoint == 'Last':
        midpoint = df['Close']
    elif choiceMidPoint == 'YDAY':
        midpoint = df['Close'].shift(1)
    elif choiceMidPoint == 'H&L':
        midpoint = (df['High'] + df['Low']) / 2
    elif choiceMidPoint == 'Tight':
        midpoint = np.minimum(df['Low'], df['Close'].shift(1))

    rr_high = midpoint + upskew * volatility
    rr_low = midpoint + downskew * volatility

    #print("Risk Range High:", rr_high)
    #print("Risk Range Low:", rr_low)

    return rr_high, rr_low
##############

def plot_price_MA_volume(ticker_data, ticker, pdf_pages, start_date):

    #collect moving averages
    ticker_data['MA10'] = ticker_data['Close'].rolling(window=10).mean()
    ticker_data['MA20'] = ticker_data['Close'].rolling(window=20).mean()
    ticker_data['MA50'] = ticker_data['Close'].rolling(window=50).mean()

    #dictionaries -> important that this data has the same range of date as the plot.
    ma10 = mpf.make_addplot(ticker_data['MA10'][start_date:], color="darkorange", width=1.5, label='MA10') #width determina grosor de la linea
    ma20 = mpf.make_addplot(ticker_data['MA20'][start_date:], color="firebrick", width=1.5, label='MA20') #type, linestyle, alpha could be added
    ma50 = mpf.make_addplot(ticker_data['MA50'][start_date:], color="tomato", width=1.5, label='MA50')

    #dictionary with volumes
    ticker_data['Volume20R'] = ticker_data['Volume'].rolling(window=20).mean()
    volume = mpf.make_addplot(ticker_data['Volume20R'][start_date:], color="lightgray", panel=1, label='Vol MA20')

    #dictionary with RSI and added to plot
    ticker_data['RSI14'] = rsi_tradingview(ticker_data, ticker, 14)['RSI']
    rsi = mpf.make_addplot(ticker_data['RSI14'][start_date:], color="steelblue", panel=3, label='RSI14')

    #MAMA and FAMA
    ticker_data["MAMA"], ticker_data["FAMA"] = calculate_mama_fama(ticker_data)
    mama = mpf.make_addplot(ticker_data["MAMA"][start_date:], color="cadetblue", panel=2, label='MAMA', secondary_y=False) #secondary y false so they share the same y-axis numbers.
    fama = mpf.make_addplot(ticker_data["FAMA"][start_date:], color="lightsteelblue", panel=2, label='FAMA', secondary_y=False)
    price = mpf.make_addplot(ticker_data["Close"][start_date:], color="black", panel=2, label='price', secondary_y=False)

    #ratios vs MA
    ticker_data['ratio/MA10'] = ticker_data["Close"] / ticker_data["MA10"]
    ticker_data['ratio/MA20'] = ticker_data["Close"] / ticker_data["MA20"]
    ticker_data['ratio/MA50'] = ticker_data["Close"] / ticker_data["MA50"]
    ratioMA10 =  mpf.make_addplot(ticker_data["ratio/MA10"][start_date:], color="forestgreen", panel=4, label='$/MA10', secondary_y=False)
    ratioMA20 =  mpf.make_addplot(ticker_data["ratio/MA20"][start_date:], color="olivedrab", panel=4, label='$/MA20', secondary_y=False)
    ratioMA50 =  mpf.make_addplot(ticker_data["ratio/MA50"][start_date:], color="darkolivegreen", panel=4, label='$/MA50', secondary_y=False)

    #probability bands
    ticker_data["high_range"], ticker_data["low_range"] = calculate_risk_ranges(ticker_data, lookback=21, skew_length=21, choiceMidPoint='Tight')
    high_range = mpf.make_addplot(ticker_data["high_range"][start_date:], color="forestgreen", panel=5, label='high', secondary_y=False)
    low_range = mpf.make_addplot(ticker_data["low_range"][start_date:], color="red", panel=5, label='low', secondary_y=False)
    price2 = mpf.make_addplot(ticker_data["Close"][start_date:], color="black", panel=5, label='price', secondary_y=False)

    #four weeks ago date
    today= ticker_data.index[-1]
    date4w = "2024-01-25"
    date4w = pd.to_datetime(date4w)
    max_price_4w = ticker_data['Close'].loc[date4w:today].max()
    min_price_4w = ticker_data['Close'].loc[date4w:today].min()

    #13 weeks
    date13w = "2023-11-20"
    date13w = pd.to_datetime(date13w)
    max_price_13w = ticker_data['Close'].loc[date13w:today].max()
    min_price_13w = ticker_data['Close'].loc[date13w:today].min()

    # 26 weeks
    date26w = "2023-07-20"
    date26w = pd.to_datetime(date26w)
    max_price_26w = ticker_data['Close'].loc[date26w:today].max()
    min_price_26w = ticker_data['Close'].loc[date26w:today].min()
    [(date26w, max_price_26w), (date26w, min_price_26w), (today, min_price_26w), (today, max_price_26w),
     (date26w, max_price_26w)]
    sequence = [[(date26w, max_price_26w), (date26w, min_price_26w), (today, min_price_26w), (today, max_price_26w), (date26w, max_price_26w)],
                     [(date13w, max_price_13w), (date13w, min_price_13w), (today, min_price_13w), (today, max_price_13w), (date13w, max_price_13w)],
                     [(date4w, max_price_4w), (date4w, min_price_4w), (today, min_price_4w), (today, max_price_4w), (date4w, max_price_4w)]]

    #plot data,     #tight_layout mete el titulo dentro del grafico. figratio pone eje y a la derecha.
    fig, ax = mpf.plot(
             ticker_data[start_date:],
             type='candle',
             addplot = [ma10, ma20, ma50, price, fama, mama, volume, rsi,ratioMA10, ratioMA20, ratioMA50, high_range, low_range, price2],
             title=f'{ticker}',
             volume=True, #volume barchart
             style='yahoo',
             datetime_format = '%b.%d',
             returnfig=True,
             xrotation=0,
             panel_ratios = (6, 2, 2, 2, 2, 4),
             figscale = 2,
             alines= dict(alines=sequence, colors=['lightblue', 'steelblue', 'blue']),
    )

    pdf_pages.savefig() #save the figure plotted to the pdf
    plt.close()

def main():
    tickers = ['AAPL', 'MSFT']
    start_time = "2021-06-01"
    start_date = "2023-06-01"

    with PdfPages('stockAnalysis.pdf') as pdf_pages:
        for ticker in tickers:
            ticker_data = fetch_ticker_data(ticker, start_time)
            ticker_data = cleaning_dataframe(ticker_data)

            plot_price_MA_volume(ticker_data, ticker, pdf_pages, start_date=start_date)


if __name__ == '__main__':
    main()
