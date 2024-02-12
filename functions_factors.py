import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime
from functions_etfReturns import *

def fetch_stock_prices(tickers):
    # ARMO PRICESDF
    tickers.insert(0, "^SPX")

    # dataframe con precios de tickers del sp500
    hoy = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    pricesDF = pd.DataFrame(index=pd.date_range(start=datetime(2022, 1, 1), end=hoy, freq="B"))  # freq B -> business days

    pricesDF = add_data_dataframe(tickers, pricesDF, "5y")  # lleno el df con data de cada stock
    cleaning_dataframe(pricesDF)  # función que limpia datos

    tickers.remove('^SPX')

    return pricesDF

def calculate_percentage_dataframe(tickers, pricesDF):
    # ARMO PERCENTAGEDF
    # dataframe con retornos de empresas del sp500 (en la lista)
    percentageDF = pd.DataFrame(index=tickers, columns=["1D", "1W", "1M", "3M", "6M", "YTD"])
    percentageDF.index.name = "Stock"

    for stock in pricesDF.columns:  # para cada stock
        if stock == '^SPX':
            continue
        pricesDF.index = pd.to_datetime(pricesDF.index)
        currentDate = pricesDF.index[-1]
        current = pricesDF[stock].loc[currentDate]  # last price in the stock column

        period_dict_days = {"1D": 1, "1W": 7, "1M": 28, "3M": 91}
        for periodKey, periodValue in period_dict_days.items():  # para cada período
            pastDate = find_previous_closest_date(currentDate - pd.DateOffset(days=periodValue), pricesDF)
            past = pricesDF[stock].loc[pastDate]  # calculo valor en ese momento
            priceChange = (current - past) / past * 100  # calculo el porcentaje de cambio de precio
            if priceChange == 0:  # caso donde la bolsa todavia no operó hoy, comparo ayer con anteayer
                pastDate = find_previous_closest_date(currentDate - pd.DateOffset(days=2), pricesDF)
                past = pricesDF[stock].loc[pastDate]  # calculo valor en ese momento
                priceChange = (current - past) / past * 100  # calculo el porcentaje de cambio de precio
            percentageDF.loc[stock, periodKey] = round(priceChange, 1)  # agrego al dataframe

        period_dict_months = {"6M": 6}
        for periodKey, periodValue in period_dict_months.items():  # para cada período
            pastDate = find_previous_closest_date(currentDate - pd.DateOffset(months=periodValue), pricesDF)
            past = pricesDF[stock].loc[pastDate]  # calculo valor en ese momento
            priceChange = (current - past) / past * 100  # calculo el porcentaje de cambio de precio
            percentageDF.loc[stock, periodKey] = round(priceChange, 1)  # agrego al dataframe

        # grab the day before the first day of the actual year
        ytdDate = datetime(currentDate.year - 1, 12, 31)
        ytdValue = pricesDF[stock].loc[find_previous_closest_date(ytdDate, pricesDF)]
        ytdPriceChange = (current - ytdValue) / ytdValue * 100
        percentageDF.loc[stock, "YTD"] = round(ytdPriceChange, 1)

    return percentageDF

def calculate_factors_dataframe(tickers, pricesDF, percentageDF, balanceDF):
    factorsDF = pd.DataFrame(index=tickers,
                             columns=["DividendYield (%)", "netDebt/EV (%)", "marketCap (M)", "volatility20r (%)",
                                      "Momentum (1m vs 4m)", "Beta (3y)"])
    factorsDF.index.name = "Ticker"
    factorsDF = add_factors(factorsDF, pricesDF, percentageDF, balanceDF)
    return factorsDF

def calculate_top_down_factors(factorsDF, pricesDF, percentageDF):
    factors = ["DividendYield (%)", "netDebt/EV (%)", "marketCap (M)", "volatility20r (%)", "Momentum (1m vs 4m)",
               "Beta (3y)"]
    ranges = ["30% top", "30% bottom"]
    time_frames = ["1D", "1W", "1M", "3M", "6M", "YTD"]
    topDownFactorsDF = pd.DataFrame(index=pd.MultiIndex.from_product([factors, ranges], names=['factor', 'ranges']),
                                    columns=time_frames)
    topDownFactorsDF = add_factors_to_topdown(topDownFactorsDF, factorsDF, pricesDF, percentageDF)
    return topDownFactorsDF

def add_factors(factorsDF, pricesDF, percentageDF, balanceDF):

    for ticker in factorsDF.index:
        #datos útiles
        last_price = pricesDF[ticker].iloc[-1]
        dividendos_pagados = balanceDF.loc[ticker]["Dividendos pagados"]
        net_debt = balanceDF.loc[ticker]["Net Debt"]
        shares_out = balanceDF.loc[ticker]["Shares Out"]

        try:
            market_cap = (shares_out) * last_price
            enterprise_value = net_debt + market_cap
            market_cap = round(market_cap, 2)
            netDebt_enterpriseValue = round((net_debt / enterprise_value) * 100, 2)
            dividend_yield = round((dividendos_pagados / market_cap) * 100, 2)
        except:
            market_cap = "null"
            enterprise_value = "null"
            netDebt_enterpriseValue = "null"
            dividend_yield = "null"

        #calculo factores
        volatility = calculate_volatility(pricesDF, ticker, 20)
        momentum = calculate_momentum(pricesDF, ticker)
        beta = calculate_beta(pricesDF, ticker)

        # agrego factores a factorsDF
        add_factors_to_df(ticker, factorsDF, dividend_yield, netDebt_enterpriseValue, market_cap, volatility, momentum, beta)

    return factorsDF

