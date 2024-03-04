import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
from matplotlib.backends.backend_pdf import PdfPages
import statistics
import math


def create_dataframe(ticker):
    '''given a ticker, download its data and return a dataframe with date'''
    ticker_data = yf.download(ticker, period='5y')

    return ticker_data

def append_variables_for_signals(df, price_column,ma1, window1, ma2, window2):
    df[ma1] = df[price_column].rolling(window=window1).mean()
    df[ma2] = df[price_column].rolling(window=window2).mean()
    return df

def delete_unuseful_columns(df, columnas_no_queridas):
    df = df.drop(columns=columnas_no_queridas)
    return df

def delete_first_x_rows(df, x):
    df = df.drop(df.index[:x])
    return df

def add_position_and_operationDay(df, shifts):
    df['position'] = None #add position column

    #specific strategy -> desp pasarla a función aparte
    for index, row in df.iterrows():
        price = row['Adj Close']
        ma20 = row['MA20']
        ma200 = row['MA200']
        position = -5

        if price < ma20:
            position = -1
        elif ma20 <= price < ma200:
            position = 0
        elif price >= ma200:
            position = 1

        df.loc[index, 'position'] = position

    #corro la señal un dia, ya que se comprará al día siguiente.
    df['operationDay'] = df['position'].shift(shifts)
    df['operationDay'] = leave_operating_days(df['operationDay'])

    return df

def leave_operating_days(column):
    '''given a column from a datarframe, only leave the first value
    when a sequence of repeated values is find, and turn those values to cero.
    Also indicate when you are buying, selling, or buyingANDselling.'''

    last_value = 0

    for i in range(200, len(column)):
        current_value = column.iloc[i] #me paro en la posición actual
        if current_value == last_value: #si es igual al valor anterior
            column = column.copy()
            column.iloc[i] = 0 #cero ya que no hay q operar
        else:
            #si estoy parado en una posición distinta a la anterior
            if (current_value == 0 and last_value == 1) or (current_value == 0 and last_value == -1): #si pase de 1->0 o -1 -> 0
                column = column.copy()
                column.iloc[i] = -11 #vendi
                last_value = current_value #actualizo el nuevo último valor
            elif (current_value == -1 and last_value == 0) or (current_value == 1 and last_value == 0):#si pase de 0 -> -1 o 0->1
                column = column.copy()
                column.iloc[i] = 11 #compré
                last_value = current_value
            elif (current_value == -1 and last_value == 1) or (current_value == 1 and last_value == -1):
                column = column.copy()
                column.iloc[i] = 22 #compra y venta.
                last_value = current_value

    return column


def add_returns(df, price_column_name):
    df['ticker_returns'] = df[price_column_name].pct_change()

    return df

def add_strategy_returns_and_prices(df, price_column, ticker_returns_column, position_shifts, starting_day:0, comision_entrada:0, comision_salida:0):
    '''add the returns of the strategy as a column, and the prices
    that the strategy is following column.
    df: dataframe to work ok
    price_column: name of price column
    ticker_returns_column: name of returns column
    position_shifts: quantity of shifts -> days after the signal when it will be operated
    starting_day: first day to start taking prices
    '''
    df['positionShift'] = df['position'].shift(position_shifts)
    df['strategy_returns'] = df[ticker_returns_column]
    df['strategy_prices'] = df[price_column]


    previous_strategy_price = df[price_column].iloc[starting_day -1]

    for index, row in df.iloc[starting_day:].iterrows():
        ticker_return = df.loc[index, ticker_returns_column]
        ticker_price = df.loc[index, price_column]

        position_shift = df.loc[index, 'positionShift']

        #armo strategy_returns dependiendo de si estoy comprado, vendido o en efectivo
        if (position_shift == 0):
            df.loc[index, 'strategy_returns'] = 0
        elif (position_shift == -1):
            df.loc[index, 'strategy_returns'] = ticker_return * -1
        elif (position_shift == 1):
            df.loc[index, 'strategy_returns'] = ticker_return

        strategy_return = df.loc[index, 'strategy_returns']

        #A REVISARRRRRRRRRRRRR -> tema comisión
        #armo strategy_prices dependiendo si estoy comprado o vendido, teniendo en cuenta la comisión
        #el precio anterior * el retorno de ese día (ya fue calculado según posición en el if anterior)
        if (df.loc[index, 'operationDay'] == 0):
            df.loc[index, 'strategy_prices'] = previous_strategy_price * (1+strategy_return)
        elif (df.loc[index, 'operationDay'] == 11):
            df.loc[index, 'strategy_prices'] = previous_strategy_price * (1+comision_entrada) * (1+(strategy_return))
        elif (df.loc[index, 'operationDay'] == -11):
            df.loc[index, 'strategy_prices'] = previous_strategy_price * (1-comision_salida) * (1+(strategy_return))
        elif (df.loc[index, 'operationDay'] == 22):
            df.loc[index, 'strategy_prices'] = previous_strategy_price * (1-comision_salida) * (1+comision_entrada) * (1+(strategy_return))




        previous_strategy_price = df.loc[index, 'strategy_prices']


    return df

