import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def add_data_dataframe(stocks, df):
    '''given a list of stocks and a dataframe, downloads the "Close" price
     of each stock everyday and concatenates it to the dataframe.'''
    for stock in stocks:
        stockDataframe = yf.download(stock, period="max")["Close"]  # columna de cotización de la stock
        stockDataframe.name = stock  # column name is the stock name
        df = pd.concat([df, stockDataframe], axis=1)  # mergeo data de cada stock al df
    return df

def cleaning_dataframe(df):
    '''clean the dataframe'''
    df.sort_index(ascending=True, inplace=True) #lo dejo sorteado con la última fecha abajo.
    df.index.name = "Date" #index column llamada "Date"
    df.ffill(inplace=True) #relleno los vacios con el valor del de arriba
    df.dropna(how="all", inplace=True) #si hay filas completamente vacias, funalas
    df.index = df.index.strftime("%Y-%m-%d")

def add_price_changes(df, percentageDF):
    '''given a dataframe with dates as index and columns for stocks, uses that information
    to compare each stock value to its previous values and adds the price change to percentageDF.'''

    for stock in df.columns:  # para cada stock
        df.index = pd.to_datetime(df.index)
        currentDate = df.index[-1]
        current = df[stock].loc[currentDate]  # last price in the stock column

        period_dict_days = {"1D": 1, "1W": 7, "1M": 28, "3M":91}
        for periodKey, periodValue in period_dict_days.items():  # para cada período
            pastDate = find_previous_closest_date(currentDate - pd.DateOffset(days=periodValue), df)
            past = df[stock].loc[pastDate]  # calculo valor en ese momento
            priceChange = (current - past) / past * 100  # calculo el porcentaje de cambio de precio
            if priceChange == 0: #caso donde la bolsa todavia no operó hoy, comparo ayer con anteayer
                pastDate = find_previous_closest_date(currentDate - pd.DateOffset(days=2), df)
                past = df[stock].loc[pastDate]  # calculo valor en ese momento
                priceChange = (current - past) / past * 100  # calculo el porcentaje de cambio de precio
            percentageDF.loc[stock, periodKey] = round(priceChange, 1)  # agrego al dataframe

        period_dict_months = {"6M": 6}
        for periodKey, periodValue in period_dict_months.items():  # para cada período
            pastDate = find_previous_closest_date(currentDate - pd.DateOffset(months=periodValue), df)
            past = df[stock].loc[pastDate]  # calculo valor en ese momento
            priceChange = (current - past) / past * 100  # calculo el porcentaje de cambio de precio
            percentageDF.loc[stock, periodKey] = round(priceChange, 1)  # agrego al dataframe

        period_dict_years = {"1Y": 1, "2Y": 2, "3Y":3}
        for periodKey, periodValue in period_dict_years.items():  # para cada período
            pastDate = find_previous_closest_date(currentDate - pd.DateOffset(years=periodValue), df)
            past = df[stock].loc[pastDate]  # calculo valor en ese momento
            priceChange = (current - past) / past * 100  # calculo el porcentaje de cambio de precio
            percentageDF.loc[stock, periodKey] = round(priceChange, 1)  # agrego al dataframe

        #grab the day before the first day of the actual month
        mtdDate = currentDate.replace(day=1) - timedelta(days=1)
        mtdValue = df[stock].loc[find_previous_closest_date(mtdDate, df)]
        mtdPriceChange = (current - mtdValue) / mtdValue * 100
        percentageDF.loc[stock, "MTD"] = round(mtdPriceChange, 1)

        #grab the day before the first day of the actual quarter
        current_quarter = (currentDate.month - 1) // 3 + 1 #calculo para sacar quarter actual
        qtdDate = datetime(currentDate.year, (current_quarter-1)*3+1, 1) - timedelta(days=1)
        qtdValue = df[stock].loc[find_previous_closest_date(qtdDate, df)] #busco valor qtd en la fecha + cercana a la querida
        qtdPriceChange = (current - qtdValue) / qtdValue * 100
        percentageDF.loc[stock, "QTD"] = round(qtdPriceChange, 1) #guardo en percentageDF

        #grab the day before the first day of the actual year
        ytdDate = datetime(currentDate.year - 1, 12, 31)
        ytdValue = df[stock].loc[find_previous_closest_date(ytdDate, df)]
        ytdPriceChange = (current - ytdValue) / ytdValue * 100
        percentageDF.loc[stock, "YTD"] = round(ytdPriceChange, 1)

        dateAsked = datetime(2022, 12, 9)
        dateAskedValue = df[stock].loc[dateAsked]
        dateAskedPriceChange = (current - dateAskedValue) / dateAskedValue * 100
        percentageDF.loc[stock, "2022/12/9"] = round(dateAskedPriceChange, 1)

        deviationReturn1D = get_standarized_daily_return(df, stock)
        percentageDF.loc[stock, "1Ddesvios"] = round(deviationReturn1D, 1)

        deviationReturn1W = get_standarized_weekly_return(df, stock)
        percentageDF.loc[stock, "1Wdesvios"] = round(deviationReturn1W, 1)

        deviationReturn1M = get_standarized_monthly_return(df, stock)
        percentageDF.loc[stock, "1Mdesvios"] = deviationReturn1M

        deviationReturn3M = get_standarized_trimestral_return(df, stock)
        percentageDF.loc[stock, "3Mdesvios"] = deviationReturn3M

    return percentageDF

