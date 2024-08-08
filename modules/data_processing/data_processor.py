import pandas as pd
import numpy as np


class ExperimentProcessor:
    def __init__(self, data):
        """
        Inicializa la clase con un DataFrame.

        Args:
            data (pd.DataFrame): DataFrame que contiene una columna 'experiments'
            con cadenas de experimentos.

        """
        self.data = data

    @staticmethod
    def convert_to_dict(exp_string: str) -> dict:
        """
        Convierte una cadena que representa un diccionario
        de experimentos en un diccionario de Python.

        Args:
            exp_string (str): Cadena con formato {key1=value1, key2=value2, ...}.

        Returns:
            dict: Diccionario donde las claves son nombres de experimentos
            y los valores son ids de variantes.
        """
        exp_string = exp_string.strip("{}")
        items = exp_string.split(", ")
        exp_dict = {item.split("=")[0]: item.split("=")[1] for item in items}
        return exp_dict

    def expand_experiments(self, row: pd.Series) -> list:
        """
        Expande el texto de la columna experiments en varias filas,
        una para cada experimento y variante.

        Args:
            row (pd.Series): Fila del DataFrame que contiene la columna experiments
            con una serie de experimentos.

        Returns:
            list: Lista de diccionarios, donde cada diccionario representa una
            fila expandida con columnas adicionales para experiment_name y variant_id.
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
        """
        Obtiene un DataFrame con los datos de compras.

        Returns:
            pd.DataFrame: Nuevo DataFrame con los datos de compras.
        """
        purchases_df = self.data[self.data["event_name"] == "BUY"].copy()
        return purchases_df

    def filter_non_purchase_events(self) -> pd.DataFrame:
        """
        Filtra los eventos que no son compras.

        Returns:
            pd.DataFrame: DataFrame filtrado sin eventos de compra.
        """
        experiments_df = self.data[~self.data["event_name"].isin(["BUY"])].copy()
        return experiments_df

    def get_non_experiments_data(self) -> pd.DataFrame:
        """
        Crea un nuevo DataFrame con los eventos no considerados
        como parte de los experimentos.

        Returns:
            pd.DataFrame: Nuevo DataFrame con filas expandidas.
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
        Crea un nuevo DataFrame con lo eventos de experimentos
        y la columna de experimentos expandida.

        Returns:
            pd.DataFrame: Nuevo DataFrame con filas expandidas
            para cada experimento y variante.
        """
        experiments_df = self.filter_non_purchase_events()
        expanded_data = experiments_df.apply(self.expand_experiments, axis=1)
        expanded_df = pd.DataFrame(
            [item for sublist in expanded_data for item in sublist]
        )
        return expanded_df

    @staticmethod
    def product_event_and_purchase(experiments: pd.DataFrame, purchases: pd.DataFrame):
        """
        Relaciona eventos de productos con compras dentro de una ventana
        de tiempo de 4 horas

        Args:
            experiments (pd.DataFrame): DataFrame con eventos de experimentos.
            purchases (pd.DataFrame): DataFrame con eventos de compra.

        Returns:
            pd.DataFrame: DataFrame fusionado con información de productos y compras.
        """
        experiments = experiments[~experiments["event_name"].isin(["SEARCH"])].copy()
        experiments["timestamp"] = pd.to_datetime(experiments["timestamp"])

        purchases["timestamp"] = pd.to_datetime(purchases["timestamp"])
        purchases["timestamp2"] = purchases["timestamp"]
        purchases["item_id_purchase"] = purchases["item_id"]

        time_window = pd.Timedelta(hours=4)

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
        merged_df["timestamp_purchase"] = np.where(
            (merged_df["timestamp_purchase"] >= merged_df["timestamp"])
            & (merged_df["timestamp_purchase"] <= merged_df["timestamp"] + time_window),
            merged_df["timestamp_purchase"],
            np.nan,
        )

        merged_df = merged_df.sort_values(
            by=["timestamp", "timestamp_purchase", "item_id_purchase"]
        ).drop_duplicates(
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

    @staticmethod
    def search_event_and_purchase(experiments: pd.DataFrame, purchases: pd.DataFrame):
        """
        Relaciona eventos de búsqueda con compras dentro de una ventana
        de tiempo de 8 horas.

        Args:
            experiments (pd.DataFrame): DataFrame con eventos de experimentos.
            purchases (pd.DataFrame): DataFrame con eventos de compra.

        Returns:
            pd.DataFrame: DataFrame fusionado con información de búsquedas y compras.
        """
        experiments = experiments[experiments["event_name"] == "SEARCH"].copy()
        experiments["timestamp"] = pd.to_datetime(experiments["timestamp"])
        experiments = experiments.groupby("experiment_name").filter(
            lambda x: x["variant_id"].nunique() >= 2
        )

        purchases["timestamp"] = pd.to_datetime(purchases["timestamp"])
        purchases["timestamp2"] = purchases["timestamp"]

        time_window = pd.Timedelta(hours=8)
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

        merged_df = merged_df.sort_values(
            by=["timestamp", "timestamp_purchase", "item_id_purchase"]
        ).drop_duplicates(
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
        """
        Etiqueta los experimentos en función de si resultaron en una compra.

        Returns:
            pd.DataFrame: DataFrame con etiquetas de si hubo compra.
        """
        experiments = self.get_experimets_data()
        purchases = self.get_purchases_data()

        product_df = self.product_event_and_purchase(experiments, purchases)
        search_df = self.search_event_and_purchase(experiments, purchases)

        merge_df = pd.concat([product_df, search_df]).reset_index(drop=True)
        merge_df["with_purchase"] = np.where(
            ~merge_df["item_id_purchase"].isna(), True, False
        )
        return merge_df
