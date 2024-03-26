from eeuuFinance.backtesting.DataManager import DataManager
from eeuuFinance.backtesting.MAstrategy import MAstrategy
from eeuuFinance.backtesting.ReportGenerator import ReportGenerator
from eeuuFinance.backtesting.SignalGenerator import SignalGenerator
from eeuuFinance.backtesting.StatisticalAnalyzer import StatisticalAnalyzer
from eeuuFinance.backtesting.UNRATEstrategy import UNRATEstrategy


def main():
    ticker = "^SPX"
    period = 'max'

    #fetches and processes data
    data_manager = DataManager(ticker, period)
    data = data_manager.fetch_data()
    data = data_manager.preprocess_data(remove_columns=['Close', 'Open', 'High', 'Low', 'Volume'])

    #add signal generator and strategy columns.
    strategy = UNRATEstrategy(data)
    data = strategy.generate_columns_needed_and_add_position_column()

    signal_generator = SignalGenerator(data)
    data = signal_generator.shift_position_x_days(1, 'shiftedPosition')
    data = signal_generator.generate_operation_day('shiftedPosition')
    data = signal_generator.add_returns_column('Adj Close', 'ticker_returns')
    data = signal_generator.add_strategy_price_and_returns('Adj Close', 'ticker_returns', 'shiftedPosition', 201, 0, 0)
    data = signal_generator.add_sp500_price_and_returns("^SPX", period)
    data = signal_generator.delete_starting_rows(5230)

    data.to_excel('excelStats/BacktestData.xlsx', index=True)

    #given the data, analyzer analyzes the data and creates stats dataframes.
    analyzer = StatisticalAnalyzer(data)
    general_stats = analyzer.generate_general_stats()
    subperiod_stats = analyzer.generate_subperiod_stats()
    analyzer.export_subperiod_stats_images(subperiod_stats)

    #report generator generates pdf report
    report_generator = ReportGenerator(data=data,
        ticker=ticker,
        period=period,
        subperiod_stats=subperiod_stats,
        general_stats_path="pngStats/general_stats.png",
        bought_stats_path="pngStats/bought_stats.png",
        cashed_stats_path="pngStats/cashed_stats.png",
        sold_stats_path="pngStats/sold_stats.png")
    report_generator.generate_report()


if __name__ == "__main__":
    main()
