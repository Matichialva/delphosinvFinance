import pandas as pd
import statistics
import dataframe_image as dfi
class StatisticalAnalyzer:
    def __init__(self, data):
        self.data = data

    def create_stats(self):
        index = ['periodo entero', 'comprado', 'en efectivo', 'vendido']
        columns = pd.MultiIndex.from_product(
            [['Activo', 'Estrategia', 'S&P-500'], ['Mediana', 'Media geo.', 'Media arit.', 'Desvio', 'Max', 'Min']])
        stats = pd.DataFrame(index=index, columns=columns)

        return stats

    def create_subperiod_stats(self):
        columns = pd.MultiIndex.from_product(
            [['Activo', 'Estrategia', 'S&P-500'], ['%30d', '%60d', '%90d', '%180d', '%total']])
        stats = pd.DataFrame(columns=columns)
        stats.index.name = 'periods'
        return stats

    def calculate_stats(self, stats, tickerPrice, tickerReturn, stratPrice, stratReturn, sp500Price,
                        sp500Return, positionColumn):
        for periodo in ['periodo entero', 'comprado', 'en efectivo', 'vendido']:
            if periodo == 'periodo entero':
                period_dataframe = self.data.copy()
            elif periodo == 'comprado':
                period_dataframe = self.data[self.data[positionColumn] == 1]
            elif periodo == 'en efectivo':
                period_dataframe = self.data[self.data[positionColumn] == 0]
            elif periodo == 'vendido':
                period_dataframe = self.data[self.data[positionColumn] == -1]

            for strategy in ['Activo', 'Estrategia', 'S&P-500']:
                if strategy == 'Activo':
                    returns_column = period_dataframe[tickerReturn]
                elif strategy == 'Estrategia':
                    returns_column = period_dataframe[stratReturn]
                elif strategy == 'S&P-500':
                    returns_column = period_dataframe[sp500Return]

                mediana = statistics.median(returns_column)
                arit_mean = statistics.mean(returns_column)
                geo_mean = self.calculate_media_geometrica(returns_column)
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

    def calculate_media_geometrica(self, returns_column):
        tot_value = 1
        for value in returns_column:
            tot_value = tot_value * (1 + value)
        tot_value = (tot_value) ** (1 / len(returns_column)) - 1

        return tot_value

    def generate_general_stats(self):
        # Your existing logic to create and calculate general stats
        general_stats = self.create_stats()
        general_stats = self.calculate_stats(general_stats, 'Adj Close', 'ticker_returns',
                                             'strategy_prices', 'strategy_returns', 'sp500price',
                                             'sp500returns', 'shiftedPosition')
        general_stats.to_excel('excelStats/general_stats.xlsx', index=True)
        dfi.export(general_stats, 'pngStats/general_stats.png', max_rows=-1)
        return general_stats

    def generate_subperiod_stats(self):
        # Your existing logic to create and calculate subperiod stats
        subperiod_stats = self.create_subperiod_stats()
        subperiod_stats = self.calculate_subperiod_stats(self.data, subperiod_stats, 'Adj Close', 'ticker_returns',
                                                         'strategy_prices', 'strategy_returns', 'sp500price',
                                                         'sp500returns',
                                                         'shiftedPosition')
        subperiod_stats.to_excel('excelStats/subperiod_stats.xlsx')
        return subperiod_stats

    def calculate_subperiod_stats(self, backtest_data, stats, tickerPrice, tickerReturn, stratPrice, stratReturn,
                                  sp500Price,
                                  sp500Return, positionColumn):
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
                    # slice dataframe from start_date to current_date
                    sliced_df = backtest_data.loc[start_date:current_date]  # df de la data solo en el subperíodo

                    new_index_period = f"{start_date.strftime('%Y-%m-%d')}/{current_date.strftime('%Y-%m-%d')}"

                    # add q days and position to stats
                    days_passed = (current_date - start_date).days
                    stats.loc[new_index_period, ('q days', '')] = days_passed
                    stats.loc[new_index_period, ('position', '')] = position

                    # add returns 30d, 60d, 90d, 180d, total to stats -> para cada strat
                    self.add_returns_to_stats(new_index_period, sliced_df, sp500Price, sp500Return, stats, stratPrice,
                                         stratReturn, tickerPrice, tickerReturn)

                    # change start_date and position for the new ones
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
                self.add_returns_to_stats(new_index_period, sliced_df, sp500Price, sp500Return, stats, stratPrice,
                                          stratReturn, tickerPrice, tickerReturn)

                # change start_date and position for the new ones
                start_date = next_date
                position = next_position

        # borrar las columnas next_date y next_position

        return stats

    def find_previous_closest_date(self, current_date, df):
        closest_date = None
        min_difference = float('inf')  # infinito

        for date in df.index:
            if date > current_date:
                continue

            difference = abs((date - current_date).total_seconds())
            if difference < min_difference:
                min_difference = difference
                closest_date = date

        return closest_date

    def add_returns_to_stats(self, new_index_period, sliced_df, sp500Price, sp500Return, stats, stratPrice, stratReturn,
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
            day30 = self.find_previous_closest_date(day0 + pd.Timedelta(days=30), sliced_df)
            day60 = self.find_previous_closest_date(day0 + pd.Timedelta(days=60), sliced_df)
            day90 = self.find_previous_closest_date(day0 + pd.Timedelta(days=90), sliced_df)
            day180 = self.find_previous_closest_date(day0 + pd.Timedelta(days=180), sliced_df)

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

    def create_stats_for_each_subperiod(self, subperiod_stats):
        bought_stats = subperiod_stats[subperiod_stats['position'] == 1]
        cash_stats = subperiod_stats[subperiod_stats['position'] == 0]
        sold_stats = subperiod_stats[subperiod_stats['position'] == -1]

        bought_stats.to_excel('excelStats/bought_stats.xlsx')
        cash_stats.to_excel('excelStats/cashed_stats.xlsx')
        sold_stats.to_excel('excelStats/sold_stats.xlsx')

        return bought_stats, cash_stats, sold_stats

    def export_subperiod_stats_images(self, subperiod_stats):
        bought_stats, cash_stats, sold_stats = self.create_stats_for_each_subperiod(subperiod_stats)
        dfi.export(bought_stats.drop(columns=['position']), 'pngStats/bought_stats.png')
        dfi.export(cash_stats.drop(columns=['position']), 'pngStats/cashed_stats.png')
        dfi.export(sold_stats.drop(columns=['position']), 'pngStats/sold_stats.png')