def add_factors_to_df(ticker, factorsDF, dividend_yield, netDebt_enterpriseValue, market_cap, volatility, momentum, beta):
    factorsDF.loc[ticker, "DividendYield (%)"] = dividend_yield
    factorsDF.loc[ticker, "netDebt/EV (%)"] = netDebt_enterpriseValue
    factorsDF.loc[ticker, "marketCap (M)"] = market_cap
    factorsDF.loc[ticker, "volatility20r (%)"] = volatility
    factorsDF.loc[ticker, "Momentum (1m vs 4m)"] = momentum
    factorsDF.loc[ticker, "Beta (3y)"] = beta

def calculate_volatility(pricesDF, ticker, rounds):
    retornos = []
    for i in range(rounds):
        #calculo % entre cada dia y su anterior, y sumo los 20 retornos a lista de retornos
        previous = pricesDF[ticker].iloc[-(i+2)]
        actual = pricesDF[ticker].iloc[-(i+1)]
        retornos.append((actual / previous - 1 )*100)

    deviation = np.std(retornos, ddof=1)
    return round(deviation, 2)

def calculate_momentum(pricesDF, ticker):
    pricesDF.index = pd.to_datetime(pricesDF.index)
    current_date = pricesDF.index[-1]
    oneMonthAgoDate = current_date - pd.DateOffset(days=28)
    fourMonthsAgoDate = current_date - pd.DateOffset(days=112)

    oneMonthAgoPrice = pricesDF[ticker].loc[oneMonthAgoDate]
    fourMonthsAgoPrice = pricesDF[ticker].loc[fourMonthsAgoDate]

    momentum = ((oneMonthAgoPrice - fourMonthsAgoPrice) / fourMonthsAgoPrice) * 100

    return round(momentum, 2)

def calculate_beta(pricesDF, ticker):
    stockData = pricesDF[ticker]
    marketData = pricesDF['^SPX']

    #calculo retornos desde hace 3 años
    stockReturns = stockData.iloc[-756:].pct_change()
    marketReturns = marketData.iloc[-756:].pct_change()

    #unifico retornos de ambos en un mismo dataframe
    merged_data = pd.merge(stockReturns, marketReturns, left_index=True, right_index=True)

    #calculo el beta
    covariance = merged_data.cov().iloc[0, 1] #[0, 1] ya q .cov() arma las 4 covarianzas, yo agarro la cov(S, M)
    market_variance = np.var(marketReturns)
    beta = covariance / market_variance

    return round(beta, 2)

def add_factors_to_topdown(topDownFactorsDF, factorsDF, pricesDF, percentageDF):
    factors = ["DividendYield (%)", "netDebt/EV (%)", "marketCap (M)", "volatility20r (%)", "Momentum (1m vs 4m)", "Beta (3y)"]
    ranges = ["30% top", "30% bottom"]
    time_frames = ["1D", "1W", "1M", "3M", "6M", "YTD"]

    #para cada factor
    for factor in factors:
        #sorteo en orden ascendiente y limpio nulos
        sorted_stocks_by_factor = factorsDF[factor].copy()
        sorted_stocks_by_factor.sort_values(ascending=False, inplace=True)
        sorted_stocks_by_factor = sorted_stocks_by_factor.dropna()

        #cantidad de stocks a meter en top y bottom
        selected_quantity = int(0.25 * len(sorted_stocks_by_factor))

        #extraigo top 30% y bottom 30%
        top = sorted_stocks_by_factor.head(selected_quantity)
        bottom = sorted_stocks_by_factor.tail(selected_quantity)


        #listas de top y bottom
        top_tickers = top.index.tolist()
        bottom_tickers = bottom.index.tolist()

        #para cada time frame
        for time in time_frames:
            top_returns = []
            bottom_returns = []

            #para cada ticker del top, agrego su retorno a la lista
            for top_ticker in top_tickers:
                ticker_return = percentageDF.loc[top_ticker, time] #calculo su retorno en ese time frame
                if not np.isnan(ticker_return):
                    top_returns = np.append(top_returns, ticker_return) #lo agrego a lista de retornos
            top_returns_mean = top_returns.mean()   #saco la media de todos los retornos de lista top
            topDownFactorsDF.loc[(factor, "30% top"), time] = top_returns_mean  #añado al dataframe

            # para cada ticker del bottom, agrego su retorno a la lista
            for bottom_ticker in bottom_tickers:
                ticker_return = percentageDF.loc[bottom_ticker, time]  # calculo su retorno en ese time frame
                if not np.isnan(ticker_return):
                    bottom_returns.append(ticker_return) # lo agrego a lista de retornos
            bottom_returns_mean = sum(bottom_returns)/len(bottom_returns) # saco la media de todos los retornos de lista top
            topDownFactorsDF.loc[(factor, "30% bottom"), time] = bottom_returns_mean # añado al dataframe

    return topDownFactorsDF
