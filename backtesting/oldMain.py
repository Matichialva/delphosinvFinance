import numpy as np
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
from matplotlib.backends.backend_pdf import PdfPages
import statistics
import math
import dataframe_image as dfi


def create_dataframe(ticker, period):
    '''given a ticker, download its data and return a dataframe with date'''
    ticker_data = yf.download(ticker, period=period)

    return ticker_data


def append_variables_for_signals(df, price_column, ma1, window1, ma2, window2):
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
    df['position'] = None  # add position column

    # specific strategy -> desp pasarla a función aparte
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

    # corro la señal un dia, ya que se comprará al día siguiente.
    df['operationDay'] = df['position'].shift(shifts)
    df['operationDay'] = leave_operating_days(df['operationDay'])

    return df


def leave_operating_days(column):
    '''given a column from a datarframe, only leave the first value
    when a sequence of repeated values is find, and turn those values to cero.
    Also indicate when you are buying, selling, or buyingANDselling.'''

    last_value = 0

    for i in range(200, len(column)):
        current_value = column.iloc[i]  # me paro en la posición actual
        if current_value == last_value:  # si es igual al valor anterior
            column = column.copy()
            column.iloc[i] = 0  # cero ya que no hay q operar
        else:
            # si estoy parado en una posición distinta a la anterior
            if (current_value == 0 and last_value == 1) or (
                    current_value == 0 and last_value == -1):  # si pase de 1->0 o -1 -> 0
                column = column.copy()
                column.iloc[i] = -11  # vendi
                last_value = current_value  # actualizo el nuevo último valor
            elif (current_value == -1 and last_value == 0) or (
                    current_value == 1 and last_value == 0):  # si pase de 0 -> -1 o 0->1
                column = column.copy()
                column.iloc[i] = 11  # compré
                last_value = current_value
            elif (current_value == -1 and last_value == 1) or (current_value == 1 and last_value == -1):
                column = column.copy()
                column.iloc[i] = 22  # compra y venta.
                last_value = current_value

    return column


def add_returns(df, price_column_name):
    df['ticker_returns'] = df[price_column_name].pct_change()

    return df


def add_strategy_returns_and_prices(df, price_column, ticker_returns_column, position_shifts, starting_day: 0,
                                    comision_entrada: 0, comision_salida: 0):
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

    previous_strategy_price = df[price_column].iloc[starting_day - 1]

    for index, row in df.iloc[starting_day:].iterrows():
        ticker_return = df.loc[index, ticker_returns_column]
        ticker_price = df.loc[index, price_column]

        position_shift = df.loc[index, 'positionShift']

        # armo strategy_returns dependiendo de si estoy comprado, vendido o en efectivo
        if (position_shift == 0):
            df.loc[index, 'strategy_returns'] = 0
        elif (position_shift == -1):
            df.loc[index, 'strategy_returns'] = ticker_return * -1
        elif (position_shift == 1):
            df.loc[index, 'strategy_returns'] = ticker_return

        strategy_return = df.loc[index, 'strategy_returns']

        # A REVISARRRRRRRRRRRRR -> tema comisión
        # armo strategy_prices dependiendo si estoy comprado o vendido, teniendo en cuenta la comisión
        # el precio anterior * el retorno de ese día (ya fue calculado según posición en el if anterior)
        if (df.loc[index, 'operationDay'] == 0):
            df.loc[index, 'strategy_prices'] = previous_strategy_price * (1 + strategy_return)
        elif (df.loc[index, 'operationDay'] == 11):
            df.loc[index, 'strategy_prices'] = previous_strategy_price * (1 + comision_entrada) * (1 + (strategy_return))
        elif (df.loc[index, 'operationDay'] == -11):
            df.loc[index, 'strategy_prices'] = previous_strategy_price * (1 - comision_salida) * (1 + (strategy_return))
        elif (df.loc[index, 'operationDay'] == 22):
            df.loc[index, 'strategy_prices'] = previous_strategy_price * (1 - comision_salida) * (1 + comision_entrada) * (1 + (strategy_return))

        previous_strategy_price = df.loc[index, 'strategy_prices']

    return df


