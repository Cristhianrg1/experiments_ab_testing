import sys
import os

##sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
from modules.data_processing.data_processor import ExperimentProcessor


def get_data():
    df = pd.read_csv("./data/raw_data/experiments_dataset.csv")
    return df


def load_and_process_data(id: str, date, is_same_day=False):
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
