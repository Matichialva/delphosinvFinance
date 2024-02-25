import mplfinance as mpf
import pandas as pd
import yfinance as yf  # You can use any other method to get financial data

# Get financial data (replace 'AAPL' and '2023-01-01' with your stock symbol and start date)
symbol = 'AAPL'
start_date = '2023-01-01'
df = yf.download(symbol, start=start_date)
print(df)

# Create a candlestick chart with a line graph overlay
fig, ax = mpf.plot(df, type='candle', #plot type
                   mav=(10, 20), #moving averages
                   volume=True, #volume subplot
                   style='yahoo', #color scheme based on yahoo finance
                   title=f'{symbol} Stock Price with Moving Averages',
                   ylabel='Price ($)',
                   ylabel_lower='Volume',
                   mavcolors=('tab:red','tab:blue'),  # Color for moving averages
                   figratio=(10, 6),    # Figure size ratio
                   tight_layout=True)

# Save or show the plot
mpf.show()

##############################################################3
'''
USING NICO'S CODE
# Function to fetch stock data
def get_stock_data(ticker, start_date, end_date):
    stock_data = yf.download(ticker, start=start_date, end=end_date)
    return stock_data


# Function to calculate MAMA and FAMA
def calculate_mama_fama(data, fast=0.25, slow=0.05):
    Price = data['Close']
    FastLimit = fast
    SlowLimit = slow
    MAMA = [0] * len(data)  # Initialize as a list
    FAMA = [0] * len(data)  # Initialize as a list
    PI = math.pi
    Smooth = [0.0] * len(data)  # Initialize as a list
    Detrender = [0.0] * len(data)  # Initialize as a list
    I1 = [0.0] * len(data)  # Initialize as a list
    Q1 = [0.0] * len(data)  # Initialize as a list
    jI = [0.0] * len(data)  # Initialize as a list
    jQ = [0.0] * len(data)  # Initialize as a list
    I2 = [0.0] * len(data)  # Initialize as a list
    Q2 = [0.0] * len(data)  # Initialize as a list
    Re = [0.0] * len(data)  # Initialize as a list
    Im = [0.0] * len(data)  # Initialize as a list
    Period = [0.0] * len(data)  # Initialize as a list
    SmoothPeriod = [0.0] * len(data)  # Initialize as a list
    Phase = [0.0] * len(data)  # Initialize as a list
    DeltaPhase = [0.0] * len(data)  # Initialize as a list
    alpha = [0.0] * len(data)  # Initialize as a list

    for i in range(len(data)):
        if math.isnan(Price[i]):
            MAMA[i] = MAMA[i - 1]
            FAMA[i] = FAMA[i - 1]
            Smooth[i] = Smooth[i - 1]
            Detrender[i] = Detrender[i - 1]
            I1[i] = I1[i - 1]
            Q1[i] = Q1[i - 1]
            I2[i] = I2[i - 1]
            Q2[i] = Q2[i - 1]
            Re[i] = Re[i - 1]
            Im[i] = Im[i - 1]
            Period[i] = Period[i - 1]
            SmoothPeriod[i] = SmoothPeriod[i - 1]
            Phase[i] = Phase[i - 1]
            continue

        if i > 5:
            Smooth[i] = (4 * Price[i] + 3 * Price[i - 1] + 2 * Price[i - 2] + Price[i - 3]) / 10
            Detrender[i] = (0.0962 * Smooth[i] + 0.5769 * Smooth[i - 2] - 0.5769 * Smooth[i - 4] - 0.0962 * Smooth[
                i - 6]) * (0.075 * Period[i - 1] + 0.54)
            Q1[i] = (0.0962 * Detrender[i] + 0.5769 * Detrender[i - 2] - 0.5769 * Detrender[i - 4] - 0.0962 * Detrender[
                i - 6]) * (0.075 * Period[i - 1] + 0.54)
            I1[i] = Detrender[i - 3]
            jI[i] = (0.0962 * I1[i] + 0.5769 * I1[i - 2] - 0.5769 * I1[i - 4] - 0.0962 * I1[i - 6]) * (
                        0.075 * Period[i - 1] + 0.54)
            jQ[i] = (0.0962 * Q1[i] + 0.5769 * Q1[i - 2] - 0.5769 * Q1[i - 4] - 0.0962 * Q1[i - 6]) * (
                        0.075 * Period[i - 1] + 0.54)
            I2[i] = I1[i] - jQ[i]
            Q2[i] = Q1[i] + jI[i]
            I2[i] = 0.2 * I2[i] + 0.8 * I2[i - 1]
            Q2[i] = 0.2 * Q2[i] + 0.8 * Q2[i - 1]
            Re[i] = I2[i] * I2[i - 1] + Q2[i] * Q2[i - 1]
            Im[i] = I2[i] * Q2[i - 1] - Q2[i] * I2[i - 1]
            Re[i] = 0.2 * Re[i] + 0.8 * Re[i - 1]
            Im[i] = 0.2 * Im[i] + 0.8 * Im[i - 1]

            if Im[i] != 0 and Re[i] != 0:
                Period[i] = 2 * PI / math.atan(Im[i] / Re[i])
                Period[i] = min(1.5 * Period[i - 1], max(0.67 * Period[i - 1], Period[i]))
                Period[i] = min(50, max(6, Period[i]))
                Period[i] = 0.2 * Period[i] + 0.8 * Period[i - 1]
                SmoothPeriod[i] = 0.33 * Period[i] + 0.67 * SmoothPeriod[i - 1]

                if I1[i] != 0:
                    Phase[i] = 180 / PI * math.atan(Q1[i] / I1[i])
                    DeltaPhase[i] = Phase[i - 1] - Phase[i]
                    DeltaPhase[i] = max(1, DeltaPhase[i])
                    alpha[i] = FastLimit / DeltaPhase[i]
                    alpha[i] = max(SlowLimit, min(FastLimit, alpha[i]))
                    MAMA[i] = alpha[i] * Price[i] + (1 - alpha[i]) * MAMA[i - 1]
                    FAMA[i] = 0.5 * alpha[i] * MAMA[i] + (1 - 0.5 * alpha[i]) * FAMA[i - 1]

    return MAMA, FAMA


# Function to plot stock data, MAMA, and FAMA
def plot_stock_with_mama_fama(data, mama, fama, ticker):
    plt.figure(figsize=(10, 6))

    # Plotting stock prices
    plt.plot(data.index, data['Close'], label=f'{ticker} Stock Price', color='black')

    # Plotting MAMA and FAMA
    plt.plot(data.index, mama, label='MAMA', color='red')
    plt.plot(data.index, fama, label='FAMA', color='blue')

    # Adding legends and title
    plt.legend()
    plt.title(f'{ticker} Stock Price with MAMA and FAMA')
    plt.xlabel('Date')
    plt.ylabel('Price')

    # Show plot
    plt.show()


if __name__ == "__main__":
    # Specify the stock symbol, start date, and end date
    ticker_symbol = "AAPL"
    start_date = "2023-06-01"
    end_date = "2024-02-15"

    # Fetch stock data
    stock_data = get_stock_data(ticker_symbol, start_date, end_date)

    # Calculate MAMA and FAMA
    mama, fama = calculate_mama_fama(stock_data)

    # Plot stock data with MAMA and FAMA
    plot_stock_with_mama_fama(stock_data, mama, fama, ticker_symbol)

'''
'''
# Function to plot stock data, MAMA, and FAMA
def plot_stock_with_mama_fama(data, mama, fama, ticker):
    plt.figure(figsize=(10, 6))

    # Plotting stock prices
    plt.plot(data.index, data['Close'], label=f'{ticker} Stock Price', color='black')

    # Plotting MAMA and FAMA
    plt.plot(data.index, mama, label='MAMA', color='red')
    plt.plot(data.index, fama, label='FAMA', color='blue')

    # Adding legends and title
    plt.legend()
    plt.title(f'{ticker} Stock Price with MAMA and FAMA')
    plt.xlabel('Date')
    plt.ylabel('Price')

    # Show plot
    plt.show()
'''


