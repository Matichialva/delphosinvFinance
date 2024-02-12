import os
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

    existing_files = drive.ListFile({'q': f"'{'1kUPSl_Zuzv6iBYIR0_M9H_SnPUUGIIEA'}' in parents and title = '{os.path.basename(file_path)}' and trashed=false"}).GetList()
    for existing_file in existing_files:
        existing_file.Trash()

    #creo un file con la data del excel guardado, y con el id del folder dentro del drive
    file_drive = drive.CreateFile({'title': os.path.basename(file_path), 'parents': [{'id': '1kUPSl_Zuzv6iBYIR0_M9H_SnPUUGIIEA'}]})
    file_drive.SetContentFile(file_path)
    file_drive.Upload()


if __name__ == "__main__":
    etfReturnsMain.main()
    returns_file_path = os.path.join("etfReturnsExcel", "etfReturns.xlsx")
    upload_to_google_drive(returns_file_path)

    technicalindicatorsMain.main()
    indicators_file_path = os.path.join("technicalIndicatorsExcel", "etfIndicators.xlsx")
    upload_to_google_drive(indicators_file_path)

    technicalFactorsMain.main()
    topDownFactors_file_path = os.path.join("technicalFactorsExcel", "sp500topDownFactors.xlsx")
    upload_to_google_drive(topDownFactors_file_path)


