import pandas as pd
import numpy as np


class ExperimentProcessor:
    def __init__(self, data):
        """
        Initializes the class with a DataFrame.

        Args:
            data (pd.DataFrame): DataFrame containing an 'experiments' column with experiment strings.
        """
        self.data = data

    @staticmethod
    def convert_to_dict(exp_string: str) -> dict:
        """
        Converts a string representing a dictionary of experiments into a Python dictionary.

        Args:
            exp_string (str): String formatted as `{key1=value1, key2=value2, ...}`.

        Returns:
            dict: Dictionary where the keys are experiment names and the values are variant IDs.
        """
        exp_string = exp_string.strip("{}")
        items = exp_string.split(", ")
        exp_dict = {item.split("=")[0]: item.split("=")[1] for item in items}
        return exp_dict

    def expand_experiments(self, row: pd.Series) -> list:
        """
        Expands the 'experiments' string into multiple rows, one for each experiment and variant.

        Args:
            row (pd.Series): DataFrame row containing an 'experiments' column with a string of experiments.

        Returns:
            list: List of dictionaries, where each dictionary represents an expanded row with additional columns for 'experiment_name' and 'variant_id'.
        """
        experiments_dict = self.convert_to_dict(row["experiments"])
        expanded_rows = [
            {
                "event_name": row["event_name"],
                "item_id": row["item_id"],
                "timestamp": row["timestamp"],
                "experiment_name": exp_name,
                "variant_id": variant_id,
                "user_id": row["user_id"],
            }
            for exp_name, variant_id in experiments_dict.items()
        ]
        return expanded_rows

    def get_purchases_data(self) -> pd.DataFrame:
        """_summary_

        Returns:
            pd.DataFrame: New DataFrame with  purchases data
        """
        purchases_df = self.data[self.data["event_name"] == "BUY"].copy()
        return purchases_df

    def filter_non_purchase_events(self) -> pd.DataFrame:
        """_summary_

        Returns:
            pd.DataFrame: _description_
        """
        experiments_df = self.data[
            ~self.data["event_name"].isin(
                ["BUY", "CHECKOUT_1", "CHECKOUT_2", "CHECKOUT_3"]
            )
        ].copy()
        return experiments_df

    def get_non_experiments_data(self) -> pd.DataFrame:
        """
        Creates a new DataFrame by expanding the 'experiments' column of the original DataFrame.

        Returns:
            pd.DataFrame: New DataFrame with expanded rows for each experiment and variant.
        """
        experiments_df = experiments_df = self.data[
            self.data["event_name"].isin(
                ["BUY", "CHECKOUT_1", "CHECKOUT_2", "CHECKOUT_3"]
            )
        ].copy()
        expanded_data = experiments_df.apply(self.expand_experiments, axis=1)
        expanded_df = pd.DataFrame(
            [item for sublist in expanded_data for item in sublist]
        )
        return expanded_df

    def get_experimets_data(self) -> pd.DataFrame:
        """
        Creates a new DataFrame by expanding the 'experiments' column of the original DataFrame.

        Returns:
            pd.DataFrame: New DataFrame with expanded rows for each experiment and variant.
        """
        experiments_df = self.filter_non_purchase_events()
        expanded_data = experiments_df.apply(self.expand_experiments, axis=1)
        expanded_df = pd.DataFrame(
            [item for sublist in expanded_data for item in sublist]
        )
        return expanded_df

    @staticmethod
    def product_event_and_purchase(experiments: pd.DataFrame, purchases: pd.DataFrame):
        experiments = experiments[experiments["event_name"] == "PRODUCT"].copy()
        experiments["timestamp"] = pd.to_datetime(experiments["timestamp"])

        purchases["timestamp"] = pd.to_datetime(purchases["timestamp"])
        purchases["timestamp2"] = purchases["timestamp"]
        purchases["item_id_purchase"] = purchases["item_id"]

        time_window = pd.Timedelta("1 day")

        merged_df = pd.merge(
            experiments,
            purchases[
                ["user_id", "timestamp", "item_id", "timestamp2", "item_id_purchase"]
            ],
            on=["user_id", "item_id"],
            how="left",
            suffixes=["", "_purchase"],
        )

        merged_df["item_id_purchase"] = np.where(
            (merged_df["timestamp_purchase"] >= merged_df["timestamp"])
            & (merged_df["timestamp_purchase"] <= merged_df["timestamp"] + time_window),
            merged_df["item_id"],
            np.nan,
        )

        merged_df = merged_df.sort_values(by="item_id_purchase").drop_duplicates(
            subset=[
                "event_name",
                "item_id",
                "timestamp",
                "experiment_name",
                "variant_id",
                "user_id",
            ],
            keep="first",
        )

        return merged_df

    @staticmethod
    def search_event_and_purchase(experiments: pd.DataFrame, purchases: pd.DataFrame):
        experiments = experiments[experiments["event_name"] == "SEARCH"].copy()
        experiments["timestamp"] = pd.to_datetime(experiments["timestamp"])
        experiments = experiments.groupby("experiment_name").filter(
            lambda x: x["variant_id"].nunique() >= 2
        )

        purchases["timestamp"] = pd.to_datetime(purchases["timestamp"])
        purchases["timestamp2"] = purchases["timestamp"]

        time_window = pd.Timedelta("1 day")
        merged_df = pd.merge_asof(
            experiments.sort_values("timestamp"),
            purchases[["user_id", "timestamp", "item_id", "timestamp2"]].sort_values(
                "timestamp"
            ),
            on="timestamp",
            by="user_id",
            direction="forward",
            tolerance=time_window,
            suffixes=["", "_purchase"],
        )

        merged_df = merged_df.sort_values(by="item_id_purchase").drop_duplicates(
            subset=[
                "event_name",
                "item_id",
                "experiment_name",
                "variant_id",
                "user_id",
            ],
            keep="first",
        )

        return merged_df

    def label_experiments(self):
        experiments = self.get_experimets_data()
        purchases = self.get_purchases_data()

        product_df = self.product_event_and_purchase(experiments, purchases)
        search_df = self.search_event_and_purchase(experiments, purchases)

        merge_df = pd.concat([product_df, search_df]).reset_index(drop=True)
        merge_df["with_purchase"] = np.where(
            ~merge_df["item_id_purchase"].isna(), True, False
        )
        return merge_df
