import pandas as pd
import yfinance as yf

class SignalGenerator:
    def __init__(self, data):
        self.data = data

    def shift_position_x_days(self, shifts, shifted_pos):
        '''given amount of shifts for the position in the case that the position
        is wanted to be changed some days after the signal is given. creates
        column called shiftedPosition'''
        self.data[shifted_pos] = self.data['position'].shift(shifts)
        return self.data

    def generate_operation_day(self, pos_col):
        '''given a column from a dataframe, only leave the first value
            when a sequence of repeated values is find, and turn those values to cero.
            Also indicate when you are buying (11), selling (-11), or buyingANDselling (22).'''

        self.data['operationDay'] = self.data[pos_col].copy()
        operation_col = self.data['operationDay']

        last_value = 0

        for i in range(200, len(operation_col)):
            current_value = operation_col.iloc[i]  # me paro en la posición actual
            if current_value == last_value:  # si es igual al valor anterior
                operation_col = operation_col.copy()
                operation_col.iloc[i] = 0  # cero ya que no hay q operar
            else:
                # si estoy parado en una posición distinta a la anterior
                if (current_value == 0 and last_value == 1) or (
                        current_value == 0 and last_value == -1):  # si pase de 1->0 o -1 -> 0
                    operation_col = operation_col.copy()
                    operation_col.iloc[i] = -11  # vendi
                    last_value = current_value  # actualizo el nuevo último valor
                elif (current_value == -1 and last_value == 0) or (
                        current_value == 1 and last_value == 0):  # si pase de 0 -> -1 o 0->1
                    operation_col = operation_col.copy()
                    operation_col.iloc[i] = 11  # compré
                    last_value = current_value
                elif (current_value == -1 and last_value == 1) or (current_value == 1 and last_value == -1):
                    operation_col = operation_col.copy()
                    operation_col.iloc[i] = 22  # compra y venta.
                    last_value = current_value

        self.data['operationDay'] = operation_col
        return self.data

    def add_returns_column(self, price_col, return_col):
        self.data[return_col] = self.data[price_col].pct_change()

        return self.data

    def add_strategy_price_and_returns(self, price_column, ticker_returns_column, pos_col, starting_day: 0,
                                       comision_entrada: 0, comision_salida: 0):
        self.data['strategy_returns'] = self.data[ticker_returns_column]
        self.data['strategy_prices'] = self.data[price_column]

        previous_strategy_price = self.data[price_column].iloc[starting_day]

        for index, row in self.data.iloc[starting_day:].iterrows():
            ticker_return = self.data.loc[index, ticker_returns_column]
            ticker_price = self.data.loc[index, price_column]

            current_pos = self.data.loc[index, pos_col]

            # armo strategy_returns dependiendo de si estoy comprado, vendido o en efectivo
            if (current_pos == 0):
                self.data.loc[index, 'strategy_returns'] = 0
            elif (current_pos == -1):
                self.data.loc[index, 'strategy_returns'] = ticker_return * -1
            elif (current_pos == 1):
                self.data.loc[index, 'strategy_returns'] = ticker_return

            strategy_return = self.data.loc[index, 'strategy_returns']

            # A REVISARRRRRRRRRRRRR -> tema comisión
            # armo strategy_prices dependiendo si estoy comprado o vendido, teniendo en cuenta la comisión
            # el precio anterior * el retorno de ese día (ya fue calculado según posición en el if anterior)
            if (self.data.loc[index, 'operationDay'] == 0):
                self.data.loc[index, 'strategy_prices'] = previous_strategy_price * (1 + strategy_return)
            elif (self.data.loc[index, 'operationDay'] == 11):
                self.data.loc[index, 'strategy_prices'] = previous_strategy_price * (1 + comision_entrada) * (
                            1 + (strategy_return))
            elif (self.data.loc[index, 'operationDay'] == -11):
                self.data.loc[index, 'strategy_prices'] = previous_strategy_price * (1 - comision_salida) * (
                            1 + (strategy_return))
            elif (self.data.loc[index, 'operationDay'] == 22):
                self.data.loc[index, 'strategy_prices'] = previous_strategy_price * (1 - comision_salida) * (
                        1 + comision_entrada) * (1 + (strategy_return))

            previous_strategy_price = self.data.loc[index, 'strategy_prices']

        return self.data

    def add_sp500_price_and_returns(self, sp500Ticker, period):
        sp500df = yf.download(sp500Ticker, period=period, auto_adjust=True)
        sp500df['sp500returns'] = sp500df['Close'].pct_change()
        sp500df.rename(columns={'Close': 'sp500price'}, inplace=True)
        self.data = pd.merge(self.data, sp500df[['sp500price', 'sp500returns']], left_index=True, right_index=True,
                             how='left')
        return self.data

    def delete_starting_rows(self, x):
        self.data = self.data.drop(self.data.index[:x])
        return self.data