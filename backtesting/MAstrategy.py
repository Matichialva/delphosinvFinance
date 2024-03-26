class MAstrategy:
    def __init__(self, data):
        self.data = data

    def compute_moving_averages(self, price_column, short_window, long_window):
        self.data[f'MA{short_window}'] = self.data[price_column].rolling(window=short_window).mean()
        self.data[f'MA{long_window}'] = self.data[price_column].rolling(window=long_window).mean()
        return self.data

    def generate_signals_MA20_MA200(self):
        '''method creates column called position, and based on a specific strategy,
        it  adds 1, 0, -1 to the column'''
        # Define logic to generate signals based on moving averages
        self.data['position'] = None  # add position column

        # specific strategy
        for index, row in self.data.iterrows():
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

            self.data.loc[index, 'position'] = position
        return self.data

    def generate_columns_needed_and_add_position_column(self, price_column, short_window, long_window):
        self.compute_moving_averages(price_column, short_window, long_window)
        self.generate_signals_MA20_MA200()
        return self.data