def add_sectors(sectorStockDict, percentageDF):
    for sector, stock in sectorStockDict.items():
        percentageDF.loc[stock, "Sector"] = sector
    return percentageDF

def style_dataframe(notStyledDF, columnsIncluded):
    '''applyies gradient to the dataframe and columns given'''
    stylePercentageDF = notStyledDF.style.background_gradient(subset=columnsIncluded, cmap='RdYlGn',
                                                               axis=0)  # applied by column not row
    return stylePercentageDF

def find_previous_closest_date(current_date, df):
    closest_date = None
    min_difference = float('inf') #infinito

    for date in df.index:
        if date > current_date:
            continue

        difference = abs((date - current_date).total_seconds())
        if difference < min_difference:
            min_difference = difference
            closest_date = date

    return closest_date

def get_standarized_daily_return(df, stock):
    daily_returns = df[stock].pct_change().iloc[-67:-1]
    current_pct = daily_returns[-1]
    mean_66_rounds_pct = daily_returns.median() #median price change
    deviation_66_rounds_pct = daily_returns.std()
    standarized_price = (current_pct - mean_66_rounds_pct) / (deviation_66_rounds_pct)
    return standarized_price

def get_standarized_weekly_return(df, stock):
    #current_date = df.index[-1]
    #current_price = df[stock].loc[current_date]

    current_day_of_week = df[stock].index[-1].day_name() #nombre de dia de semana
    starting_day = current_day_of_week[:3] #tomo las primeras 3 letras

    #tabla de retornos del último dia de la semana, en % comparado al anterior
    #'W-' names the table, and closed=left to include the actual day in the week
    #tomo la cotización de hoy, la comparo con la de una semana antes, y doy el % q creció
    #cada semana termina el dia semanal de hoy. si hoy es miercoles, arranca la semana el jueves y termina el miercoles (closed='right')
    weekly_returns = df[stock].resample('W-' + starting_day, closed='right').last().pct_change()

    #agarro % de la última actual semana
    current_week_return = weekly_returns.iloc[-1]

    #últimas 13 sin contar la actual
    last_13_weeks_returns = weekly_returns.iloc[-14:-1]

    #saco mediana y desvio de los 13 price changes
    med = last_13_weeks_returns.median()
    ds = last_13_weeks_returns.std()

    #print(stock, current_week_return, med, ds)

    #lo estandarizo.
    standarized = (current_week_return - med) / (ds)
    return standarized

