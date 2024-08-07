
import logging
import argparse
from api.ab_testing_api import create_ab_test_api
from flask import request, jsonify


def parse_arguments():
    parser = argparse.ArgumentParser(description='Run A/B Test API')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host for the API server (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=5000, help='Port for the API server (default: 5000)')
    return parser.parse_args()


def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    return logging.getLogger(__name__)


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
    
    app.run(host=args.host, port=args.port, debug=True)

if __name__ == "__main__":
    main()