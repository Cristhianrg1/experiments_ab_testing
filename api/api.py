import sys
import os
from urllib.parse import unquote

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
from datetime import datetime
import pandas as pd
from modules.data_processor import ExperimentProcessor
from modules.hypothesis_tester import determine_winner

app = Flask(__name__)


def load_and_process_data():
    data = pd.read_csv("data/experiments_dataset.csv")
    processor = ExperimentProcessor(data)
    processed_data = processor.label_experiments()
    return processed_data


@app.route("/experiment/<path:id>/result", methods=["GET"])
def get_experiment_result(id):
    id = unquote(id)
    day = request.args.get("day")
    if not day:
        return jsonify({"error": "Day parameter is required"}), 400

    try:
        date = datetime.strptime(day, "%Y-%m-%d %H")
    except ValueError:
        return jsonify({"error": "Invalid date format, expected YYYY-MM-DD HH"}), 400

    processed_data = load_and_process_data()

    experiment_data = processed_data[
        (processed_data["experiment_name"] == id)
        & (processed_data["timestamp"].dt.date == date.date())
    ]

    if experiment_data.empty:
        return jsonify({"error": "Experiment not found"}), 404

    winner = determine_winner(experiment_data)

    response = {
        "results": {
            id: {
                "number_of_participants": int(experiment_data["user_id"].nunique()),
                "winner": winner,
                "variants": [],
            }
        }
    }

    variants = experiment_data["variant_id"].unique()
    for variant in variants:
        variant_data = experiment_data[experiment_data["variant_id"] == variant]
        response["results"][id]["variants"].append(
            {
                "id": variant,
                "number_of_purchases": int(variant_data["with_purchase"].sum()),
            }
        )

    return jsonify(response), 200


if __name__ == "__main__":
    app.run(debug=True)
