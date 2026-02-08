from flask import Flask, request, jsonify
from flask_cors import CORS
from analyzer import load_data, analyse_telemetry


def create_app():
    """
    Factory function for creating the Flask application.

    Returns
    -------
    flask.Flask
        Configured Flask app instance.
    """
    app = Flask(__name__)
    # Enable CORS for all routes.  This is useful when running the
    # frontend from a file:// origin during local development.
    CORS(app)

    @app.route("/analyze", methods=["POST"])
    def analyze():
        """
        Analyse uploaded telemetry and return ranked bottlenecks.

        Expects a multipart/form‑data request with a file field named
        ``file`` containing the CSV telemetry.  Optional form fields:
          - ``n_segments``: number of segments (default 4)
          - ``segments``: (preferred) number of segments (default 4)
          - ``max_dt``: maximum allowed dt in seconds (float; optional)
          - ``brake_threshold``: brake threshold in [0,1] (default 0.15)
          - ``throttle_threshold``: throttle threshold in [0,1] (default 0.25)

        Returns
        -------
        flask.Response
            JSON array of segment analysis records.
        """
        if "file" not in request.files:
            return jsonify({"error": "Missing file"}), 400
        file = request.files["file"]
        # Segments: accept either `segments` (frontend) or legacy `n_segments`
        n_segments_raw = request.form.get("segments", request.form.get("n_segments", 4))
        try:
            n_segments = int(n_segments_raw)
        except (TypeError, ValueError):
            n_segments = 4

        # Optional thresholds (for useful loss breakdown)
        brake_raw = request.form.get("brake_threshold", 0.15)
        throttle_raw = request.form.get("throttle_threshold", 0.25)
        try:
            brake_threshold = float(brake_raw)
        except (TypeError, ValueError):
            brake_threshold = 0.15
        try:
            throttle_threshold = float(throttle_raw)
        except (TypeError, ValueError):
            throttle_threshold = 0.25

        # Parse max_dt if provided
        max_dt_value = request.form.get("max_dt", None)
        max_dt = None
        if max_dt_value is not None and max_dt_value != "":
            try:
                max_dt = float(max_dt_value)
            except ValueError:
                max_dt = None

        # Load data into DataFrame
        # Using `file.stream` is the most reliable across Flask/Werkzeug versions
        df = load_data(file.stream)

        # Run analysis (now returns useful fields like brake_time_loss and exit_time_loss)
        result_df = analyse_telemetry(
            df,
            n_segments=n_segments,
            max_dt=max_dt,
            brake_threshold=brake_threshold,
            throttle_threshold=throttle_threshold,
        )
        # Convert result into JSON serialisable format
        data = result_df.to_dict(orient="records")
        return jsonify(data)

    return app


if __name__ == "__main__":
    app = create_app()
    # Use 0.0.0.0 so that the service is reachable from the host machine
    app.run(host="0.0.0.0", port=5001, debug=True)