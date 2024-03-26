import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mplfinance as mpf
import talib
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime, timedelta
import os
#import seaborn as sns

######################################drive##############################################
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials

# Get the path of the current script
script_path = os.path.realpath(__file__)

# Change the working directory to the script's directory
os.chdir(os.path.dirname(script_path))
############################################################################################################


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

    file_id = '1Hb9I1tE8qN7FxoK_6pL_ZzaxZN-Gkqtz'

    # Descarga del archivo
    file_drive = drive.CreateFile({'id': file_id}) #crea conexión al archivo en google
    file_drive.GetContentFile(destination_path) #descarga el contenido del archivo al destination_path

def upload_to_google_drive(file_path, basename_, folder_id):
    '''sube a google drive el archivo encontrado en el filepath que se pasa.'''
    #antes fue necesario 'enable' google drive api dado un projecto creado, luego cree un service account(bot para autenticar) y le di acceso de editor al folder en el drive.

    #credenciales guardadas de la service account(bot q lleva acabo la authentication), json fue descargado de console.cloud.google
    credentials = ServiceAccountCredentials.from_json_keyfile_name("delphosdatascience-1956c0e4959e.json", ["https://www.googleapis.com/auth/drive"])

    #realizo la authentication con esas credenciales
    gauth = GoogleAuth()
    gauth.credentials = credentials

    #conecto a google drive con la autenticación.
    drive = GoogleDrive(gauth)

    existing_files = drive.ListFile({'q': f"'{folder_id}' in parents and title contains '{os.path.basename(basename_)}' and trashed=false"}).GetList()
    for existing_file in existing_files:
        existing_file.Trash()


    #creo un file con la data del excel guardado, y con el id del folder dentro del drive
    file_drive = drive.CreateFile({'title': os.path.basename(file_path), 'parents': [{'id': folder_id}]})
    file_drive.SetContentFile(file_path)
    file_drive.Upload()



def fetch_ticker_data(ticker, period):
    ticker_data = yf.download(ticker, period=period, auto_adjust=True)
    return ticker_data

def cleaning_dataframe(df, ticker, period):
    '''clean the dataframe'''
    attempt = 1
    max_attempts = 3
    while attempt <= max_attempts:
        try:
            df.sort_index(ascending=True, inplace=True)  # lo dejo sorteado con la última fecha abajo.
            df.index.name = "Date"  # index column llamada "Date"
            df.ffill(inplace=True)  # relleno los vacios con el valor del de arriba
            df.dropna(how="all", inplace=True)  # si hay filas completamente vacias, funalas
            df.index = df.index.strftime("%Y-%m-%d")
            df.index = pd.to_datetime(df.index)
            return df
        except AttributeError:
            df = yf.download(ticker, period=period, auto_adjust=True)  # adjust by dividends/stocksplits
        attempt +=1
    return df

def calculate_rsi(df, amount, period, price_column, stock):
    df[f'RSI{period}{amount}'] = np.nan

    for date in df.index:
        current_day = df.index[-1].day_name()[:3]  # nombre de dia de semana, primeras 3 letras

        # resample weekly and take the last value, so it only appears the price of the last day of each particular week.
        weekly_returns = df[price_column][:date].resample('W-' + current_day, closed='right').last()
        delta = weekly_returns.diff()

        up = delta.copy()
        up[up < 0] = 0
        up = pd.Series.ewm(up, alpha=1 / amount).mean()

        down = delta.copy()
        down[down > 0] = 0
        down *= -1
        down = pd.Series.ewm(down, alpha=1 / amount).mean()

        rsi_values = np.where(up == 0, 0, np.where(down == 0, 100, 100 - (100 / (1 + up / down))))

        # en la última fecha, guardo el último rsi de la tabla de valores
        df.loc[date, f'RSI{period}{amount}'] = rsi_values[-1]

    return df

def calculate_current_over_media(df, ticker, rounds, price_column):

    df[f'$/{rounds}M'] = np.nan

    for date in df.index:
        current_price = df.loc[date, price_column]
        media200 = find_media_rounds(df[:date], price_column, rounds)

        df.loc[date, f'$/{rounds}M'] = current_price/media200

    return df

def find_media_rounds(df, price_column, rounds):
    last_values = df[price_column][-rounds:]
    mean_last_values = last_values.mean()
    return mean_last_values

def main():
    tickers_file_path = os.path.join("tickers.xlsx")
    download_from_google_drive(tickers_file_path)  # descargo el excel del drive y lo guardo en tickers_file_path
    tickers_df = pd.read_excel(tickers_file_path, engine="openpyxl")
    tickers = tickers_df['TICKER']
    #column names
    price_200_media_column = "$/200MA"
    desvio_column = "desvio "
    rsi_column = "RSI14W"

    #armo dataframe
    df = pd.DataFrame(index=tickers, columns=[price_200_media_column, desvio_column, rsi_column])
    df.index.name = "Ticker"

    #para cada ticker
    for ticker in tickers:
        period = '10y'

        ticker_data = fetch_ticker_data(ticker, period)
        ticker_data = cleaning_dataframe(ticker_data, ticker, period)

        #parameters
        rounds = 200
        rsi_amount = 14
        rsi_period = 'weekly'
        price_column = 'Close'

        ticker_data = calculate_rsi(ticker_data, rsi_amount, rsi_period, price_column, ticker) #agrego columna con rsi de 14 semanas al momento
        ticker_data = calculate_current_over_media(ticker_data, ticker, rounds, price_column) #columna del ratio al momento

        #estandarizo ratio sobre serie histórica
        mean = ticker_data[f'$/{rounds}M'].mean()
        std = ticker_data[f'$/{rounds}M'].std()
        current_price = ticker_data.loc[ticker_data.index[-1], price_column]
        ratio = ticker_data[f'$/{rounds}M'].iloc[-1]
        standarized = (ratio - mean) / std

        #add to dataframe
        df.loc[ticker, price_200_media_column] = round(ticker_data[f'$/{rounds}M'].iloc[-1], 2)
        df.loc[ticker, desvio_column] = round(standarized, 2)
        df.loc[ticker, rsi_column] = round(ticker_data[f'RSI{rsi_period}{rsi_amount}'].iloc[-1], 2)

    df.to_excel('worldAnalysis.xlsx')
    upload_to_google_drive('worldAnalysis.xlsx', 'worldAnalysis', '1lJxR5KceOwqe8u1KlApCZALpyQ8sJ5RR')




if __name__ == '__main__':
    main()