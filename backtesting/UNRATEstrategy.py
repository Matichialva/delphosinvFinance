import pandas as pd
from fredapi import Fred

from eeuuFinance.backtesting.DataManager import DataManager


class UNRATEstrategy:
    def __init__(self, data):
        self.data = data
        self.fred = Fred(api_key='7605ba60cc0ee27eed45a2d9ed448e67')

    def compute_moving_average(self, price_column, window):
        self.data[f'MA{window}'] = self.data[price_column].rolling(window=window).mean()
        return self.data


    def add_unrate_column(self):
        #get unrate series from fred
        unrate_monthly = self.fred.get_series('UNRATE')

        #reindex the unrate series to a daily series.
        daily_dates = pd.date_range(start=unrate_monthly.index.min(), end=unrate_monthly.index.max(), freq='D')
        unrate_daily = unrate_monthly.reindex(daily_dates)

        #fill everyday with an unrate value
        unrate_daily = unrate_daily.fillna(method='ffill')
        unrate_daily = unrate_daily.reindex(self.data.index) #reindex to the data dataframe's dates.
        unrate_daily = unrate_daily.fillna(method='ffill')

        #add the column to the data dataframe
        self.data['unRate'] = unrate_daily

        return self.data

    def add_pm12m_unrate_column(self):
        #get unrate series from fred
        unrate_monthly = self.fred.get_series('UNRATE')
        pm12m = unrate_monthly.rolling(window=12).mean()

        #reindex the pm12m series to a daily series.
        daily_dates = pd.date_range(start=pm12m.index.min(), end=pm12m.index.max(), freq='D')
        pm12m_daily = pm12m.reindex(daily_dates)

        #fill everyday with an pm12m value
        pm12m_daily = pm12m_daily.fillna(method='ffill')
        pm12m_daily = pm12m_daily.reindex(self.data.index) #reindex to the data dataframe's dates.
        pm12m_daily = pm12m_daily.fillna(method='ffill')

        #add the column to the data dataframe
        self.data['pm12m'] = pm12m_daily

        return self.data

    def add_series_column(self, series_name, window=None, stat='mean'):
        # Get the series from FRED
        series_monthly = self.fred.get_series(series_name)

        # Calculate the rolling statistic if a window is provided
        if window:
            if stat == 'mean':
                series_monthly = series_monthly.rolling(window=window).mean()
            elif stat == 'min':
                series_monthly = series_monthly.rolling(window=window).min()
            # You can add more statistical calculations here as needed

        # Reindex the series to a daily series
        daily_dates = pd.date_range(start=series_monthly.index.min(), end=series_monthly.index.max(), freq='D')
        series_daily = series_monthly.reindex(daily_dates)

        # Fill every day with a value
        series_daily = series_daily.fillna(method='ffill')

        # Reindex to match the data DataFrame's dates
        series_daily = series_daily.reindex(self.data.index)

        # Forward fill to ensure all days have values
        series_daily = series_daily.fillna(method='ffill')

        # Determine the column name based on the statistic and window
        if window and stat == 'mean':
            column_name = f'pm{window}m'
        elif window and stat == 'min':
            column_name = f'min{window}m'
        else:
            column_name = series_name

        # Add the column to the data DataFrame
        self.data[column_name] = series_daily

        return self.data

    def generate_signals(self):
        '''method creates column called position, and based on a specific strategy,
        it  adds 1, 0, -1 to the column'''
        # Define logic to generate signals based on moving averages
        self.data['position'] = None  # add position column

        # specific strategy
        for index, row in self.data.iterrows():
            price = row['Adj Close']
            ma200 = row['MA200']
            unrate = row['unrate']
            unrate_pm12m = row['pm12m']
            position = -5

            if (price < ma200) and (unrate > unrate_pm12m):
                position = 0
            else:
                position = 1

            self.data.loc[index, 'position'] = position
        return self.data

    def generate_columns_needed_and_add_position_column(self):
        self.add_series_column('unrate')
        self.add_series_column('unrate', window=12, stat='mean')
        self.add_series_column('unrate', window=12, stat='min')
        self.compute_moving_average('Adj Close', 200)
        self.generate_signals()
        return self.data


if __name__ == '__main__':
    ticker = "^SPX"
    period = 'max'

    # fetches and processes data
    data_manager = DataManager(ticker, period)
    data = data_manager.fetch_data()
    data = data_manager.preprocess_data(remove_columns=['Close', 'Open', 'High', 'Low', 'Volume'])

    unrate = UNRATEstrategy(data)
    data = unrate.add_series_column('unrate')
    data = unrate.add_series_column('unrate', window=12, stat='mean')
    data = unrate.add_series_column('unrate', window=12, stat='min')
    data = unrate.compute_moving_average('Adj Close',200)
    data = unrate.generate_signals()
    data.to_excel('excelStats/unrateBacktesting.xlsx', index=True)

