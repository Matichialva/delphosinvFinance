import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import mplfinance as mpf
import talib
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime, timedelta
import os
import seaborn as sns


#######################drive#####################################33
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials

# Get the path of the current script
script_path = os.path.realpath(__file__)

# Change the working directory to the script's directory
os.chdir(os.path.dirname(script_path))

def upload_pdf_to_google_drive(file_path, mime_type):
    '''sube a google drive el archivo encontrado en el filepath que se pasa.'''
    #antes fue necesario 'enable' google drive api dado un projecto creado, luego cree un service account(bot para autenticar) y le di acceso de editor al folder en el drive.

    #credenciales guardadas de la service account(bot q lleva acabo la authentication), json fue descargado de console.cloud.google
    credentials = ServiceAccountCredentials.from_json_keyfile_name("delphosdatascience-1956c0e4959e.json", ["https://www.googleapis.com/auth/drive"])

    #realizo la authentication con esas credenciales
    gauth = GoogleAuth()
    gauth.credentials = credentials

    #conecto a google drive con la autenticación.
    drive = GoogleDrive(gauth)

    folder_id = '1yDcZ1BdNQ6bPkicsz2jJBm5Vr7OgabIx'


    existing_files = drive.ListFile({'q': f"'{folder_id}' in parents and title contains '{os.path.basename(file_path)}' and trashed=false"}).GetList()
    for existing_file in existing_files:
        existing_file.Trash()


    #creo un file con la data del excel guardado, y con el id del folder dentro del drive
    file_drive = drive.CreateFile({'title': os.path.basename(file_path),
                                   'mimeType': mime_type,
                                   'parents': [{'id': folder_id}]})
    file_drive.SetContentFile(file_path)
    file_drive.Upload()

def download_from_google_drive(destination_path):
    '''Descarga un archivo de Google Drive.'''
    # credenciales guardadas de la service account(bot q lleva acabo la authentication), json fue descargado de console.cloud.google
    credentials = ServiceAccountCredentials.from_json_keyfile_name("delphosdatascience-1956c0e4959e.json",
                                                                   ["https://www.googleapis.com/auth/drive"])

    # realizo la authentication con esas credenciales
    gauth = GoogleAuth()
    gauth.credentials = credentials

    # Conexión a Google Drive
    drive = GoogleDrive(gauth)

    # ID del archivo en Google Drive
    file_id = '1yoc6pcRjmOnT-iI3Vr4xcGpdOHc7IGfi'

    # Descarga del archivo
    file_drive = drive.CreateFile({'id': file_id})
    file_drive.GetContentFile(destination_path)


def fetch_ticker_data(ticker, start_time):
    ticker_data = yf.download(ticker, start= start_time, auto_adjust=True) #adjust by dividends/stocksplits
    return ticker_data

def cleaning_dataframe(df):
    '''clean the dataframe'''
    df.sort_index(ascending=True, inplace=True) #lo dejo sorteado con la última fecha abajo.
    df.index.name = "Date" #index column llamada "Date"
    df.ffill(inplace=True) #relleno los vacios con el valor del de arriba
    df.dropna(how="all", inplace=True) #si hay filas completamente vacias, funalas
    df.index = df.index.strftime("%Y-%m-%d")
    df.index = pd.to_datetime(df.index)

    return df

def calculate_mama_fama_daily(data, fast=0.25, slow=0.05):
    mama, fama = talib.MAMA(data['Close'], fastlimit=fast, slowlimit=slow)
    return pd.Series(mama, index=data.index), pd.Series(fama, index=data.index)

def calculate_mama_fama_week(data, fast=0.25, slow=0.05):
    # Convert the daily MAMA and FAMA series to a DataFrame with the original index
    # Weekly calculation

    data['MAMAweeks'] = np.nan
    data['FAMAweeks'] = np.nan


    for date in data.index:
        data_weekly = data[:date].resample('W-Fri').last()
        mama, fama = talib.MAMA(data_weekly['Close'], fastlimit=fast, slowlimit=slow)
        # Convert the weekly MAMA and FAMA series to a DataFrame with the original index
        data.loc[date, 'MAMAweeks'] = mama[-1]
        data.loc[date, 'FAMAweeks'] = fama[-1]


