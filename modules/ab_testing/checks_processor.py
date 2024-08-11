from statsmodels.stats.power import NormalIndPower, GofChisquarePower

from modules.utils.statistical_functions import normal_approximation


class ChecksProcessor:
    """
    Clase para realizar verificaciones en los datos de pruebas A/B.

    Esta clase proporciona métodos para verificar la independencia de los usuarios y experimentos,
    calcular la variación dentro de cada variante, y evaluar si el tamaño de la muestra es adecuado
    para los análisis estadísticos.

    Args:
        data (DataFrame): DataFrame de pandas que contiene los datos de las pruebas A/B.

    Methods:
        check_user_independence():
            Verifica si cada usuario está asociado únicamente a una variante en cada experimento.
            Returns:
                bool: True si todos los usuarios son independientes, False en caso contrario.

        check_experiment_independence():
            Verifica si cada experimento está asociado únicamente a un tipo de evento.
            Returns:
                bool: True si todos los experimentos son independientes, False en caso contrario.

        check_variation():
            Calcula la variación dentro de cada variante en términos de tasa de conversión.
            Returns:
                dict: Diccionario con la variación por cada variante.

        check_sample_size(alpha=0.05, power=0.8, effect_size=0.2):
            Evalúa si el tamaño de la muestra es adecuado para el análisis estadístico,
            considerando un nivel de significancia (alpha), poder estadístico (power) y tamaño del efecto.
            Args:
                alpha (float): Nivel de significancia para el análisis estadístico.
                power (float): Poder estadístico deseado.
                effect_size (float): Tamaño del efecto esperado.
            Returns:
                dict: Diccionario que indica si el tamaño de la muestra es adecuado para cada variante.

        run_all_checks(alpha=0.05, power=0.8):
            Ejecuta todas las verificaciones disponibles y devuelve los resultados.
            Args:
                alpha (float): Nivel de significancia para la verificación de tamaño de muestra.
                power (float): Poder estadístico para la verificación de tamaño de muestra.
            Returns:
                dict: Resultados de todas las verificaciones realizadas, incluyendo el número de variantes,
                independencia de usuarios y experimentos, variación por variante, y adecuación del tamaño de muestra.
    """

    def __init__(self, data):
        """
        Inicializa la instancia de ChecksProcessor con los datos proporcionados.

        Args:
            data (DataFrame): DataFrame que contiene los datos del experimento A/B.
        """
        self.data = data
        self.variants = data["variant_id"].unique()

    def check_user_independence(self):
        """
        Verifica si cada usuario está asociado únicamente a una variante en cada experimento.

        Returns:
            bool: True si todos los usuarios son independientes, False en caso contrario.
        """
        experiment_variants = self.data.groupby(["user_id", "experiment_name"])[
            "variant_id"
        ].nunique()
        independent = all(experiment_variants == 1)
        return independent

    def check_experiment_independence(self):
        """
        Verifica si cada experimento está asociado únicamente a un tipo de evento.

        Returns:
            bool: True si todos los experimentos son independientes, False en caso contrario.
        """
        experiment_variants = self.data.groupby(["experiment_name"])[
            "event_name"
        ].nunique()
        independent = all(experiment_variants == 1)
        return independent

    def check_normal_approximation(self):
        """
        Verifica si el experimento cumple con la distribución normal esperada. La 
        aproximación normal debe ser igual o superior a 5 para cada muestra, en caso contrario
        no se cumplieríia.

        Returns:
            bool: True si se cumple la normalidad aproximada, False en caso contrario.
        """
        grouped = (
            self.data.groupby("variant_id")
            .agg(n=("variant_id", "count"), p=("with_purchase", "mean"))
            .reset_index()
        )

        grouped["normal_approximation"] = grouped.apply(
            lambda row: normal_approximation(row["n"], row["p"]), axis=1
        )

        norm = grouped["normal_approximation"].all()

        return norm

    def check_sample_size(self, alpha=0.05, power=0.8, effect_size=0.2):
        """
        Evalúa si el tamaño de la muestra es adecuado para el análisis estadístico.

        Args:
            alpha (float): Nivel de significancia para el análisis estadístico.
            power (float): Poder estadístico deseado.
            effect_size (float): Tamaño del efecto esperado.

        Returns:
            dict: Diccionario que indica si el tamaño de la muestra es adecuado para cada variante.
        """
        sample_sizes = self.data.groupby("variant_id")["with_purchase"].count()
        adequacy = {}
        if len(sample_sizes) == 2:
            power_analysis = NormalIndPower()
            alternative = "two-sided"
        else:
            power_analysis = GofChisquarePower()
            alternative = None

        for variant, size in sample_sizes.items():
            if alternative:
                required_n = power_analysis.solve_power(
                    effect_size=effect_size,
                    alpha=alpha,
                    power=power,
                    alternative=alternative,
                )
            else:
                required_n = power_analysis.solve_power(
                    effect_size=effect_size, alpha=alpha, power=power
                )
            adequacy[variant] = size >= required_n

        return adequacy

    def run_all_checks(self, alpha=0.05, power=0.8):
        """
        Ejecuta todas las verificaciones disponibles y devuelve los resultados.

        Args:
            alpha (float): Nivel de significancia para la verificación de tamaño de muestra.
            power (float): Poder estadístico para la verificación de tamaño de muestra.

        Returns:
            dict: Resultados de todas las verificaciones realizadas, incluyendo el número de variantes,
            independencia de usuarios y experimentos, variación por variante, y adecuación del tamaño de muestra.
        """
        if len(self.variants) == 1:
            return {
                "num_of_variants": int(len(self.variants)),
            }
        else:
            return {
                "num_of_variants": int(len(self.variants)),
                "user_independence": self.check_user_independence(),
                "experiment_independence": self.check_experiment_independence(),
                "normal_approximation": self.check_normal_approximation(),
                "sample_size_adequacy": self.check_sample_size(alpha, power),
            }
