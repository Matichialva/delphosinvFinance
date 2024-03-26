import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
class ReportGenerator:
    def __init__(self, data, ticker, period, subperiod_stats, general_stats_path, bought_stats_path,
                 cashed_stats_path, sold_stats_path):
        self.data = data
        self.ticker = ticker
        self.period = period
        self.subperiod_stats = subperiod_stats
        self.general_stats_path = general_stats_path
        self.bought_stats_path = bought_stats_path
        self.cashed_stats_path = cashed_stats_path
        self.sold_stats_path = sold_stats_path

    def create_prices_graph(self, price_column, strategy_price_column, ax=None, first_ax = 0):
        if ax.any():
            ax[first_ax].plot(self.data.index, self.data[price_column], label='stock price')
            ax[first_ax].plot(self.data.index, self.data[strategy_price_column], label='strategy price')

            ax[first_ax].set_title('stock & strategy prices')
            # ax[first_ax].set_xlabel('Date')
            ax[first_ax].set_ylabel('prices')
            ax[first_ax].legend()

        else:
            plt.figure(figsize=(10, 6))
            plt.plot(self.data.index, self.data[price_column], label='stock price')
            plt.plot(self.data.index, self.data[strategy_price_column], label='strategy price')

            plt.title('stock & strategy prices')
            plt.xlabel('Date')
            plt.ylabel('prices')
            plt.legend()

            plt.savefig('pngStats/prices_graph.png')

    def create_drawdown_graph(self, price_column, ax=None, first_ax=0):
        ticker_data = self.data.copy()
        ticker_data['previous peak'] = ticker_data[price_column].cummax()
        ticker_data['drawdown'] = (ticker_data[price_column] - ticker_data['previous peak']) / ticker_data['previous peak'] * 100

        if ax is None:
            fig, ax = plt.subplots(2, 1, figsize=(10, 10), gridspec_kw={'height_ratios': [2, 1]})

        # Plot stock price and previous peak in the first subplot
        ax[first_ax].plot(ticker_data.index, ticker_data[price_column], label='Stock Price', color='dodgerblue')
        ax[first_ax].plot(ticker_data.index, ticker_data['previous peak'], label='Previous Peak', linestyle='--',
                          color='blue')
        # ax[first_ax].set_xlabel('Date')
        ax[first_ax].set_ylabel('Price')
        ax[first_ax].set_title('Stock Price & Drawdown')
        ax[first_ax].legend()

        # Plot drawdown in the second subplot
        ax[first_ax + 1].fill_between(ticker_data.index, 0, ticker_data['drawdown'],
                                      where=ticker_data['drawdown'] < 0, color='salmon', alpha=0.3, label='Drawdown')
        # ax[first_ax+1].set_xlabel('Date')
        ax[first_ax + 1].set_ylabel('Drawdown (%)')
        ax[first_ax + 1].set_title('Stock Drawdown')
        ax[first_ax + 1].legend()

        # plt.tight_layout()
        # plt.savefig('drawdown_graph.png')
        # plt.close()


    def add_general_stats(self, ax):
        image = plt.imread(self.general_stats_path)
        ax.imshow(image)
        ax.axis('off')

    def add_text_statistics(self, ax, subperiods_rows, bought_rows, cash_rows, sold_rows, trading_days, bought_days, cash_days, sold_days):

        ax.axis('off')
        ax.text(0.01, 0.90, f"cantidad de señales/períodos: {subperiods_rows}", fontsize=18)
        ax.text(0.01, 0.78, f"período analizado: {self.period}", fontsize=18)
        #plt.axis('off')
        plt.text(0.01, 0.66, f"períodos comprado : {bought_rows}, tiempo comprado : {round(((bought_days / trading_days) * 100), 1)}%", fontsize=18)
        plt.text(0.01, 0.54, f"períodos vendido : {sold_rows}, tiempo vendido : {round(((sold_days / trading_days) * 100), 1)}%", fontsize=18)
        plt.text(0.01, 0.42, f"períodos en cash : {cash_rows}, tiempo en cash : {round(((cash_days / trading_days) * 100), 1)}%", fontsize=18)

    def generate_report(self):
        with PdfPages('backtestAnalysis.pdf') as pdf_pages:
            nrows = 5
            ncols = 1
            fig, axs = plt.subplots(nrows, ncols, figsize=(15, 25))
            plt.suptitle(f'Backtesting - {self.ticker} - {self.period}', fontsize=30, y=0.98)

            self.create_prices_graph('Adj Close', 'strategy_prices', ax=axs, first_ax=0)
            self.create_drawdown_graph('Adj Close', axs, 1)
            self.add_general_stats(axs[3])

            subperiods_rows = len(self.subperiod_stats)
            bought_rows = len(self.subperiod_stats[self.subperiod_stats['position'] == 1])
            cash_rows = len(self.subperiod_stats[self.subperiod_stats['position'] == 0])
            sold_rows = len(self.subperiod_stats[self.subperiod_stats['position'] == -1])

            trading_days = len(self.data)
            bought_days = len(self.data[self.data['position'] == 1])
            cash_days = len(self.data[self.data['position'] == 0])
            sold_days = len(self.data[self.data['position'] == -1])
            self.add_text_statistics(axs[4], subperiods_rows, bought_rows, cash_rows, sold_rows, trading_days, bought_days, cash_days, sold_days)

            pdf_pages.savefig(fig)
            plt.close(fig)

            # Add additional pages for bought, cashed, and sold stats
            for stats_path in [self.bought_stats_path, self.cashed_stats_path, self.sold_stats_path]:
                fig = plt.figure(figsize=(40, 40))
                image = plt.imread(stats_path)
                plt.imshow(image)
                plt.axis('off')
                plt.title(f'{stats_path.split("/")[1].split("_")[0].capitalize()} Stats')
                pdf_pages.savefig(fig)
                plt.close(fig)