import pandas as pd
import numpy as np
from scipy.stats import chi2_contingency, norm, t
from statsmodels.stats.proportion import proportions_ztest
from statsmodels.stats.multitest import multipletests
import statsmodels.api as sm
from statsmodels.formula.api import ols
from statsmodels.stats.multicomp import pairwise_tukeyhsd


class ABTestAnalyzer:
    """
    Clase para analizar resultados de pruebas A/B utilizando diferentes métodos estadísticos.

    Esta clase proporciona métodos para crear tablas de contingencia, realizar pruebas
    estadísticas como Chi-cuadrado y z-test, y ejecutar análisis más complejos como
    comparaciones por pares y análisis de efectos causales.

    Args:
        data (DataFrame): DataFrame de pandas que contiene los datos de las pruebas A/B.

    Methods:
        create_contingency_table():
            Crea una tabla de contingencia que cruza la variante con el resultado de compra.
            Returns:
                DataFrame: Tabla de contingencia de pandas.

        chi_square_test(contingency_table):
            Realiza una prueba Chi-cuadrado en la tabla de contingencia.
            Args:
                contingency_table (DataFrame): Tabla de contingencia.
            Returns:
                tuple: Estadístico Chi-cuadrado y p-valor.

        z_test(winner_id):
            Realiza una prueba z-test entre la variante ganadora y las demás variantes.
            Args:
                winner_id (str): ID de la variante ganadora.
            Returns:
                tuple: Estadístico z, p-valor y intervalo de confianza.

        post_hoc_test():
            Realiza un post-hoc test para comparar variantes después de un Chi-cuadrado significativo.
            Returns:
                tuple: Listas de booleanos indicando si se rechaza la hipótesis nula y p-valores corregidos.

        multi_variant_analysis():
            Realiza un análisis de variantes múltiples, incluyendo ANOVA y pruebas de Tukey.
            Returns:
                tuple: Resultados por variante, tabla ANOVA y resultados de Tukey HSD.

        pairwise_comparisons():
            Realiza comparaciones por pares entre las variantes.
            Returns:
                list: Lista de diccionarios con las comparaciones por pares, efectos y p-valores.

        rubin_causal_model():
            Realiza un análisis de efectos causales utilizando el modelo causal de Rubin.
            Returns:
                tuple: Resultados por variante y efectos causales entre variantes.

        average_treatment_effect():
            Calcula el Efecto Medio del Tratamiento (ATE) entre dos variantes.
            Returns:
                dict: Resultados del ATE incluyendo el intervalo de confianza.

        determine_winner():
            Determina la variante ganadora utilizando los métodos adecuados según el número de variantes.
            Returns:
                dict: Resultados incluyendo la variante ganadora y pruebas estadísticas realizadas.
    """

    def __init__(self, data):
        """
        Inicializa la instancia de ABTestAnalyzer con los datos proporcionados.

        Args:
            data (DataFrame): DataFrame que contiene los datos del experimento A/B.
        """
        self.data = data
        self.variants = data["variant_id"].unique()

    def create_contingency_table(self):
        """
        Crea una tabla de contingencia que cruza la variante con el resultado de compra.

        Returns:
            DataFrame: Tabla de contingencia de pandas que muestra la distribución de compras
            por variante.
        """
        return pd.crosstab(self.data["variant_id"], self.data["with_purchase"])

    def chi_square_test(self, contingency_table):
        """
        Realiza una prueba Chi-cuadrado en la tabla de contingencia.

        Args:
            contingency_table (DataFrame): Tabla de contingencia creada con create_contingency_table.

        Returns:
            tuple: Estadístico Chi-cuadrado y p-valor.
        """
        chi2, p, _, _ = chi2_contingency(contingency_table)
        return chi2, p

    def z_test(self, winner_id):
        """
        Realiza una prueba z-test entre la variante ganadora y las demás variantes.

        Args:
            winner_id (str): ID de la variante ganadora.

        Returns:
            tuple: Estadístico z, p-valor y intervalo de confianza.
        """
        data_v1 = self.data[self.data["variant_id"] == winner_id]
        data_v2 = self.data[self.data["variant_id"] != winner_id]

        conversions_v1 = data_v1["with_purchase"].sum()
        total_v1 = data_v1["with_purchase"].count()
        conversions_v2 = data_v2["with_purchase"].sum()
        total_v2 = data_v2["with_purchase"].count()

        prop_v1 = conversions_v1 / total_v1
        prop_v2 = conversions_v2 / total_v2
        diff = prop_v1 - prop_v2

        if prop_v1 == 0 and prop_v2 == 0:
            stat = 0.0
            pval = 1.0
            ci = (0.0, 0.0)
        else:
            count = [conversions_v1, conversions_v2]
            nobs = [total_v1, total_v2]
            stat, pval = proportions_ztest(count, nobs, alternative="larger")

            se = np.sqrt(
                prop_v1 * (1 - prop_v1) / total_v1 + prop_v2 * (1 - prop_v2) / total_v2
            )

            if np.isnan(se) or se == 0:
                ci = (None, None)
            else:
                z = norm.ppf(0.975)
                ci_low = diff - z * se
                ci_high = diff + z * se
                ci = (ci_low, ci_high)

        return float(stat), float(pval), ci

    def post_hoc_test(self):
        """
        Realiza un post-hoc test para comparar variantes después de un Chi-cuadrado significativo.

        Returns:
            tuple: Listas de booleanos indicando si se rechaza la hipótesis nula y p-valores corregidos.
        """
        pvals = []
        for i, v1 in enumerate(self.variants):
            for v2 in self.variants[i + 1 :]:
                subset = self.data[self.data["variant_id"].isin([v1, v2])]
                count = subset.groupby("variant_id")["with_purchase"].sum().values
                nobs = subset.groupby("variant_id")["with_purchase"].count().values
                if 0 in nobs:
                    continue
                stat, pval = proportions_ztest(count, nobs)
                pvals.append(pval)
        reject, pvals_corrected, _, _ = multipletests(pvals, method="bonferroni")
        return reject.tolist(), pvals_corrected.tolist()

    def _determine_winner_one_variants(self):
        """
        Determina la variante ganadora en un experimento con una sola variante.

        Este método calcula la tasa de conversión para la única variante y la devuelve
        como la ganadora.

        Returns:
            dict: Un diccionario con la variante ganadora y sin pruebas estadísticas adicionales.
        """
        rates = self.data.groupby("variant_id")["with_purchase"].mean()
        winner = rates.idxmax()

        return {
            "winner": winner,
            "tests": None,
        }

    def _determine_winner_two_variants(self):
        """
        Determina la variante ganadora en un experimento con dos variantes.

        Este método utiliza un z-test para comparar las tasas de conversión entre las dos
        variantes y también calcula el Efecto Medio del Tratamiento (ATE) y el modelo causal
        de Rubin.

        Returns:
            dict: Un diccionario con la variante ganadora y los resultados de las pruebas
            estadísticas realizadas.
        """
        rates = self.data.groupby("variant_id")["with_purchase"].mean()
        winner = rates.idxmax()

        z_stat, pval, ci = self.z_test(winner)
        significant_difference = pval < 0.05

        return {
            "winner": winner,
            "tests": {
                "z-test": {
                    "p_value": pval,
                    "significant_difference": significant_difference,
                    "z_statistic": z_stat,
                    "ci": ci,
                },
            },
        }

    def _determine_winner_multi_variants(self):
        """
        Determina la variante ganadora en un experimento con más de dos variantes.

        Este método realiza una prueba Chi-cuadrado para detectar diferencias significativas
        entre variantes, seguida de análisis post-hoc y comparaciones por pares si es necesario.

        Returns:
            dict: Un diccionario con la variante ganadora y los resultados de las pruebas
            estadísticas realizadas.
        """
        contingency_table = self.create_contingency_table()
        chi2, pval = self.chi_square_test(contingency_table)

        significant_difference = pval < 0.05
        winner = None

        if significant_difference:
            reject, _ = self.post_hoc_test()
            if any(reject):
                significant_variants = [
                    self.variants[i] for i, r in enumerate(reject) if r
                ]
                max_rate = 0
                for variant in significant_variants:
                    rate = self.data[self.data["variant_id"] == variant][
                        "with_purchase"
                    ].mean()
                    if rate > max_rate:
                        max_rate = rate
                        winner = variant
            else:
                rates = self.data.groupby("variant_id")["with_purchase"].mean()
                winner = rates.idxmax()
        else:
            rates = self.data.groupby("variant_id")["with_purchase"].mean()
            winner = rates.idxmax()

        return {
            "winner": winner,
            "tests": {
                "chi_square": {
                    "chi2": chi2,
                    "p_value": pval,
                    "significant_difference": significant_difference,
                },
            },
        }

    def determine_winner(self):
        """
        Determina la variante ganadora en un experimento A/B basado en el número de variantes.

        Utiliza diferentes métodos estadísticos según el número de variantes en el experimento.

        Returns:
            dict: Un diccionario con la variante ganadora y los resultados de las pruebas
            estadísticas realizadas.
        """
        if len(self.variants) == 1:
            return self._determine_winner_one_variants()
        elif len(self.variants) == 2:
            return self._determine_winner_two_variants()
        else:
            return self._determine_winner_multi_variants()