def create_prices_graph(ticker_data, price_column, strategy_price_column, fechas, ax=None, first_ax = 0):
    if ax.any():
        ax[first_ax].plot(fechas, ticker_data[price_column], label='stock price')
        ax[first_ax].plot(fechas, ticker_data[strategy_price_column], label='strategy price')

        ax[first_ax].set_title('stock & strategy prices')
        #ax[first_ax].set_xlabel('Date')
        ax[first_ax].set_ylabel('prices')
        ax[first_ax].legend()

    else:
        plt.figure(figsize=(10, 6))
        plt.plot(fechas, ticker_data[price_column], label='stock price')
        plt.plot(fechas, ticker_data[strategy_price_column], label='strategy price')

        plt.title('stock & strategy prices')
        plt.xlabel('Date')
        plt.ylabel('prices')
        plt.legend()

        plt.savefig('pngStats/prices_graph.png')


def create_drawdown_graph(df, price_column, ax=None, first_ax=0):
    ticker_data = df.copy()
    ticker_data['previous peak'] = ticker_data[price_column].cummax()
    ticker_data['drawdown'] = (ticker_data[price_column] - ticker_data['previous peak']) / ticker_data[
        'previous peak'] * 100

    if ax is None:
        fig, ax = plt.subplots(2, 1, figsize=(10, 10), gridspec_kw={'height_ratios': [2, 1]})

    # Plot stock price and previous peak in the first subplot
    ax[first_ax].plot(ticker_data.index, ticker_data[price_column], label='Stock Price', color='dodgerblue')
    ax[first_ax].plot(ticker_data.index, ticker_data['previous peak'], label='Previous Peak', linestyle='--', color='blue')
    #ax[first_ax].set_xlabel('Date')
    ax[first_ax].set_ylabel('Price')
    ax[first_ax].set_title('Stock Price & Drawdown')
    ax[first_ax].legend()

    # Plot drawdown in the second subplot
    ax[first_ax+1].fill_between(ticker_data.index, 0, ticker_data['drawdown'],
                       where=ticker_data['drawdown'] < 0, color='salmon', alpha=0.3, label='Drawdown')
    #ax[first_ax+1].set_xlabel('Date')
    ax[first_ax+1].set_ylabel('Drawdown (%)')
    ax[first_ax+1].set_title('Stock Drawdown')
    ax[first_ax+1].legend()

    #plt.tight_layout()
    #plt.savefig('drawdown_graph.png')
    #plt.close()


def create_stats_df(df):
    index = ['periodo entero', 'comprado', 'en efectivo', 'vendido']
    columns = pd.MultiIndex.from_product(
        [['Activo', 'Estrategia', 'S&P-500'], ['Mediana', 'Media geo.', 'Media arit.', 'Desvio', 'Max', 'Min']])
    stats = pd.DataFrame(index=index, columns=columns)

    return stats


def media_geometrica(returns_column):
    tot_value = 1
    for value in returns_column:
        tot_value = tot_value * (1 + value)
    tot_value = (tot_value) ** (1 / len(returns_column)) - 1

    return tot_value


