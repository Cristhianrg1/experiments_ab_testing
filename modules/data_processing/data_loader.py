import os
from io import StringIO

from google.cloud import storage
from google.oauth2 import service_account
from dotenv import load_dotenv
import pandas as pd

from modules.data_processing.data_processor import ExperimentProcessor

load_dotenv()
credentials_path_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
file_name = os.getenv("EXPERIMENTS_FILE_NAME")
bucket_name = os.getenv("BUCKET_NAME")


def read_csv_from_gcs(bucket_name, file_name):
    """
    Carga los datos del archivo CSV desde un bucket en GCS.

    Returns:
        pd.DataFrame: DataFrame con los datos cargados del archivo CSV.
    """
    if os.getenv('ENV') == 'local':
        credentials_path_file = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path_file
        )
        storage_client = storage.Client(credentials=credentials)
    else:
        storage_client = storage.Client()
    
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    data = blob.download_as_text()
    df = pd.read_csv(StringIO(data))

    return df


def read_csv_from_local_folder():
    """
    Carga los datos del archivo CSV.

    Returns:
        pd.DataFrame: DataFrame con los datos cargados del archivo CSV.
    """
    df = pd.read_csv("./data/raw_data/experiments_dataset.csv")
    return df


def load_and_process_data(id: str, date, is_same_day=False):
    """
    Carga y procesa los datos de experimentos, etiquetándolos
    en función de si resultaron en una compra.

    Args:
        id (str): Identificador del experimento que se desea filtrar.
        date (datetime): Fecha específica para filtrar los datos.
        is_same_day (bool, opcional): Si es True, filtra los datos
        para incluir solo los eventos del mismo día.
        Si es False, toma datos del posterior día.

    Returns:
        pd.DataFrame: DataFrame con los datos procesados y
        filtrados por el experimento y la fecha especificada.
    """

    data = read_csv_from_gcs(bucket_name, file_name)
    if is_same_day:
        data = data[(data["timestamp"].dt.date == date.date())]
        processor = ExperimentProcessor(data)
        processed_data = processor.label_experiments()
        processed_data = processed_data[(processed_data["experiment_name"] == id)]
    else:
        processor = ExperimentProcessor(data)
        processed_data = processor.label_experiments(date)
        processed_data = processed_data[(processed_data["experiment_name"] == id)]
    return processed_data


def get_all_data():
    data = read_csv_from_gcs(bucket_name, file_name)
    return data
