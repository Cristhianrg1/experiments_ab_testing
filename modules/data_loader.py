import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd


def get_data():
    df = pd.read_csv('./data/experiments_dataset.csv')
    return df