def calculate_stats(backtest_data, stats, tickerPrice, tickerReturn, stratPrice, stratReturn, sp500Price, sp500Return,
                    positionColumn):
    for periodo in ['periodo entero', 'comprado', 'en efectivo', 'vendido']:
        if periodo == 'periodo entero':
            period_dataframe = backtest_data.copy()
        elif periodo == 'comprado':
            period_dataframe = backtest_data[backtest_data[positionColumn] == 1]
        elif periodo == 'en efectivo':
            period_dataframe = backtest_data[backtest_data[positionColumn] == 0]
        elif periodo == 'vendido':
            period_dataframe = backtest_data[backtest_data[positionColumn] == -1]

        for strategy in ['Activo', 'Estrategia', 'S&P-500']:
            if strategy == 'Activo':
                price_column = period_dataframe[tickerPrice]
                returns_column = period_dataframe[tickerReturn]
            elif strategy == 'Estrategia':
                price_column = period_dataframe[stratPrice]
                returns_column = period_dataframe[stratReturn]
            elif strategy == 'S&P-500':
                price_column = period_dataframe[sp500Price]
                returns_column = period_dataframe[sp500Return]

            mediana = statistics.median(returns_column)
            arit_mean = statistics.mean(returns_column)
            geo_mean = media_geometrica(returns_column)
            stddev = statistics.stdev(returns_column)
            max_value = max(returns_column)
            min_value = min(returns_column)

            stats.loc[periodo, (strategy, 'Mediana')] = round(mediana * 100, 2)
            stats.loc[periodo, (strategy, 'Media arit.')] = round(arit_mean * 100, 2)
            stats.loc[periodo, (strategy, 'Media geo.')] = round(geo_mean * 100, 2)
            stats.loc[periodo, (strategy, 'Desvio')] = round(stddev * 100, 2)
            stats.loc[periodo, (strategy, 'Max')] = round(max_value * 100, 2)
            stats.loc[periodo, (strategy, 'Min')] = round(min_value * 100, 2)

    return stats

def calculate_subperiod_stats(backtest_data, stats, tickerPrice, tickerReturn, stratPrice, stratReturn, sp500Price, sp500Return, positionColumn):
    start_date = backtest_data.index[0]
    position = backtest_data[positionColumn][0]

    backtest_data['date'] = backtest_data.index
    backtest_data['next_date'] = backtest_data['date'].shift(-1)
    backtest_data['next_position'] = backtest_data[positionColumn].shift(-1)

    for idx, row in backtest_data.iterrows():
        current_date = idx
        current_position = row[positionColumn]

        if not pd.isnull(row['next_date']):
            next_position = row['next_position']
            next_date = row['next_date']

            if next_position != position:
                #slice dataframe from start_date to current_date
                sliced_df = backtest_data.loc[start_date:current_date] #df de la data solo en el subperíodo

                new_index_period = f"{start_date.strftime('%Y-%m-%d')}/{current_date.strftime('%Y-%m-%d')}"

                #add q days and position to stats
                days_passed = (current_date - start_date).days
                stats.loc[new_index_period, ('q days', '')] = days_passed
                stats.loc[new_index_period, ('position', '')] = position


                #add returns 30d, 60d, 90d, 180d, total to stats -> para cada strat
                add_returns_to_stats(new_index_period, sliced_df, sp500Price, sp500Return, stats, stratPrice,
                                     stratReturn, tickerPrice, tickerReturn)

                #change start_date and position for the new ones
                start_date = next_date
                position = next_position
        else:
            # slice dataframe from start_date to current_date
            sliced_df = backtest_data.loc[start_date:current_date]  # df de la data solo en el subperíodo

            new_index_period = f"{start_date.strftime('%Y-%m-%d')}/{current_date.strftime('%Y-%m-%d')}"

            # add q days and position to stats
            days_passed = (current_date - start_date).days
            stats.loc[new_index_period, ('q days', '')] = days_passed
            stats.loc[new_index_period, ('position', '')] = position

            # add returns 30d, 60d, 90d, 180d, total to stats -> para cada strat
            add_returns_to_stats(new_index_period, sliced_df, sp500Price, sp500Return, stats, stratPrice,
                                 stratReturn, tickerPrice, tickerReturn)

            # change start_date and position for the new ones
            start_date = next_date
            position = next_position


    #borrar las columnas next_date y next_position


    return stats