def rsi_tradingview(df: pd.DataFrame, stock, period_days):
    """
    :param df:
    :param stock:
    :param period_days:
    :return: RSI
    """
    delta = df['Close'].diff()

    up = delta.copy()
    up[up < 0] = 0
    up = pd.Series.ewm(up, alpha=1/period_days).mean()

    down = delta.copy()
    down[down > 0] = 0
    down *= -1
    down = pd.Series.ewm(down, alpha=1/period_days).mean()

    rsi_values = np.where(up == 0, 0, np.where(down == 0, 100, 100 - (100 / (1 + up / down))))

    rsi_df = pd.DataFrame({'RSI': rsi_values}, index=df.index)
    return rsi_df #return date as index, and rsi value as another column.

def rsi_tradingview_weekly(df: pd.DataFrame, stock, period_days):
    """
    igual al rsiDaily pero en vez de tener todos los precios de todos los dias en el df que le paso,
    tengo las fechas de todos los viernes, y del current day.

    :param df:
    :param stock:
    :param period_days:
    :return: RSI
    """

    df['RSI14weeks'] = np.nan

    for date in df.index:
        #resample weekly and take the last value, so it only appears the price of the last day of each particular week.
        weekly_returns = df['Close'][:date].resample('W-Fri', closed='right').last()
        delta = weekly_returns.diff()

        up = delta.copy()
        up[up < 0] = 0
        up = pd.Series.ewm(up, alpha=1/period_days).mean()

        down = delta.copy()
        down[down > 0] = 0
        down *= -1
        down = pd.Series.ewm(down, alpha=1/period_days).mean()

        rsi_values = np.where(up == 0, 0, np.where(down == 0, 100, 100 - (100 / (1 + up / down))))

        #rsi_df = pd.DataFrame({'RSI14weeks': rsi_values}, index=df.index)

        #en la última fecha, guardo el último rsi de la tabla de valores
        df.loc[date, 'RSI14weeks'] = rsi_values[-1]

###########
def calculate_volatility(df, lookback):
    returns = np.log(df['Close'] / df['Close'].shift(1))
    volatility = returns.rolling(window=lookback).std() * np.sqrt(252)
    #print("Volatility:", volatility)
    return volatility

def kurtosis(src, length):
    avg = src.ewm(span=length, adjust=False).mean()
    stdv = src.rolling(window=length).std()
    sum_values = ((src - avg) ** 4).rolling(window=length).sum()
    for i in range(1, length):
        sum_values += ((src.shift(-i) - avg) ** 4).rolling(window=length).sum()
    return sum_values / length / (stdv ** 4) - 3

# Function to calculate x_star
def x_star(q, k3, k4):
    second_term = (q ** 2 - 1) / 6 * k3
    third_term = (q ** 3 - 3 * q) / 24 * k4
    fourth_term = (2 * q ** 3 - 5 * q) / 36 * k3 ** 2
    return q + second_term + third_term + fourth_term

def calculate_risk_ranges(ticker_data, choiceMidPoint):
    LookBack = 21
    alpha = 2.0 / (1.0 + LookBack)
    SkewLength = 21
    true_range = np.maximum.reduce([ticker_data['High'] - ticker_data['Low'],
                                    np.abs(ticker_data['High'] - ticker_data['Close'].shift(1)),
                                    np.abs(ticker_data['Low'] - ticker_data['Close'].shift(1))]) / ticker_data[
                     'Close'].shift(1)

    deviation_max = 1.0
    deviation_min = 1.0

    # Calculate deviation_max and deviation_min
    for i in range(1, len(ticker_data)):
        deviation_max = alpha * (ticker_data['Close'][i] > ticker_data['Close'][i - 1]) * true_range[i] + (
                    1.0 - alpha) * deviation_max
        deviation_min = alpha * (ticker_data['Close'][i] < ticker_data['Close'][i - 1]) * true_range[i] + (
                    1.0 - alpha) * deviation_min

    # Calculate skewness
    skewness = deviation_max / deviation_min
    # print(skewness)

    # Calculate kurtosis
    x_kurtosis = ticker_data['Close'].kurtosis()
    # print(x_kurtosis)

    # Cornish-Fisher approximation of 90th quantile
    upskew = x_star(1.645, skewness, x_kurtosis)
    downskew = x_star(-1.645, skewness, x_kurtosis)

    # Calculate PxH and PxL based on choiceMidPoint
    if choiceMidPoint == 'Last':
        PxH = ticker_data['Close']
        PxL = ticker_data['Close']
    elif choiceMidPoint == 'YDAY':
        PxH = ticker_data['Close'].shift(1)
        PxL = ticker_data['Close'].shift(1)
    elif choiceMidPoint == 'H&L':
        PxH = ticker_data['Low']
        PxL = ticker_data['High']
    elif choiceMidPoint == 'Tight':
        PxH = np.minimum(ticker_data['Low'], ticker_data['Close'].shift(1))
        PxL = np.maximum(ticker_data['High'], ticker_data['Close'].shift(1))

    # print(downskew)
    # Calculate RRHigh and RRLow
    RRHigh = PxH + upskew * ticker_data['Close'].rolling(window=LookBack).std()
    RRLow = PxL + downskew * ticker_data['Close'].rolling(window=LookBack).std()

    return RRHigh, RRLow

