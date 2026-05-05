import os
import random
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

chaos_state = {
    "mode": None,
    "duration": None,
    "rate": None,
}
MODE = os.environ.get("MODE", "stable")
APP_VERSION = os.environ.get("APP_VERSION", "1.0.0")
START_TIME = time.time()

def apply_mode_header(response):
    """
    Add a custom header to indicate the current mode (stable/chaos) in responses.
    """
    if MODE == "canary":
        response.headers['X-Mode'] = MODE
    return response

def apply_chaos():
    """
    Background thread function to apply chaos based on the current state.
    """
    if chaos_state["mode"] == "slow" and chaos_state["duration"]:
        time.sleep(chaos_state["duration"])
    elif chaos_state['mode'] == 'error' and chaos_state['rate']:
        if random.random() < chaos_state['rate']:
            response = jsonify({
                "error": "chaos error injection",
            })
            response.status_code = 500
            return apply_mode_header(response)
    return None


@app.route('/', methods=['GET'])
def index():
    """
    Main endpoint that simulates normal API behavior. 
    In "canary" mode, it randomly returns a 500 error to simulate instability.
    """
    if MODE == "canary":
        # Simulate chaos by randomly returning a 500 error
        response = apply_chaos()
        if response:
            return response

    response = jsonify({
        "message": f"Welcome to SwiftDeploy API",
        "mode": MODE,
        "version": APP_VERSION,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    })

    return apply_mode_header(response)


@app.route("/healthz", methods=["GET",])
def healthz():
    """
    Health check endpoint. Always returns 200 OK.
    """
    uptime = time.time() - START_TIME
    response =  jsonify({
        "status": "ok", 
        "uptime": uptime,
    })
    return apply_mode_header(response)

@app.route("/chaos", methods=["POST"])
def chaos():
    """
    Endpoint to set chaos mode. Accepts JSON body with 'mode', 'duration', and 'rate'.
    """
    if MODE != "canary":
        return jsonify({"error": "Chaos mode can only be set in canary mode"}), 400
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Invalid JSON body",
        }), 400
    mode = data.get("mode", "None")
    duration = data.get("duration")
    rate = data.get("rate")

    if mode not in ["slow", "error", "recover"]:
        return jsonify({
            "error": "Invalid mode",
        }), 403
    if mode == "slow":
        if not isinstance(duration, (int, float)) or duration <= 0:
            return jsonify({
                "error": "Invalid duration for slow mode"}), 400
        chaos_state["mode"] = mode
        chaos_state["duration"] = duration
        chaos_state["rate"] = None
        message = f"Chaos mode set to SLOW with duration {duration} seconds"

    elif mode == "error":
        if not isinstance(rate, (int, float)) or not (0 < rate <= 1):
            return jsonify({
                "error": "Invalid rate for error mode"}), 400
        chaos_state["mode"] = mode
        chaos_state["duration"] = None
        chaos_state["rate"] = rate
        message = f"Chaos mode set to ERROR with error rate {rate*100}%"
    
    elif mode == "recover":
        chaos_state["mode"] = None
        chaos_state["duration"] = None
        chaos_state["rate"] = None
        message = "Chaos mode cancelled and reset: recovering service to stable state"
    
    response = jsonify({
        "message": message,
        "chaos": {
            "mode": chaos_state["mode"],
            "duration": chaos_state["duration"],
            "rate": chaos_state["rate"],
        }
    })
    return apply_mode_header(response)

    

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)