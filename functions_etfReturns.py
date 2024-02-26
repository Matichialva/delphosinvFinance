import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

def add_data_dataframe(stocks, df, periodo):
    '''given a list of stocks and a dataframe, downloads the "Close" price
     of each stock everyday and concatenates it to the dataframe.'''
    for stock in stocks:
        stockDataframe = yf.download(stock, period=periodo)["Close"]  # columna de cotización de la stock
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
    return df

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
            if (priceChange == 0) and (periodKey == "1D"): #caso donde la bolsa todavia no operó hoy, comparo ayer con anteayer
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

        deviationReturn1D = get_standarized_daily_return(df, stock, 66)
        percentageDF.loc[stock, "1Ddesvios"] = round(deviationReturn1D, 1)

        deviationReturn1W = get_standarized_weekly_return(df, stock)
        percentageDF.loc[stock, "1Wdesvios"] = round(deviationReturn1W, 1)

        deviationReturn1M = get_standarized_monthly_return(df, stock)
        percentageDF.loc[stock, "1Mdesvios"] = round(deviationReturn1M, 1)

    return percentageDF

def add_sectors(sectorStockDict, percentageDF):
    for sector, stock in sectorStockDict.items():
        percentageDF.loc[stock, "Sector"] = sector
    return percentageDF

def color_red_green(val):
    if val < 0:
        return 'background-color: red'
    elif val > 0:
        return 'background-color: green'
    else:
        return 'background-color: black'

def style_dataframe_red_green(notStyledDF, columnsIncluded):
    '''applyies red/green values to the dataframe and columns given'''
    stylePercentageDF = notStyledDF.style.applymap(lambda x: [color_red_green(v) for v in x], subset=columnsIncluded)
    return stylePercentageDF

def style_dataframe(notStyledDF, columnsIncluded):
    '''applyies gradient to the dataframe and columns given'''
    stylePercentageDF = notStyledDF.style.background_gradient(subset=columnsIncluded, cmap='RdYlGn', axis=0, vmin=-10, vmax=10)  # applied by column not row
    return stylePercentageDF

def style_dataframe_min_max(notStyledDF, columnsIncluded, mini, maxi):
    '''applyies gradient to the dataframe and columns given'''
    stylePercentageDF = notStyledDF.style.background_gradient(subset=['1D'], cmap='RdYlGn', axis=0, vmin=mini, vmax=maxi).background_gradient(subset=['3Y'], cmap='RdYlGn', axis=0, vmin=-50, vmax=50)  # applied by column not row
    return stylePercentageDF


def highlight_max_between_pairs(data):
    # Set the background color attribute
    attr_red = 'background-color: #FFD3D3'  # or 'background-color: #FFA8A8'
    attr_green = 'background-color: #D3FFD3' # or 'background-color: #A8FFA8'

    # Create an empty list to store True/False values
    is_max_between_pairs = []

    # Loop through pairs of consecutive elements in the Series
    for i in range(0, len(data) - 1, 2):
        # Compare the current pair and highlight the greater value
        is_max_between_pairs.append(data[i] > data[i + 1])
        is_max_between_pairs.append(data[i] < data[i + 1])

    # Create a new list with background color attributes
    formatted_values = []
    for v in is_max_between_pairs:
        if v:
            formatted_values.append(attr_green)
        else:
            formatted_values.append(attr_red)

    # Return the list with background color attributes
    return formatted_values

# Define a function to add a border line after each index
def add_border_line(index):
    styles = []
    for i in range(1, len(index)*2, 2):
        styles.append({
            'selector': f'tr:nth-child({i}) td',
            'props': 'border-right: 2px solid black;'
        })
    return styles
def style_columns(notStyledDF, columnsIncluded):
    '''applyies gradient to the dataframe and columns given'''
    styled = notStyledDF.copy()

    for column in columnsIncluded:
        mini = notStyledDF[column].min()
        if mini < 0:
            maxi = -mini
        else:
            mini=-10
            maxi=10
        styled = styled.style.background_gradient(subset=[column], cmap='RdYlGn', vmin=mini, vmax=maxi)  # applied by column not row
    return styled