##############

def plot_price_MA_volume(ticker_data, ticker, pdf_pages, tickersCategories, start_date):
    try:
        gics1 = tickersCategories.loc[ticker, 'GICS 1']
        gics2 = tickersCategories.loc[ticker, 'GICS 2']
    except:
        gics1=''
        gics2=''

    #four weeks ago date
    today= ticker_data.index[-1] #fecha de último dia de cotización
    date4w = today - timedelta(days=28) #fecha hace 4 semanas.
    date4w = pd.to_datetime(date4w)
    max_price_4w = ticker_data['Close'].loc[date4w:today].max() #precio maximo en ese periodo de tiempo
    min_price_4w = ticker_data['Close'].loc[date4w:today].min() #precio minimo en el periodo

    #13 weeks
    date13w = today - timedelta(days=91)
    date13w = pd.to_datetime(date13w)
    max_price_13w = ticker_data['Close'].loc[date13w:today].max()
    min_price_13w = ticker_data['Close'].loc[date13w:today].min()

    # 26 weeks
    date26w = today - timedelta(days=182)
    date26w = pd.to_datetime(date26w)
    max_price_26w = ticker_data['Close'].loc[date26w:today].max()
    min_price_26w = ticker_data['Close'].loc[date26w:today].min()

    #fixed date
    datefixed = "2023-12-9"
    datefixed = pd.to_datetime(datefixed)
    max_price_fixed = ticker_data['Close'].loc[datefixed:today].max()
    min_price_fixed = ticker_data['Close'].loc[datefixed:today].min()

    #lista con 4 listas, cada una con 4 vértices para armar el cuadrado.
    sequence = [[(date26w, max_price_26w), (date26w, min_price_26w), (today, min_price_26w), (today, max_price_26w), (date26w, max_price_26w)],
                [(date13w, max_price_13w), (date13w, min_price_13w), (today, min_price_13w), (today, max_price_13w), (date13w, max_price_13w)],
                [(date4w, max_price_4w), (date4w, min_price_4w), (today, min_price_4w), (today, max_price_4w), (date4w, max_price_4w)],
                [(datefixed, max_price_fixed), (datefixed, min_price_fixed), (today, min_price_fixed), (today, max_price_fixed), (datefixed, max_price_fixed)]]


    #armo figura
    fig = mpf.figure(style='yahoo', figsize=(15, 25))
    gs = fig.add_gridspec(6, 1, height_ratios=[10, 3, 3, 5, 5, 5]) #ratios entre gráficos
    #fig.subplots_adjust(hspace=0.4)

    #cada ax comparte el x-axis del de abajo suyo.
    #ax7 = fig.add_subplot(gs[6]) prender cuando se muestre gráfico de probability bands
    ax6 = fig.add_subplot(gs[5])
    ax1 = fig.add_subplot(gs[0], sharex=ax6)
    ax2 = fig.add_subplot(gs[1], sharex=ax6)
    ax3 = fig.add_subplot(gs[2], sharex=ax6)
    ax4 = fig.add_subplot(gs[3], sharex=ax6)
    ax5 = fig.add_subplot(gs[4], sharex=ax6)

    #FIRST PLOT
    #extraigo las medias moviles, y las agrego como columna.
    ticker_data['MA8'] = ticker_data['Close'].rolling(window=8).mean()
    ticker_data['MA20'] = ticker_data['Close'].rolling(window=20).mean()
    ticker_data['MA50'] = ticker_data['Close'].rolling(window=50).mean()
    ticker_data['MA200'] = ticker_data['Close'].rolling(window=200).mean()

    #armo plot de cada media movil, con respectivo color, label and respective axes.
    m8 = mpf.make_addplot(ticker_data['MA8'][start_date:], color="darkorange", width=1.5, label='MA8', ax=ax1) #width determina grosor de la linea
    m20 = mpf.make_addplot(ticker_data['MA20'][start_date:], color="firebrick", width=1.5, label='MA20', ax=ax1)  # type, linestyle, alpha could be added
    m50 = mpf.make_addplot(ticker_data['MA50'][start_date:], color="tomato", width=1.5, label='MA50', ax=ax1)
    m200 = mpf.make_addplot(ticker_data['MA200'][start_date:], color="red", width=1.5, label='MA200', ax=ax1)

    #plot the ticker_data as candle in this axes, add plots that also correspond to this axes, xrotation null and plot the lines forming a rectangle.
    mpf.plot(ticker_data[start_date:], type='candle', ax=ax1, addplot=[m8, m20, m50, m200], xrotation=0, alines= dict(alines=sequence, colors=['lightblue', 'steelblue', 'blue', 'purple']))

    #SECOND PLOT
    ticker_data['Volume20R'] = ticker_data['Volume'].rolling(window=20).mean()
    volume = mpf.make_addplot(ticker_data['Volume20R'][start_date:], color="lightgray", label='Vol MA20', ax=ax2)
    mpf.plot(ticker_data[start_date:], type='line', ax=ax2, volume=ax2, xrotation=0, addplot=[volume])


    #THIRD PLOT
    ticker_data['RSI14'] = rsi_tradingview(ticker_data, ticker, 14)['RSI']
    rsi_tradingview_weekly(ticker_data, ticker, 14)
    rsi = mpf.make_addplot(ticker_data['RSI14'][start_date:], color="steelblue", label='RSI14', ax=ax3)
    rsiWeeks = mpf.make_addplot(ticker_data['RSI14weeks'][start_date:], color="teal", label='RSI14weeks', ax=ax3)

    ax3.set_yticks([10, 30, 50, 70, 90])
    mpf.plot(ticker_data[start_date:], type='candle', ax=ax4, xrotation=0, addplot=[rsi, rsiWeeks])


    #FORTH PLOT
    ticker_data["MAMA"], ticker_data["FAMA"] = calculate_mama_fama_daily(ticker_data)
    calculate_mama_fama_week(ticker_data)

    #mamaW = mpf.make_addplot(ticker_data["MAMAweeks"][start_date:], color="hotpink", label='MAMAweekly', secondary_y=False, ax=ax4)  # secondary y false so they share the same y-axis numbers.
    #famaW = mpf.make_addplot(ticker_data["FAMAweeks"][start_date:], color="mediumvioletred", label='FAMAweekly', secondary_y=False, ax=ax4)
    mama = mpf.make_addplot(ticker_data["MAMA"][start_date:], color="cadetblue", label='MAMA', secondary_y=False, ax=ax4)  # secondary y false so they share the same y-axis numbers.
    fama = mpf.make_addplot(ticker_data["FAMA"][start_date:], color="steelblue", label='FAMA', secondary_y=False, ax=ax4)

    #IMPORTANTE -> raro, dejo ax=ax4(otro grafico donde esta el candlechart del price, pero al agregar addplot a ese, y en el addplot esta ax=ax6, agrega lo del addplot al ax6 sin agregar el candlechart)
    mpf.plot(ticker_data[start_date:], type='candle', ax=ax4, xrotation=0, addplot=[mama, fama])

    #color palet for the fifth plot
    color_palette = sns.color_palette("Blues", n_colors=5)

    #FIFTH PLOT
    ticker_data['ratio/MA8'] = ticker_data["Close"] / ticker_data["MA8"]
    ticker_data['ratio/MA20'] = ticker_data["Close"] / ticker_data["MA20"]
    ticker_data['ratio/MA50'] = ticker_data["Close"] / ticker_data["MA50"]
    ticker_data['ratio/MA200'] = ticker_data["Close"] / ticker_data["MA200"]

    ratioMA8 = mpf.make_addplot(ticker_data["ratio/MA8"][start_date:], color=color_palette[1], label='$/MA8',
                                 secondary_y=False, ax=ax5)
    ratioMA20 = mpf.make_addplot(ticker_data["ratio/MA20"][start_date:], color=color_palette[2],  label='$/MA20',
                                 secondary_y=False, ax=ax5)
    ratioMA50 = mpf.make_addplot(ticker_data["ratio/MA50"][start_date:], color=color_palette[3],
                                 label='$/MA50', secondary_y=False, ax=ax5)
    ratioMA200 = mpf.make_addplot(ticker_data["ratio/MA200"][start_date:], color=color_palette[4],
                                 label='$/MA200', secondary_y=False, ax=ax5)
    mpf.plot(ticker_data[start_date:], type='candle', ax=ax4, xrotation=0, addplot=[ratioMA8, ratioMA20, ratioMA50, ratioMA200])


    #SIXTH PLOT
    ticker_data['ratio/MAMA'] = ticker_data["Close"] / ticker_data["MAMA"]
    ticker_data['ratio/FAMA'] = ticker_data["Close"] / ticker_data["FAMA"]
    ratioMAMA = mpf.make_addplot(ticker_data["ratio/MAMA"][start_date:], color="forestgreen", label='$/MAMA',
                                 secondary_y=False, ax=ax6)
    ratioFAMA = mpf.make_addplot(ticker_data["ratio/FAMA"][start_date:], color="olivedrab", label='$/FAMA',
                                 secondary_y=False, ax=ax6)
    mpf.plot(ticker_data[start_date:], type='candle', ax=ax4, xrotation=0, addplot=[ratioMAMA, ratioFAMA], datetime_format='%b.%d')


    #SEVENTH PLOT
    '''ticker_data["high_range"], ticker_data["low_range"] = calculate_risk_ranges(ticker_data, choiceMidPoint='Tight')
    high_range = mpf.make_addplot(ticker_data["high_range"][start_date:], color="forestgreen", label='high',
                                  secondary_y=False, ax=ax7)
    low_range = mpf.make_addplot(ticker_data["low_range"][start_date:], color="red",label='low',
                                 secondary_y=False, ax=ax7)
    mpf.plot(ticker_data[start_date:], type='candle', ax=ax7, xrotation=0, addplot=[high_range, low_range])'''

    # hide the x-axis of the first plots, leaving only in the last.
    plt.setp(ax2.get_xticklabels(), visible=False)
    plt.setp(ax3.get_xticklabels(), visible=False)
    plt.setp(ax4.get_xticklabels(), visible=False)
    plt.setp(ax5.get_xticklabels(), visible=False)

    #set the legends of the plots to the upper left
    ax1.legend(loc='upper left')
    ax2.legend(loc='upper left')
    ax3.legend(loc='upper left')
    ax4.legend(loc='upper left')
    ax5.legend(loc='upper left')
    ax6.legend(loc='upper left')

    plt.suptitle(f'{ticker} - {gics1} - {gics2}', fontsize=35, y=0.98)
    plt.text(0.05, 0.94, f'última fecha tenida en cuenta: {ticker_data.index[-1].strftime("%Y-%m-%d")}', fontsize=16, transform=fig.transFigure)
    pdf_pages.savefig(fig, bbox_inches='tight') #save the figure plotted to the pdf
    plt.close()

