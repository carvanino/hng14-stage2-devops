import time
import threading
import psutil
from flask import Flask, jsonify, render_template_string

# We'll define the HTML template below
from dashboard_template import HTML_TEMPLATE


class Dashboard:

    def __init__(self, blocker, detector, baseline, start_time):
        self.blocker = blocker
        self.detector = detector
        self.baseline = baseline
        self.start_time = start_time
        self.app = Flask(__name__)
        self._register_routes()

    def _register_routes(self):

        @self.app.route('/')
        def index():
            return render_template_string(HTML_TEMPLATE)

        @self.app.route('/metrics')
        def metrics():
            return jsonify(self._collect_metrics())

    def _collect_metrics(self):
        # Uptime in seconds
        uptime_seconds = int(time.time() - self.start_time)

        # Banned IPs with their info
        with self.blocker.lock:
            banned = {
                ip: {
                    'duration': info['duration'],
                    'banned_at': info['banned_at'],
                    'level': info['level'],
                    # how many seconds remaining
                    'remaining': (
                        'permanent' if info['duration'] == 'permanent'
                        else max(0, info['duration'] * 60 - (time.time() - info['banned_at']))
                    )
                }
                for ip, info in self.blocker.banned_ips.items()
            }

        # Top 10 source IPs by request count
        with self.detector.lock:
            top_ips = sorted(
                [
                    {'ip': ip, 'rate': window.rate()}
                    for ip, window in self.detector.per_ip.items()
                ],
                key=lambda x: x['rate'],
                reverse=True
            )[:10]

            global_rate = self.detector.global_window.rate()

        return {
            'uptime': uptime_seconds,
            'uptime_human': self._format_uptime(uptime_seconds),
            'global_rate': round(global_rate, 2),
            'top_ips': top_ips,
            'banned_ips': banned,
            'banned_count': len(banned),
            'baseline_mean': round(self.baseline.effective_mean, 2),
            'baseline_stddev': round(self.baseline.effective_stddev, 2),
            'cpu_percent': psutil.cpu_percent(interval=None),
            'memory_percent': psutil.virtual_memory().percent,
        }

    def _format_uptime(self, seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours}h {minutes}m {secs}s"

    def run(self, port=8080):
        # Runs Flask in a background thread
        threading.Thread(
            target=lambda: self.app.run(host='0.0.0.0', port=port),
            daemon=True
        ).start()