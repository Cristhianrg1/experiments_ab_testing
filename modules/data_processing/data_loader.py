import pandas as pd
from modules.data_processing.data_processor import ExperimentProcessor


def get_data():
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

    data = get_data()
    if is_same_day:
        data = data[(data["timestamp"].dt.date == date.date())]
        processor = ExperimentProcessor(data)
        processed_data = processor.label_experiments()
        processed_data = processed_data[(processed_data["experiment_name"] == id)]
    else:
        processor = ExperimentProcessor(data)
        processed_data = processor.label_experiments()
        processed_data = processed_data[
            (processed_data["experiment_name"] == id)
            & (processed_data["timestamp"].dt.date == date.date())
        ]
    return processed_data
