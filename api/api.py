import sys
import os
from urllib.parse import unquote

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
from datetime import datetime
from modules.data_loader import load_and_process_data
from modules.hypothesis_tester import determine_winner
from modules.data_checks import ChecksProcessor

app = Flask(__name__)


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

    experiment_data = load_and_process_data(id, date)

    if experiment_data.empty:
        return jsonify({"error": "Experiment not found"}), 404

    winner, pval, is_significant = determine_winner(experiment_data)
    checks_processor = ChecksProcessor(experiment_data)
    user_independence = checks_processor.check_user_independence()
    experiment_independence = checks_processor.check_experiment_independence()
    variation = checks_processor.check_variation()
    sample_size = checks_processor.check_sample_size()

    response = {
        "results": {
            id: {
                "number_of_participants": int(experiment_data["user_id"].nunique()),
                "checks": {
                    "p-val": pval,
                    "significant_pval": is_significant,
                    "user_independence": user_independence,
                    "experiment_independence":experiment_independence,
                    "variation": variation,
                    "sample_size": sample_size,
                },
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