def get_standarized_monthly_return(df, stock):
    current_day_of_week = df[stock].index[-1].day_name()  # nombre de dia de semana
    starting_day = current_day_of_week[:3]  # tomo las primeras 3 letras

    weekly_returns = df[stock].resample('W-' + starting_day, closed='right').last().pct_change()
    last_56_weeks_returns = weekly_returns.iloc[-56:]

    #numeric index, Date and weekly_returns
    four_week_packs = create_4week_from_weeks(stock, last_56_weeks_returns) #dejar el último al final nuevamente

    last_month_return = four_week_packs.iloc[-1]["weekly_returns"] #retorno del último mes
    #last_12_months_returns = four_week_packs.iloc[-13:-1] #últimos 12 packs de 4 semanas

    #obtengo data de las últimas 52 semanas sin contar las últimas 4
    med = weekly_returns.iloc[-56:-4].median()
    ds = weekly_returns.iloc[-56:-4].std()

    print(weekly_returns)
    print(stock, last_month_return, med*4, ds*np.sqrt(4))
    standarized = (last_month_return - med*4) / ds*np.sqrt(4)
    return standarized

def get_standarized_trimestral_return(df, stock):
    current_day_of_week = df[stock].index[-1].day_name()  # nombre de dia de semana
    starting_day = current_day_of_week[:3]  # tomo las primeras 3 letras

    weekly_returns = df[stock].resample('W-' + starting_day, closed='right').last().pct_change()
    last_65_weeks_returns = weekly_returns.iloc[-65:]

    # numeric index, Date and weekly_returns
    thirteen_week_packs = create_13week_from_weeks(stock, last_65_weeks_returns)  # dejar el último al final nuevamente
    last_3months_return = thirteen_week_packs.iloc[-1]["weekly_returns"]  # no cuento el current mes

    #med y ds de las últimas 65 semanas sin contar las últimas 13
    med = weekly_returns.iloc[-65:-13].median()
    ds = weekly_returns.iloc[-65:-13].std()

    #print(stock, last_3months_return, med*13, ds*np.sqrt(4))

    standarized = (last_3months_return - med*13) / ds * np.sqrt(13)
    return standarized

def create_4week_from_weeks(stock, weekly_returns):
    num_rows = len(weekly_returns)

    four_week_packs = pd.DataFrame(columns=['Date', 'weekly_returns'])

    for i in range(0, num_rows, 4):
        chunk = weekly_returns.iloc[i:i+4]

        chunk.index.name = 'Date'
        last_date = chunk.index[-1]

        sum_value = 0
        for i in range(4):
            value = chunk[i]
            sum_value += value


        four_week_packs = four_week_packs.append({'Date': last_date, 'weekly_returns': sum_value}, ignore_index=True)

    #four_week_packs['Date'] = pd.to_datetime(four_week_packs['Date'])
    four_week_packs.set_index('Date', inplace=True)
    #print(four_week_packs)
    return four_week_packs

def create_13week_from_weeks(stock, weekly_returns):
    num_rows = len(weekly_returns)

    thirteen_week_packs = pd.DataFrame(columns=['Date', 'weekly_returns'])

    for i in range(0, num_rows, 13):
        chunk = weekly_returns.iloc[i:i+13]

        chunk.index.name = 'Date'
        last_date = chunk.index[-1]

        sum_value = 0
        for i in range(13):
            value = chunk[i]
            sum_value += value


        thirteen_week_packs = thirteen_week_packs.append({'Date': last_date, 'weekly_returns': sum_value}, ignore_index=True)

    #four_week_packs['Date'] = pd.to_datetime(four_week_packs['Date'])
    thirteen_week_packs.set_index('Date', inplace=True)
    #print(four_week_packs)
    return thirteen_week_packs
