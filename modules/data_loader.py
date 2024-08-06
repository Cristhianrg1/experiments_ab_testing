import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
from modules.data_processor import ExperimentProcessor


def get_data():
    df = pd.read_csv("./data/experiments_dataset.csv")
    return df


def load_and_process_data(id, date):
    data = get_data()
    processor = ExperimentProcessor(data)
    processed_data = processor.label_experiments()
    processed_data = processed_data[
        (processed_data["experiment_name"] == id)
        & (processed_data["timestamp"].dt.date == date.date())
    ]
    return processed_data
