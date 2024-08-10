import pandas as pd
import numpy as np


class ExperimentProcessor:
    """
    Clase para procesar y etiquetar experimentos en un DataFrame.

    Esta clase proporciona métodos para convertir cadenas de experimentos en diccionarios,
    expandir datos de experimentos, filtrar eventos, y relacionar eventos con compras dentro
    de ventanas de tiempo específicas.

    Args:
        data (pd.DataFrame): DataFrame que contiene una columna 'experiments' con cadenas de experimentos.

    Methods:
        convert_to_dict(exp_string: str) -> dict:
            Convierte una cadena que representa un diccionario de experimentos en un diccionario de Python.
            Args:
                exp_string (str): Cadena con formato {key1=value1, key2=value2, ...}.
            Returns:
                dict: Diccionario donde las claves son nombres de experimentos y los valores son ids de variantes.

        expaneded_experiments_list(row: pd.Series) -> list:
            Expande el texto de la columna experiments en varias filas, una para cada experimento y variante.
            Args:
                row (pd.Series): Fila del DataFrame que contiene la columna experiments.
            Returns:
                list: Lista de diccionarios, cada uno representando una fila expandida con columnas adicionales.

        get_purchases_data() -> pd.DataFrame:
            Obtiene un DataFrame con los datos de compras.
            Returns:
                pd.DataFrame: Nuevo DataFrame con los datos de compras.

        filter_non_purchase_events() -> pd.DataFrame:
            Filtra los eventos que no son compras.
            Returns:
                pd.DataFrame: DataFrame filtrado sin eventos de compra.

        get_experimets_data() -> pd.DataFrame:
            Crea un nuevo DataFrame con los eventos de experimentos y la columna de experimentos expandida.
            Returns:
                pd.DataFrame: Nuevo DataFrame con filas expandidas para cada experimento y variante.

        product_event_and_purchase(experiments: pd.DataFrame, purchases: pd.DataFrame) -> pd.DataFrame:
            Relaciona eventos de productos con compras dentro de una ventana de tiempo de 81 minutos.
            Args:
                experiments (pd.DataFrame): DataFrame con eventos de experimentos.
                purchases (pd.DataFrame): DataFrame con eventos de compra.
            Returns:
                pd.DataFrame: DataFrame fusionado con información de productos y compras.

        search_event_and_purchase(experiments: pd.DataFrame, purchases: pd.DataFrame) -> pd.DataFrame:
            Relaciona eventos de búsqueda con compras dentro de una ventana de tiempo de 210 minutos.
            Args:
                experiments (pd.DataFrame): DataFrame con eventos de experimentos.
                purchases (pd.DataFrame): DataFrame con eventos de compra.
            Returns:
                pd.DataFrame: DataFrame fusionado con información de búsquedas y compras.

        label_experiments(date=None) -> pd.DataFrame:
            Etiqueta los experimentos en función de si resultaron en una compra.
            Args:
                date (datetime, opcional): Fecha específica para filtrar los eventos.
            Returns:
                pd.DataFrame: DataFrame con etiquetas de si hubo compra.
    """

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

    @staticmethod
    def expaneded_experiments_list(row: pd.Series) -> list:
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
        experiments_dict = ExperimentProcessor.convert_to_dict(row["experiments"])
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

    def get_experimets_data(self) -> pd.DataFrame:
        """
        Crea un nuevo DataFrame con lo eventos de experimentos
        y la columna de experimentos expandida.

        Returns:
            pd.DataFrame: Nuevo DataFrame con filas expandidas
            para cada experimento y variante.
        """
        experiments_df = self.filter_non_purchase_events()
        expanded_data = experiments_df.apply(self.expaneded_experiments_list, axis=1)
        expanded_df = pd.DataFrame(
            [item for sublist in expanded_data for item in sublist]
        )
        return expanded_df

    @staticmethod
    def product_event_and_purchase(experiments: pd.DataFrame, purchases: pd.DataFrame):
        """
        Relaciona eventos de productos con compras dentro de una ventana
        de tiempo de 81 minutos.

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

        time_window = pd.Timedelta(minutes=81)

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

        return merged_df

    @staticmethod
    def search_event_and_purchase(experiments: pd.DataFrame, purchases: pd.DataFrame):
        """
        Relaciona eventos de búsqueda con compras dentro de una ventana
        de tiempo de 210 minutos

        Args:
            experiments (pd.DataFrame): DataFrame con eventos de experimentos.
            purchases (pd.DataFrame): DataFrame con eventos de compra.

        Returns:
            pd.DataFrame: DataFrame fusionado con información de búsquedas y compras.
        """
        experiments = experiments[experiments["event_name"] == "SEARCH"].copy()
        experiments["timestamp"] = pd.to_datetime(experiments["timestamp"])

        purchases["timestamp"] = pd.to_datetime(purchases["timestamp"])
        purchases["timestamp_purchase"] = purchases["timestamp"]

        time_window = pd.Timedelta(minutes=210)
        merged_df = pd.merge_asof(
            experiments.sort_values("timestamp"),
            purchases[
                ["user_id", "timestamp", "item_id", "timestamp_purchase"]
            ].sort_values("timestamp"),
            on="timestamp",
            by="user_id",
            direction="forward",
            tolerance=time_window,
            suffixes=["", "_purchase"],
        )

        return merged_df

    def label_experiments(self, date=None):
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

        if date is not None:
            merge_df = merge_df[(merge_df["timestamp"].dt.date == date.date())]

        merge_df = (
            merge_df.groupby(["event_name", "experiment_name", "variant_id", "user_id"])
            .agg(
                purchases=("item_id_purchase", "nunique"),
                attempts=("timestamp", "nunique"),
            )
            .reset_index()
        )
        merge_df["with_purchase"] = np.where(merge_df["purchases"] > 0, True, False)
        return merge_df