import yfinance as yf
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import mplfinance as mpf
import numpy as np
import pandas as pd
import math
import talib

def fetch_stock_data(ticker, start_date):
    stock_data = yf.download(ticker, start=start_date)
    return stock_data

def plot_stock_price(stock_data, ticker, pdf_pages):
    # Calculate moving average of volume
    stock_data['Volume_MA'] = stock_data['Volume'].rolling(window=20).mean()

    # Plot candlestick chart with volume subplot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [3, 1]})

    mpf.plot(stock_data, type='candle', ax=ax1, volume=ax2, show_nontrading=True)
    ax1.set_yscale('log')  # Logarithmic scale for the price axis

    # Add line for moving average of volume
    ax2.plot(stock_data.index, stock_data['Volume_MA'], label='Volume MA (20 rounds)', color='orange', linestyle='--')
    ax2.legend()

    plt.title(f'{ticker} Candlestick Chart with Volume and Volume MA')
    pdf_pages.savefig()
    plt.close()

# Function to calculate MAMA and FAMA using talib
def calculate_mama_fama(data, fast=0.25, slow=0.05):
    mama, fama = talib.MAMA(data['Close'], fastlimit=fast, slowlimit=slow)
    return pd.Series(mama, index=data.index), pd.Series(fama, index=data.index)