def add_returns_to_stats(new_index_period, sliced_df, sp500Price, sp500Return, stats, stratPrice, stratReturn,
                         tickerPrice, tickerReturn):
    for strategy in ['Activo', 'Estrategia', 'S&P-500']:
        if strategy == 'Activo':
            price_column = tickerPrice
            returns_column = tickerReturn
        elif strategy == 'Estrategia':
            price_column = stratPrice
            returns_column = stratReturn
        elif strategy == 'S&P-500':
            price_column = sp500Price
            returns_column = sp500Return

        day0 = sliced_df['date'].iloc[0]
        day30 = find_previous_closest_date(day0 + pd.Timedelta(days=30), sliced_df)
        day60 = find_previous_closest_date(day0 + pd.Timedelta(days=60), sliced_df)
        day90 = find_previous_closest_date(day0 + pd.Timedelta(days=90), sliced_df)
        day180 = find_previous_closest_date(day0 + pd.Timedelta(days=180), sliced_df)

        day0_price = sliced_df.loc[day0, price_column]
        day30_price = sliced_df.loc[day30, price_column]
        day60_price = sliced_df.loc[day60, price_column]
        day90_price = sliced_df.loc[day90, price_column]
        day180_price = sliced_df.loc[day180, price_column]
        last_day_price = sliced_df[price_column].iloc[-1]

        day30_return = (day30_price - day0_price) / day0_price
        day60_return = (day60_price - day0_price) / day0_price
        day90_return = (day90_price - day0_price) / day0_price
        day180_return = (day180_price - day0_price) / day0_price
        total_return = (last_day_price - day0_price) / day0_price

        stats.loc[new_index_period, (strategy, '%30d')] = day30_return
        stats.loc[new_index_period, (strategy, '%60d')] = day60_return
        stats.loc[new_index_period, (strategy, '%90d')] = day90_return
        stats.loc[new_index_period, (strategy, '%180d')] = day180_return
        stats.loc[new_index_period, (strategy, '%total')] = total_return


def add_sp500_returns_and_prices(df, sp500Ticker, period):
    sp500df = yf.download(sp500Ticker, period=period, auto_adjust=True)
    sp500df['sp500returns'] = sp500df['Close'].pct_change()
    sp500df.rename(columns={'Close': 'sp500price'}, inplace=True)

    df = pd.merge(df, sp500df[['sp500price', 'sp500returns']], left_index=True, right_index=True, how='left')

    return df

def create_subperiod_stats(ticker_data):
    columns = pd.MultiIndex.from_product(
        [['Activo', 'Estrategia', 'S&P-500'], ['%30d', '%60d', '%90d', '%180d', '%total']])
    stats = pd.DataFrame(columns=columns)
    stats.index.name = 'periods'
    return stats

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


def create_stats_for_each_subperiod(subperiod_stats):
    bought_stats = subperiod_stats[subperiod_stats['position'] == 1]
    cash_stats = subperiod_stats[subperiod_stats['position'] == 0]
    sold_stats = subperiod_stats[subperiod_stats['position'] == -1]

    bought_stats.to_excel('excelStats/bought_stats.xlsx')
    cash_stats.to_excel('excelStats/cashed_stats.xlsx')
    sold_stats.to_excel('excelStats/sold_stats.xlsx')

    return bought_stats, cash_stats, sold_stats


