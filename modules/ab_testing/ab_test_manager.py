from modules.ab_testing.ab_test_analyzer import ABTestAnalyzer
from modules.ab_testing.checks_processor import ChecksProcessor


class ABTestManager:
    """
    Clase para gestionar y ejecutar el análisis de pruebas A/B.

    Esta clase coordina el procesamiento de datos y el análisis estadístico para 
    determinar los resultados de las pruebas A/B. Utiliza las clases ABTestAnalyzer 
    y ChecksProcessor para realizar verificaciones y análisis completos.

    Args:
        data (DataFrame): DataFrame de pandas que contiene los datos de las pruebas A/B.

    Methods:
        run_analysis():
            Ejecuta todas las verificaciones y el análisis para determinar la 
            variante ganadora del experimento A/B.
            Returns:
                tuple: Resultados de las verificaciones (checks) y análisis (results) 
                de las pruebas A/B.
    """
    def __init__(self, data):
        """
        Inicializa la instancia de ABTestManager con los datos proporcionados.

        Args:
            data (DataFrame): DataFrame que contiene los datos del experimento A/B.
        """
        self.data = data
        self.analyzer = ABTestAnalyzer(data)
        self.checks = ChecksProcessor(data)

    def run_analysis(self):
        """
        Ejecuta todas las verificaciones y análisis para determinar la variante ganadora.

        Este método coordina la ejecución de las verificaciones de datos y el análisis
        estadístico para determinar qué variante del experimento A/B es la ganadora.

        Returns:
            tuple: Contiene los resultados de las verificaciones (ab_checks) y los 
            resultados del análisis estadístico (ab_results).
        """
        ab_checks = self.checks.run_all_checks()
        ab_results = self.analyzer.determine_winner()

        return ab_checks, ab_results