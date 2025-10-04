#!/usr/bin/env python3
"""Mock server to demonstrate API endpoints without FastAPI dependency."""

import json
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import sys
from pathlib import Path

# Add the app to the path
sys.path.insert(0, str(Path(__file__).parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class MockAPIHandler(BaseHTTPRequestHandler):
    """Mock API handler to simulate FastAPI endpoints."""

    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        # Log the request
        logger.info(f"GET {path} - Mock API request")

        if path == '/v1/health':
            # V1 health endpoint
            response = {"status": "ok"}
            self.send_json_response(200, response)
        elif path in ['/health/', '/health']:
            # Legacy health endpoint
            response = {
                "status": "healthy",
                "service": "splunk-auto-doc-api",
                "version": "0.1.0",
            }
            self.send_json_response(200, response)
        else:
            # 404 for unknown paths
            response = {"error": "Not found"}
            self.send_json_response(404, response)

    def send_json_response(self, status_code, data):
        """Send a JSON response."""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        """Override default logging to use our logger."""
        logger.info(f"{self.address_string()} - {format % args}")


def main():
    """Run the mock server."""
    port = 8000
    server_address = ('', port)
    httpd = HTTPServer(server_address, MockAPIHandler)

    logger.info(f"Starting mock Splunk Auto Doc API server on port {port}")
    logger.info(f"Available endpoints:")
    logger.info(f"  GET /v1/health -> {{\"status\": \"ok\"}}")
    logger.info(f"  GET /health/   -> legacy health check")
    logger.info(f"Access server at: http://localhost:{port}")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down mock server")
        httpd.shutdown()


if __name__ == "__main__":
    main()
