import os
import logging
import argparse
from flask import request, jsonify
from dotenv import load_dotenv

from api.ab_testing_api import create_ab_test_api


def parse_arguments():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Run A/B Test API")
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host for the API server (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", 8080)),
        help="Port for the API server (default: 8080)",
    )
    return parser.parse_args()


def setup_logging():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    return logging.getLogger(__name__)


def is_development():
    return os.getenv('ENV', 'production').lower() == 'local'

def main():
    logger = setup_logging()
    args = parse_arguments()

    app = create_ab_test_api()
    logger.info(f"Starting API server on {args.host}:{args.port}")

    @app.before_request
    def before_request():
        logger.info(f"Received request: {request.url}")

    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.exception("An error occurred:")
        return jsonify({"error": "An unexpected error occurred"}), 500
    
    debug_mode = is_development()
    app.run(host=args.host, port=args.port, debug=debug_mode)


if __name__ == "__main__":
    main()
