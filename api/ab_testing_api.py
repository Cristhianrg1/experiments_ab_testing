from datetime import datetime
from urllib.parse import unquote
import logging

from flask import Flask, request, jsonify

from modules.data_processing.data_loader import load_and_process_data
from modules.ab_testing.ab_test_manager import ABTestManager
from modules.utils.utils import convert_to_serializable


def create_ab_test_api():
    """
    Crea y configura una API Flask para realizar análisis de experimentos A/B.

    Esta función configura una instancia de Flask que maneja solicitudes HTTP 
    relacionadas con la obtención de resultados de experimentos A/B. La API 
    procesa los datos del experimento, ejecuta pruebas estadísticas, y devuelve 
    los resultados en formato JSON.

    Args:
        None

    Returns:
        Flask: Una instancia de la aplicación Flask configurada para manejar 
        las solicitudes relacionadas con los experimentos A/B.

    Raises:
        400: Si falta el parámetro `day` o si el formato de la fecha es inválido.
        404: Si el experimento no se encuentra en los datos procesados.
        500: Si ocurre un error inesperado durante el procesamiento de la solicitud.
    """
    app = Flask(__name__)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    @app.route("/experiment/<path:id>/result", methods=["GET"])
    def get_experiment_result(id):
        try:
            id = unquote(id)
            day = request.args.get("day")
            if not day:
                return jsonify({"error": "Day parameter is required"}), 400
            try:
                date = datetime.strptime(day, "%Y-%m-%d %H")
            except ValueError:
                return jsonify(
                    {"error": "Invalid date format, expected YYYY-MM-DD HH"}
                ), 400

            experiment_data = load_and_process_data(id, date)
            if experiment_data.empty:
                return jsonify({"error": "Experiment not found"}), 404

            ab_test = ABTestManager(experiment_data)
            checks, results = ab_test.run_analysis()

            response = {
                "results": {
                    id: {
                        "number_of_participants": int(
                            experiment_data["user_id"].nunique()
                        ),
                        "checks":checks,
                        "statistical_tests": {
                            k: int(v) if isinstance(v, bool) else v
                            for k, v in results["tests"].items()
                        },
                        "winner": results["winner"],
                        "variants": [
                            {
                                "id": variant,
                                "number_of_purchases": int(
                                    experiment_data[
                                        experiment_data["variant_id"] == variant
                                    ]["with_purchase"].sum()
                                ),
                            }
                            for variant in experiment_data["variant_id"].unique()
                        ],
                    }
                }
            }
            serializable_response = convert_to_serializable(response)
            return jsonify(serializable_response), 200
        except Exception as e:
            logger.exception("An error occurred while processing the request:")
            return jsonify({"error": "An unexpected error occurred"}), 500

    return app
