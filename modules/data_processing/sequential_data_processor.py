from pandasql import sqldf
import pandas as pd
import numpy as np

from modules.data_processing.data_processor import ExperimentProcessor


class SequentialExperimentProcessor:
    """
    Clase para procesar y etiquetar experimentos secuenciales en un DataFrame.

    Esta clase proporciona métodos para preparar datos de eventos, fusionar datos de compras,
    y expandir datos de experimentos en filas adicionales basadas en la estructura de los experimentos.

    Args:
        data (pd.DataFrame): DataFrame que contiene una columna 'experiments' con cadenas de experimentos.

    Methods:
        prepare_events_data() -> pd.DataFrame:
            Prepara los datos de eventos no relacionados con compras, añadiendo timestamps previos y posteriores,
            y calculando el tiempo máximo permitido para una compra asociada.

        merge_purchase_data() -> pd.DataFrame:
            Fusiona los datos de eventos con los datos de compras dentro de ventanas de tiempo específicas para
            identificar si una compra ocurrió en el tiempo máximo permitido.

        expand_experiments(row: pd.Series) -> list:
            Expande el texto de la columna experiments en varias filas, una para cada experimento y variante.
            Args:
                row (pd.Series): Fila del DataFrame que contiene la columna experiments.
            Returns:
                list: Lista de diccionarios, cada uno representando una fila expandida con columnas adicionales.

        expanded_experiments() -> pd.DataFrame:
            Crea un nuevo DataFrame con los eventos de experimentos y la columna de experimentos expandida.
            Returns:
                pd.DataFrame: Nuevo DataFrame con filas expandidas para cada experimento y variante.

        labeled_experiments() -> pd.DataFrame:
            Etiqueta los experimentos en función de si resultaron en una compra, agrupando por usuario y variante.
            Returns:
                pd.DataFrame: DataFrame con etiquetas indicando si hubo compra.
    """

    def __init__(self, data):
        """
        Inicializa la clase con un DataFrame.

        Args:
            data (pd.DataFrame): DataFrame que contiene una columna 'experiments'
            con cadenas de experimentos.

        """
        self.data = data

    def prepare_events_data(self):
        df = self.data[~self.data["event_name"].isin(["BUY"])].copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["user_id"] = df["user_id"].astype(str)
        df = df.sort_values(by=["user_id", "event_name", "timestamp", "item_id"])
        df["next_timestamp_event"] = df.groupby(
            [
                "user_id",
                "event_name",
                df["item_id"].notna() & (df["item_id"] != ""),
            ]
        )["timestamp"].shift(-1)

        df["prev_timestamp_event"] = df.groupby(
            [
                "user_id",
                "event_name",
                df["item_id"].notna() & (df["item_id"] != ""),
            ]
        )["timestamp"].shift(1)
        df["max_time"] = np.where(
            df["event_name"] == "SEARCH",
            pd.to_datetime(df["timestamp"]) + pd.Timedelta(minutes=210),
            pd.to_datetime(df["timestamp"]) + pd.Timedelta(minutes=81),
        )

        return df

    def merge_purchase_data(self):
        purchase_data = self.data[self.data["event_name"] == "BUY"].copy()
        purchase_data["timestamp"] = pd.to_datetime(purchase_data["timestamp"])
        purchase_data["user_id"] = purchase_data["user_id"].astype(str)
        non_purchase_data = self.prepare_events_data()
        query = """
        SELECT
            non_purchase_data.*,
            purchase_data.timestamp AS purchase_timestamp,
            purchase_data.item_id AS purchase_item_id,
            purchase_data.user_id AS purchase_user_id
        FROM 
            non_purchase_data
        LEFT JOIN 
            purchase_data 
        ON 
            non_purchase_data.user_id = purchase_data.user_id
            AND (
                (non_purchase_data.event_name = 'SEARCH' 
                AND purchase_data.timestamp >= non_purchase_data.timestamp
                AND (purchase_data.timestamp < non_purchase_data.next_timestamp_event
                    OR non_purchase_data.next_timestamp_event IS NULL)
                )
                OR (non_purchase_data.event_name != 'SEARCH'
                    AND non_purchase_data.item_id = purchase_data.item_id
                    AND purchase_data.timestamp >= non_purchase_data.timestamp
                    AND (purchase_data.timestamp < non_purchase_data.next_timestamp_event
                    OR non_purchase_data.next_timestamp_event IS NULL)
                )
            )
        """

        result = sqldf(query)
        result["with_purchase"] = np.where(
            result["purchase_timestamp"] <= result["max_time"], True, False
        )

        return result

    def expand_experiments(row: pd.Series) -> list:
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
                "with_purchase": row["with_purchase"],
            }
            for exp_name, variant_id in experiments_dict.items()
        ]
        return expanded_rows

    def expanded_experiments(self) -> pd.DataFrame:
        """
        Crea un nuevo DataFrame con lo eventos de experimentos
        y la columna de experimentos expandida.

        Returns:
            pd.DataFrame: Nuevo DataFrame con filas expandidas
            para cada experimento y variante.
        """
        data = self.merge_purchase_data()
        expanded_data = data.apply(
            SequentialExperimentProcessor.expand_experiments, axis=1
        )
        expanded_df = pd.DataFrame(
            [item for sublist in expanded_data for item in sublist]
        )
        return expanded_df

    def labeled_experiments(self):
        df = self.expanded_experiments()
        df_grouped = (
            df.groupby(["event_name", "experiment_name", "variant_id", "user_id"])
            .agg(
                total_attempts=("with_purchase", "count"),
                purchases=("with_purchase", "sum"),
            )
            .reset_index()
        )

        df_grouped["with_purchase"] = np.where(df_grouped["purchases"] > 0, True, False)
        return df_grouped
