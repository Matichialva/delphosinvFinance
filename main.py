import os

# Get the path of the current script
script_path = os.path.realpath(__file__)

# Change the working directory to the script's directory
os.chdir(os.path.dirname(script_path))

import yfinance as yf
import pandas as pd
import numpy as np
from functions_etfReturns import *
from datetime import datetime

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials

import etfReturnsMain
import technicalindicatorsMain
import technicalFactorsMain
import latamReturns
import latamRatios

def upload_to_google_drive(file_path):
    '''sube a google drive el archivo encontrado en el filepath que se pasa.'''
    #antes fue necesario 'enable' google drive api dado un projecto creado, luego cree un service account(bot para autenticar) y le di acceso de editor al folder en el drive.

    #credenciales guardadas de la service account(bot q lleva acabo la authentication), json fue descargado de console.cloud.google
    credentials = ServiceAccountCredentials.from_json_keyfile_name("delphosdatascience-1956c0e4959e.json", ["https://www.googleapis.com/auth/drive"])

    #realizo la authentication con esas credenciales
    gauth = GoogleAuth()
    gauth.credentials = credentials

    #conecto a google drive con la autenticación.
    drive = GoogleDrive(gauth)

    folder_id = '1kUPSl_Zuzv6iBYIR0_M9H_SnPUUGIIEA'


    existing_files = drive.ListFile({'q': f"'{folder_id}' in parents and title contains '{os.path.basename(file_path)}' and trashed=false"}).GetList()
    for existing_file in existing_files:
        existing_file.Trash()


    #creo un file con la data del excel guardado, y con el id del folder dentro del drive
    file_drive = drive.CreateFile({'title': os.path.basename(file_path), 'parents': [{'id': folder_id}]})
    file_drive.SetContentFile(file_path)
    file_drive.Upload()


if __name__ == "__main__":

    prices_file_path = os.path.join("etfReturnsExcel", "etfPrices.xlsx")
    df = pd.read_excel(prices_file_path, index_col="Date", engine="openpyxl")
    last_date = df.index.strftime("%Y-%m-%d")[-1]

    #armo y agrego etfReturns
    etfReturnsMain.main()
    returns_file_path = os.path.join("etfReturnsExcel", f"etfReturns-{last_date}.xlsx")
    upload_to_google_drive(returns_file_path)

############################################################################################################
    prices_indicators_path = os.path.join("technicalIndicatorsExcel", "etfPrices.xlsx")
    indicators_df = pd.read_excel(prices_indicators_path, index_col="Date", engine="openpyxl")
    last_date1 = indicators_df.index.strftime("%Y-%m-%d")[-1]

    #armo y agrego technicalIndicators
    technicalindicatorsMain.main()
    indicators_file_path = os.path.join("technicalIndicatorsExcel", f"etfIndicators-{last_date1}.xlsx")
    upload_to_google_drive(indicators_file_path)

################################################################################################################

    prices_factors_path = os.path.join("technicalFactorsExcel", "sp500Prices.xlsx")
    factors_df = pd.read_excel(prices_factors_path, index_col="Date", engine="openpyxl")
    last_date2 = factors_df.index.strftime("%Y-%m-%d")[-1]

    #armo y agrego technical factors
    technicalFactorsMain.main()
    topDownFactors_file_path = os.path.join("technicalFactorsExcel", f"sp500topDownFactors-{last_date2}.xlsx")
    upload_to_google_drive(topDownFactors_file_path)

############################################################################################################
    prices_latam_returns_path = os.path.join("latamReturns&Ratios", "latamPrices.xlsx")
    latam_prices_df = pd.read_excel(prices_latam_returns_path, index_col="Date", engine="openpyxl")
    last_date3 = latam_prices_df.index.strftime("%Y-%m-%d")[-1]

    latamReturns.main()
    latam_returns_file_path = os.path.join("latamReturns&Ratios", f"latamReturns-{last_date3}.xlsx")
    upload_to_google_drive(latam_returns_file_path)

################################################################################################################

    latamRatios.main()
    latam_country_ratios_file_path = os.path.join("latamReturns&Ratios", f"latamCountriesRatios-{last_date3}.xlsx")
    latam_industry_ratios_file_path = os.path.join("latamReturns&Ratios", f"latamIndustryRatios-{last_date3}.xlsx")
    upload_to_google_drive(latam_country_ratios_file_path)
    upload_to_google_drive(latam_industry_ratios_file_path)