def main():
    ticker = "AAPL"
    period = '5y'

    #create ticker data's dataframe
    ticker_data = create_dataframe(ticker, period)

    #particular strategy
    ticker_data = append_variables_for_signals(ticker_data, 'Adj Close', 'MA20', 20, 'MA200', 200)
    ticker_data = delete_unuseful_columns(ticker_data, ['Close', 'Open', 'High', 'Low', 'Volume'])
    ticker_data = add_position_and_operationDay(ticker_data, 1)

    #add ticker returns / add strategy returns and prices given columns and particular position. / add sp500 returns and prices.
    ticker_data = add_returns(ticker_data, 'Adj Close')
    ticker_data = add_strategy_returns_and_prices(ticker_data, 'Adj Close', 'ticker_returns', 1, 202, 0, 0)
    ticker_data = add_sp500_returns_and_prices(ticker_data, "^SPX", period)

    #particular strategy-extra
    ticker_data = delete_first_x_rows(ticker_data, 201)

    #save database in excel file
    ticker_data.to_excel('excelStats/BacktestData.xlsx', index=True)

    #create general stats - excel
    general_stats = create_stats_df(ticker_data)
    general_stats = calculate_stats(ticker_data, general_stats, 'Adj Close', 'ticker_returns',
                            'strategy_prices', 'strategy_returns', 'sp500price',
                            'sp500returns', 'positionShift')

    general_stats.to_excel('excelStats/general_stats.xlsx', index=True)

    #create subperiod stats - excel
    subperiod_stats = create_subperiod_stats(ticker_data)
    subperiod_stats = calculate_subperiod_stats(ticker_data, subperiod_stats, 'Adj Close', 'ticker_returns', 'strategy_prices', 'strategy_returns', 'sp500price', 'sp500returns', 'positionShift')
    subperiod_stats.to_excel('excelStats/subperiod_stats.xlsx')

    #create each subperiod's stats - excel
    bought_stats, cash_stats, sold_stats = create_stats_for_each_subperiod(subperiod_stats)

    subperiods_rows = len(subperiod_stats)
    bought_rows = len(bought_stats)
    cash_rows = len(cash_stats)
    sold_rows = len(sold_stats)

    dfi.export(general_stats, 'pngStats/general_stats.png')
    dfi.export(bought_stats.drop(columns=['position']), 'pngStats/bought_stats.png')
    dfi.export(cash_stats.drop(columns=['position']), 'pngStats/cashed_stats.png')
    dfi.export(sold_stats.drop(columns=['position']), 'pngStats/sold_stats.png')


    #create informe with data & graphs.
    with PdfPages('backtestAnalysis.pdf') as pdf_pages:
        nrows=5
        ncols=1

        #create figure and axes to then add text and graphs
        fig, axs = plt.subplots(nrows, ncols, figsize = (15, 25))

        #add title
        plt.suptitle(f'Backtesting - {ticker} - {period}', fontsize=30, y=0.98)

        # create price plot of strategy and stock, and save it in png file.
        create_prices_graph(ticker_data, 'Adj Close', 'strategy_prices', ticker_data.index, ax=axs, first_ax=0)

        # create drawdown graph
        create_drawdown_graph(ticker_data, 'Adj Close', ax=axs, first_ax=1)

        #create general stats graph
        general_stats_image = plt.imread('pngStats/general_stats.png')
        axs[nrows-2].imshow(general_stats_image)
        axs[nrows-2].axis('off')

        #add text to the last axis
        axs[nrows-1].axis('off')
        axs[nrows-1].text(0.01, 0.90, f"cantidad de señales/períodos: {subperiods_rows}", fontsize=18)
        axs[nrows-1].text(0.01, 0.78, f"período analizado: {subperiods_rows}", fontsize=18)
        plt.text(0.01, 0.66, f"%comprado : {round(((bought_rows/subperiods_rows)*100), 1)} %", fontsize=18)
        plt.text(0.01, 0.54, f"%vendido : {round(((sold_rows/subperiods_rows)*100), 1)} %", fontsize=18)
        plt.text(0.01, 0.42, f"%cash : {round(((cash_rows/subperiods_rows)*100), 1)} %", fontsize=18)

        #save figure in pdf and then close it
        pdf_pages.savefig(fig)
        plt.close(fig)

        #page 2
        fig = plt.figure(figsize=(10, 10))
        bought_stats_image = plt.imread('pngStats/bought_stats.png')
        plt.imshow(bought_stats_image)
        plt.axis('off')
        plt.title('Bought Stats')
        pdf_pages.savefig(fig)
        plt.close(fig)

        #page 3
        fig = plt.figure(figsize=(10, 10))
        cashed_stats_image = plt.imread('pngStats/cashed_stats.png')
        plt.imshow(cashed_stats_image)
        plt.axis('off')
        plt.title('Cashed Stats')
        pdf_pages.savefig(fig)
        plt.close(fig)

        #page 4
        fig = plt.figure(figsize=(10, 10))
        sold_stats_image = plt.imread('pngStats/sold_stats.png')
        plt.imshow(sold_stats_image)
        plt.axis('off')
        plt.title('Sold Stats')
        pdf_pages.savefig(fig)
        plt.close(fig)




if __name__ == "__main__":
    main()