# Function to apply background gradient
def color_gradient(column):
    vmin = column.min()
    vmax = column.max()

    def apply_gradient(val):
        if val < 0:
            red = 255
            green = 255 + int((val/vmin) * 255)
            blue = 255 + int((val/vmin) * 255)
        elif val > 0:
            red = 255 - int((val/vmax) * 255)
            green = 255
            blue = 255 - int((val/vmax) * 255)
        else:
            red = 255
            green = 255
            blue = 255

        # Ensure RGB values are within the valid range (0 to 255)
        red = max(0, min(255, red))
        green = max(0, min(255, green))
        blue = max(0, min(255, blue))

        return f'background-color: red'

    return column.apply(lambda val: apply_gradient(val))



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

def get_standarized_daily_return(df, stock, number_of_days):
    '''df: dataframe
       stock: stock
       number_of_days: número de días a tomar para sacar la mediana, que luego
       será usada para estandarizar.'''

    daily_returns = df[stock].pct_change().iloc[-(number_of_days+1):]
    current_pct = daily_returns[-1]

    mediana = daily_returns.median()
    desvio = daily_returns.std()

    standarized_price = (current_pct - mediana) / (desvio)
    return standarized_price

def get_standarized_weekly_return(df, stock):
    current_day_of_week = df[stock].index[-1].day_name() #nombre de dia de semana
    starting_day = current_day_of_week[:3] #tomo las primeras 3 letras

    #tabla de retornos del último dia de la semana, en % comparado al anterior
    #'W-' names the table, and closed=left to include the actual day in the week
    #tomo la cotización de hoy, la comparo con la de una semana antes, y doy el % q creció
    #cada semana termina el dia semanal de hoy. si hoy es miercoles, arranca la semana el jueves y termina el miercoles (closed='right')
    weekly_returns = df[stock].resample('W-' + starting_day, closed='right').last().pct_change()

    current_week_return = weekly_returns.iloc[-1] #agarro % de la última actual semana
    last_13_weeks_returns = weekly_returns.iloc[-14:-1]  #últimas 13 sin contar la actual

    med_13weeks = last_13_weeks_returns.median()
    desvio_13weeks = last_13_weeks_returns.std()

    standarized = (current_week_return - med_13weeks) / (desvio_13weeks)
    return standarized

def get_standarized_monthly_return(df, stock):
    current_day_of_week = df[stock].index[-1].day_name()  # nombre de dia de semana
    starting_day = current_day_of_week[:3]  # tomo las primeras 3 letras

    #retornos semanales, y precios semanales en dataframes
    weekly_returns_prices = df[stock].resample('W-' + starting_day, closed='right').last()
    weekly_returns_pct = weekly_returns_prices.pct_change()

    monthly_returns_prices = weekly_returns_prices.iloc[::-1][0::4][::-1] #lo doy vuelta, selecciono cada 4 semanas y lo vuelvo a dar vuelta
    monthly_return_pct = monthly_returns_prices.pct_change() #misma pero con %
    last_month_return = monthly_return_pct.iloc[-1] #retorno del último mes

    med_mensual = monthly_return_pct.iloc[-13:-1].median() #media mensual
    desvio_semanal = weekly_returns_pct.iloc[-56:-4].std() #desvio semanal

    standarized = (last_month_return - med_mensual) / desvio_semanal*np.sqrt(4)
    return standarized
def get_standarized_trimestral_return(df, stock):
    current_day_of_week = df[stock].index[-1].day_name()  # nombre de dia de semana
    starting_day = current_day_of_week[:3]  # tomo las primeras 3 letras

    weekly_returns = df[stock].resample('W-' + starting_day, closed='right').last()
    weekly_returns_pct = df[stock].resample('W-' + starting_day, closed='right').last().pct_change()
    last_65_weeks_returns = weekly_returns_pct.iloc[-65:]
    last_13weeks_returns = weekly_returns.iloc[-1] / weekly_returns.iloc[-13] -1

    #med y ds de las últimas 65 semanas sin contar las últimas 13
    med = weekly_returns_pct.iloc[-65:-13].median()
    ds = weekly_returns_pct.iloc[-65:-13].std()

    #print(stock, last_13weeks_returns, med*13, ds*np.sqrt(13))

    standarized = (last_13weeks_returns - med*13) / ds * np.sqrt(13)
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
