"""A small JSON API used to demonstrate a secure CI/CD pipeline.

The application itself is intentionally simple: the point of this repository
is the pipeline that tests, scans, builds, and publishes it.
"""
import os

from flask import Flask, jsonify

app = Flask(__name__)


@app.get("/")
def index():
    return jsonify(
        service="utiso-cicd-demo",
        status="ok",
        message="Hello from the CI/CD demo API",
    )


@app.get("/healthz")
def healthz():
    """Liveness/readiness probe used by the container HEALTHCHECK."""
    return jsonify(status="healthy"), 200


if __name__ == "__main__":
    # Host/port are configurable so the same image runs locally and in a container.
    host = os.environ.get("HOST", "0.0.0.0")  # noqa: S104 (bind-all is expected in a container)
    port = int(os.environ.get("PORT", "8080"))
    app.run(host=host, port=port)