# Function to plot candlestick chart with MAMA and FAMA
def plot_candlestick_with_mama_fama(data, mama, fama, ticker, pdf_pages):
    # Create a DataFrame with MAMA and FAMA values
    df_mama_fama = pd.DataFrame({'MAMA': mama, 'FAMA': fama}, index=data.index)

    # Plot candlestick chart with MAMA and FAMA
    mpf.plot(data, type='candle', mav=(20,), volume=True, addplot=df_mama_fama, figscale=1.2, title=f'{ticker} Candlestick with MAMA and FAMA',
             ylabel='Price', ylabel_lower='Volume', style='yahoo', show_nontrading=True, savefig=pdf_pages)

def plot_probability_bands(stock_data, ticker, pdf_pages):
    # Add your code to plot probability bands using mplfinance
    # Example:
    fig, ax = plt.subplots(figsize=(12, 6))
    # Plot probability bands
    plt.title(f'{ticker} Probability Bands')
    pdf_pages.savefig()
    plt.close()

def plot_rsi(stock_data, ticker, pdf_pages):
    # Calculate RSI using Talib library
    stock_data['RSI'] = talib.RSI(stock_data['Close'], timeperiod=14)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(stock_data['RSI'], label='RSI (14 weeks)')
    plt.title(f'{ticker} RSI Over Time (14 weeks)')
    plt.xlabel('Date')
    plt.ylabel('RSI Value')
    ax.legend()
    pdf_pages.savefig()
    plt.close()

def plot_max_min_lines(stock_data, ticker, pdf_pages):
    # Add your code to draw lines at maximum and minimum values using mplfinance
    # Example:
    fig, ax = plt.subplots(figsize=(12, 6))
    # Plot lines at max and min values
    plt.title(f'{ticker} Max and Min Lines')
    pdf_pages.savefig()
    plt.close()

def plot_volatility(stock_data, ticker, pdf_pages):
    # Calculate volatility using Talib library
    stock_data['Volatility'] = talib.ATR(stock_data['High'], stock_data['Low'], stock_data['Close'])

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(stock_data['Volatility'], label='Volatility')
    plt.title(f'{ticker} Volatility Over Time')
    plt.xlabel('Date')
    plt.ylabel('Volatility Value')
    ax.legend()
    pdf_pages.savefig()
    plt.close()

def main():
    tickers = ['AAPL']  # Add your desired tickers
    start_date = '2023-06-01'  # Specify the start date

    with PdfPages('stock_analysis.pdf') as pdf_pages:
        for ticker in tickers:
            stock_data = fetch_stock_data(ticker, start_date)
            plot_stock_price(stock_data, ticker, pdf_pages)

            mama, fama = calculate_mama_fama(stock_data)
            plot_candlestick_with_mama_fama(stock_data, mama, fama, ticker, pdf_pages)

            plot_probability_bands(stock_data, ticker, pdf_pages)
            plot_rsi(stock_data, ticker, pdf_pages)
            plot_max_min_lines(stock_data, ticker, pdf_pages)
            plot_volatility(stock_data, ticker, pdf_pages)

if __name__ == "__main__":
    main()