def main():

    tickers_file_path = os.path.join("graphicalAnalysis", "tickersCategories.xlsx")
    download_from_google_drive(tickers_file_path) #descargo el excel del drive y lo guardo en tickers_file_path
    tickersCategories = pd.read_excel(tickers_file_path, engine="openpyxl") #chupo ticker-categoria del excel

    #document to test locally
    tickers = tickersCategories['TICKER'].tolist() #lista de tickers
    #tickers = ['GLD', 'UUP']
    #tickers = list(set(tickers))

    tickersCategories.set_index('TICKER', inplace=True)


    start_time = "2021-06-01" #tomo data desde antes para calcular las medias desde la startdate
    start_date = "2023-06-01" #date desde la q va a figurar en los gráficos

    with PdfPages('stockAnalysis.pdf') as pdf_pages: #guardo en pdf el resultado
        for ticker in tickers:
            if ticker not in ['HYGY', 'EWZ-again', 'FXI-again', 'ITA-again']:
                ticker_data = fetch_ticker_data(ticker, start_time) #armo dataframe con precios historicos
                ticker_data = cleaning_dataframe(ticker_data) #limpio dataframe

                plot_price_MA_volume(ticker_data, ticker, pdf_pages, tickersCategories, start_date=start_date) #ploteo el gráfico


    #documento para testear localmente
    upload_pdf_to_google_drive('stockAnalysis.pdf', 'application/pdf')


if __name__ == '__main__':
    main()
