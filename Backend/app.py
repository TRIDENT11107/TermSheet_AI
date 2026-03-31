from __future__ import annotations

import json
import logging
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge

try:
    from .utils.document_utils import SUPPORTED_EXTENSIONS, extract_text_from_upload
    from .utils.predict import get_model_status, predict_text
except ImportError:
    # Supports direct execution: python Backend/app.py
    from utils.document_utils import SUPPORTED_EXTENSIONS, extract_text_from_upload
    from utils.predict import get_model_status, predict_text


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FRONTEND_DIST = PROJECT_ROOT / "Front End" / "react-app" / "dist"
MAX_INFERENCE_CHARS = 120_000


def create_app(frontend_dist: Path | None = None) -> Flask:
    app = Flask(__name__, static_folder=None)
    app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25MB upload limit
    app.config["FRONTEND_DIST"] = str(frontend_dist or DEFAULT_FRONTEND_DIST)
    CORS(app)

    def _json_text_payload():
        if not request.is_json:
            return None
        payload = request.get_json(silent=True) or {}
        if "text" not in payload:
            return None
        text = str(payload.get("text") or "").strip()
        if not text:
            raise ValueError("Text payload is empty.")
        return text, {
            "filename": None,
            "extension": None,
            "source_type": "json_text",
            "text_length": len(text),
            "warnings": [],
        }

    @app.route("/predict", methods=["POST"])
    def predict():
        try:
            logger.info("Received /predict request")

            if "file" in request.files:
                upload = request.files["file"]
                if not upload.filename:
                    return jsonify({"error": "No selected file"}), 400
                text, input_metadata = extract_text_from_upload(upload)
            else:
                payload = _json_text_payload()
                if payload is None:
                    return jsonify({"error": "No file or text provided"}), 400
                text, input_metadata = payload

            if len(text) > MAX_INFERENCE_CHARS:
                text = text[:MAX_INFERENCE_CHARS]
                warnings = input_metadata.setdefault("warnings", [])
                warnings.append(
                    f"Input text truncated to {MAX_INFERENCE_CHARS} characters for faster inference."
                )
                input_metadata["text_length"] = len(text)

            result = predict_text(text)
            result["input"] = input_metadata
            return jsonify(result), 200

        except RequestEntityTooLarge:
            max_bytes = app.config.get("MAX_CONTENT_LENGTH", 0)
            max_mb = max_bytes / (1024 * 1024) if max_bytes else 0
            return (
                jsonify(
                    {
                        "error": (
                            f"Uploaded file is too large. Maximum allowed size is "
                            f"{max_mb:.0f} MB."
                        ),
                        "max_size_mb": round(max_mb, 2),
                    }
                ),
                413,
            )
        except ValueError as exc:
            return (
                jsonify(
                    {
                        "error": str(exc),
                        "supported_types": sorted(SUPPORTED_EXTENSIONS),
                    }
                ),
                400,
            )
        except RuntimeError as exc:
            return (
                jsonify(
                    {
                        "error": str(exc),
                        "supported_types": sorted(SUPPORTED_EXTENSIONS),
                    }
                ),
                422,
            )
        except Exception as exc:
            logger.exception("Unhandled error in /predict: %s", exc)
            return jsonify({"error": "Server error while processing prediction."}), 500

    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify(
            {
                "status": "ok",
                "message": "TermSheet AI Backend is running",
                "model_status": get_model_status(),
            }
        )

    @app.route("/model/metrics", methods=["GET"])
    def model_metrics():
        metrics_path = Path(__file__).resolve().parent / "model" / "metrics.json"
        if not metrics_path.exists():
            return jsonify({"error": "Model metrics not found. Train the model first."}), 404

        try:
            with metrics_path.open("r", encoding="utf-8") as metrics_file:
                metrics = json.load(metrics_file)
            return jsonify(metrics)
        except Exception as exc:
            logger.exception("Failed to read model metrics: %s", exc)
            return jsonify({"error": "Failed to read metrics file."}), 500

    @app.route("/supported-types", methods=["GET"])
    def supported_types():
        return jsonify({"supported_types": sorted(SUPPORTED_EXTENSIONS)})

    @app.errorhandler(RequestEntityTooLarge)
    def handle_too_large(_error):
        max_bytes = app.config.get("MAX_CONTENT_LENGTH", 0)
        max_mb = max_bytes / (1024 * 1024) if max_bytes else 0
        return (
            jsonify(
                {
                    "error": (
                        f"Uploaded file is too large. Maximum allowed size is "
                        f"{max_mb:.0f} MB."
                    ),
                    "max_size_mb": round(max_mb, 2),
                }
            ),
            413,
        )

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        # Ensure API endpoints always return JSON errors.
        if request.path.startswith("/predict") or request.path.startswith("/model") or request.path.startswith("/supported-types") or request.path.startswith("/health"):
            return jsonify({"error": error.description}), error.code
        return error

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        logger.exception("Unhandled server error: %s", error)
        if request.path.startswith("/predict") or request.path.startswith("/model") or request.path.startswith("/supported-types") or request.path.startswith("/health"):
            return jsonify({"error": "Internal server error."}), 500
        return jsonify({"error": "Internal server error."}), 500

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path: str):
        frontend_dist_path = Path(app.config["FRONTEND_DIST"])

        if not frontend_dist_path.exists():
            return (
                jsonify(
                    {
                        "error": "Frontend build not found.",
                        "expected_path": str(frontend_dist_path),
                        "hint": "Run: cd \"Front End/react-app\" && npm run build",
                    }
                ),
                404,
            )

        requested = frontend_dist_path / path
        if path and requested.exists() and requested.is_file():
            return send_from_directory(str(frontend_dist_path), path)
        return send_from_directory(str(frontend_dist_path), "index.html")

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
