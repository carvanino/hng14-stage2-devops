import time
import threading
from collections import defaultdict
from monitor import SlidingWindow

"""global_window = SlidingWindow()
ip_windows = {}

def record(entry):
    # Records a new log entry and updates the sliding windows
    timestamp = entry['timestamp']
    source_ip = entry['source_ip']

    # Update global window
    global_window.add(timestamp)

    # Update IP-specific window
    if source_ip not in ip_windows:
        ip_windows[source_ip] = SlidingWindow()
    ip_windows[source_ip].add(timestamp)

    print(global_window.rate())
    print(ip_windows[source_ip].rate())"""



class AnamolyDetector:
    """
    Maintains a rolling window of request counts and calculates an effective baseline.
    Uses a global window for overall traffic and hourly slots to capture time-of-day patterns.
    Recalculates the baseline every minute based on the current window.
    Flags anomalies based on deviations from the effective mean and stddev.
    """
    def __init__(self, baseline, config):
        self.baseline = baseline
        self.config = config

        # Sliding windows per-IP traffic
        self.per_ip = defaultdict(lambda: SlidingWindow())

        # Sliding window for global traffic
        self.global_window = SlidingWindow()

        # One error-rate window per IP
        self.ip_errors = defaultdict(lambda: SlidingWindow())

        self.lock = threading.Lock()

    def record(self, entry):
        """
        Records a new log entry, updates the sliding windows, and checks for anomalies.
        Called for each new log entry.
        """
        ip = entry['source_ip']
        timestamp = time.time()
        status = int(entry['status'])

        with self.lock:
            # Update sliding windows
            self.global_window.add(timestamp)
            self.per_ip[ip].add(timestamp)

            if status >= 400:
                self.ip_errors[ip].add(timestamp)
        
        return self._check(ip)
    
    def _check(self, ip):
        """
        Checks if the current request from the given IP is anomalous based on the baseline.
        Returns a list of alerts if anomalies are detected.
        """
        alerts = []

        with self.lock:
            # Check global traffic rate
            global_rate = self.global_window.rate()
            # Check IP-specific traffic rate
            ip_rate = self.per_ip[ip].rate()
            # Check IP-specific error rate
            ip_error_rate = self.ip_errors[ip].rate()

        mean = self.baseline.effective_mean
        stddev = self.baseline.effective_stddev
        z_thresh = self.config['thresholds']['z_score']          # 3.0
        multiplier = self.config['thresholds']['rate_multiplier']       # 5.0
        error_multiplier = self.config['thresholds']['error_rate_multiplier']  # 3.0

        baseline_error_rate = max(mean * self.config['error_rate_baseline_multiplier'], 0.1)  # 0.01
        if ip_error_rate > error_multiplier * baseline_error_rate:
            z_thresh = z_thresh * 0.7  # Lower threshold for high error rates

        ip_z_score = self.baseline.z_score(ip_rate)
        if ip_z_score > z_thresh or ip_rate > multiplier * mean:
            alerts.append({
                'type': 'ip',
                'ip': ip,
                'rate': ip_rate,
                'z_score': ip_z_score,
                'condition': 'z-score' if ip_z_score > z_thresh else 'rate multiplier'
            })

        global_z_score = self.baseline.z_score(global_rate)
        if global_z_score > z_thresh or global_rate > multiplier * mean:
            alerts.append({
                'type': 'global',
                'rate': global_rate,
                'z_score': global_z_score,
                'condition': 'z-score' if global_z_score > z_thresh else 'rate multiplier'
            })

        return alerts