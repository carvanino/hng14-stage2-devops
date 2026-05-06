import os
import random
import time
import threading
from flask import Flask, request, jsonify, Response
from prometheus_client import (
    Counter, Histogram, Gauge,
    generate_latest, CONTENT_TYPE_LATEST
)

app = Flask(__name__)

# ── Environment ───────────────────────────────────────────────────
MODE        = os.environ.get("MODE", "stable")
APP_VERSION = os.environ.get("APP_VERSION", "1.0.0")
START_TIME  = time.time()

# ── Chaos state ───────────────────────────────────────────────────
chaos_state = {"mode": None, "duration": None, "rate": None}
chaos_lock  = threading.Lock()

# ── Prometheus metrics ────────────────────────────────────────────
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status_code"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

app_uptime_seconds = Gauge(
    "app_uptime_seconds",
    "Application uptime in seconds"
)

app_mode_gauge = Gauge(
    "app_mode",
    "Current app mode: 0=stable, 1=canary"
)

chaos_active = Gauge(
    "chaos_active",
    "Active chaos mode: 0=none, 1=slow, 2=error"
)

# Set static gauges at startup
app_mode_gauge.set(1 if MODE == "canary" else 0)
chaos_active.set(0)


# ── Middleware — track every request ──────────────────────────────
@app.before_request
def start_timer():
    request._start_time = time.time()

@app.after_request
def track_metrics(response):
    duration = time.time() - request._start_time
    path     = request.path
    method   = request.method
    status   = str(response.status_code)

    http_requests_total.labels(method=method, path=path, status_code=status).inc()
    http_request_duration_seconds.labels(method=method, path=path).observe(duration)
    app_uptime_seconds.set(time.time() - START_TIME)

    return response


# ── Helpers ───────────────────────────────────────────────────────
def apply_mode_header(response):
    if MODE == "canary":
        response.headers["X-Mode"] = MODE
    return response

def apply_chaos():
    with chaos_lock:
        current_mode = chaos_state["mode"]
        duration     = chaos_state["duration"]
        rate         = chaos_state["rate"]

    if current_mode == "slow" and duration:
        time.sleep(duration)

    elif current_mode == "error" and rate:
        if random.random() < rate:
            response = jsonify({"error": "chaos error injection"})
            response.status_code = 500
            return apply_mode_header(response)

    return None


# ── Endpoints ─────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def index():
    if MODE == "canary":
        chaos_response = apply_chaos()
        if chaos_response:
            return chaos_response

    response = jsonify({
        "message":   "Welcome to SwiftDeploy API",
        "mode":      MODE,
        "version":   APP_VERSION,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    })
    return apply_mode_header(response)


@app.route("/healthz", methods=["GET"])
def healthz():
    uptime   = time.time() - START_TIME
    response = jsonify({"status": "ok", "uptime": uptime})
    return apply_mode_header(response)


@app.route("/metrics", methods=["GET"])
def metrics():
    # Update uptime before scrape
    app_uptime_seconds.set(time.time() - START_TIME)
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.route("/chaos", methods=["POST"])
def chaos():
    if MODE != "canary":
        return jsonify({"error": "Chaos mode only available in canary mode"}), 403

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400

    mode     = data.get("mode")
    duration = data.get("duration")
    rate     = data.get("rate")

    if mode not in ["slow", "error", "recover"]:
        return jsonify({"error": "Invalid mode"}), 400

    with chaos_lock:
        if mode == "slow":
            if not isinstance(duration, (int, float)) or duration <= 0:
                return jsonify({"error": "Invalid duration for slow mode"}), 400
            chaos_state["mode"]     = "slow"
            chaos_state["duration"] = duration
            chaos_state["rate"]     = None
            chaos_active.set(1)
            message = f"Chaos activated: slow mode, {duration}s delay per request"

        elif mode == "error":
            if not isinstance(rate, (int, float)) or not (0 < rate <= 1):
                return jsonify({"error": "Invalid rate for error mode"}), 400
            chaos_state["mode"]     = "error"
            chaos_state["duration"] = None
            chaos_state["rate"]     = rate
            chaos_active.set(2)
            message = f"Chaos activated: error mode, {rate*100:.0f}% error rate"

        elif mode == "recover":
            chaos_state["mode"]     = None
            chaos_state["duration"] = None
            chaos_state["rate"]     = None
            chaos_active.set(0)
            message = "Chaos cancelled: service recovering to normal"

    response = jsonify({
        "message": message,
        "chaos":   {"mode": chaos_state["mode"], "duration": chaos_state["duration"], "rate": chaos_state["rate"]}
    })
    return apply_mode_header(response)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("APP_PORT", 3000)))