def create_prices_graph(ticker_data, price_column, strategy_price_column, fechas):
    plt.figure(figsize=(10, 6))
    plt.plot(fechas, ticker_data[price_column], label='stock price')
    plt.plot(fechas, ticker_data[strategy_price_column], label='strategy price')

    plt.title('stock & strategy prices')
    plt.xlabel('Date')
    plt.ylabel('prices')
    plt.legend()

    plt.savefig('prices_graph.png')


def create_stats_df(df):
    index = ['periodo entero', 'comprado', 'en efectivo', 'vendido']
    columns = pd.MultiIndex.from_product(
        [['Activo', 'Estrategia'], ['Mediana', 'Media geo.', 'Media arit.', 'Desvio', 'Max', 'Min']])
    stats = pd.DataFrame(index=index, columns=columns)

    return stats

def media_geometrica(returns_column):
    tot_value = 1
    for value in returns_column:
        tot_value = tot_value * (1+value)
    tot_value = (tot_value)**(1/len(returns_column)) - 1

    return tot_value

def calculate_stats(backtest_data, stats, tickerPrice, tickerReturn, stratPrice, stratReturn):

    for strategy in ['Activo', 'Estrategia']:

        if strategy == 'Activo':
            price_column = backtest_data[tickerPrice]
            returns_column = backtest_data[tickerReturn]
        elif strategy == 'Estrategia':
            price_column = backtest_data[stratPrice]
            returns_column = backtest_data[stratReturn]


        mediana = statistics.median(returns_column)
        arit_mean = statistics.mean(returns_column)
        geo_mean = media_geometrica(returns_column)
        stddev = statistics.stdev(returns_column)
        max_value = max(returns_column)
        min_value = min(returns_column)

        stats.loc['periodo entero', (strategy, 'Mediana')] = round(mediana *100, 2)
        stats.loc['periodo entero', (strategy, 'Media arit.')] = round(arit_mean *100, 2)
        stats.loc['periodo entero', (strategy, 'Media geo.')] = round(geo_mean *100, 2)
        stats.loc['periodo entero', (strategy, 'Desvio')] = round(stddev *100, 2)
        stats.loc['periodo entero', (strategy, 'Max')] = round(max_value *100, 2)
        stats.loc['periodo entero', (strategy, 'Min')] = round(min_value *100, 2)


    return stats



def main():
    ticker = "^SPX"
    ticker_data = create_dataframe(ticker)
    ticker_data = append_variables_for_signals(ticker_data, 'Adj Close','MA20', 20, 'MA200', 200)
    ticker_data = delete_unuseful_columns(ticker_data, ['Close','Open', 'High', 'Low', 'Volume'])
    ticker_data = add_position_and_operationDay(ticker_data, 1)
    ticker_data = add_returns(ticker_data, 'Adj Close')
    ticker_data = add_strategy_returns_and_prices(ticker_data, 'Adj Close', 'ticker_returns', 1, 202, 0, 0)

    ticker_data = delete_first_x_rows(ticker_data, 201)
    ticker_data.to_excel('sp500Backtest.xlsx', index=True)

    #create price plot of strategy and stock, and save it in png file.
    create_prices_graph(ticker_data, 'Adj Close', 'strategy_prices', ticker_data.index)

    stats = create_stats_df(ticker_data)
    stats = calculate_stats(ticker_data, stats, 'Adj Close', 'ticker_returns', 'strategy_prices', 'strategy_returns')
    stats.to_excel('stats.xlsx', index=True)

if __name__ == "__main__":
    main()