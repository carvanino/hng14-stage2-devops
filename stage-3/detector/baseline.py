import math
import time
import threading
from collections import deque



class BaselineEngine:
    """
    Baseline detection engine that tracks request rates and identifies anomalies.
    """

    def __init__(self, window_minutes=30, recalc_intervals=60):
        # 30 minutes worth of per-second counts
        self.window_seconds = window_minutes * 60
        self.recalc_intervals = recalc_intervals

        # Rolling window — stores (timestamp, count) pairs
        self.global_window = deque()

        # Separate bucket for each hour
        # key: hour number (0-23), value: list of per-second counts
        self.hourly_slots = {}

        self.effective_mean = 1.0
        self.effective_stddev = 0.5

        # self.ip_windows = {}
        self.last_recalc = time.time()
        self.lock = threading.Lock()

    def _remove_old_entries(self, timestamp):
        """Removes entries from the global window that are older than the window size."""
        cutoff = timestamp - self.window_seconds
        while self.global_window and self.global_window[0][0] < cutoff:
            self.global_window.popleft()
            # old_timestamp, old_count = 
            # old_hour = int((old_timestamp / 3600) % 24)
            # if old_hour in self.hourly_slots:
            #     if old_count in self.hourly_slots[old_hour]:
            #         self.hourly_slots[old_hour].remove(old_count)

    def record(self, count):
        """
        Records a new request count for the current second and updates the baseline.
        Called every second with the current req/s count.
        Adds to the rolling window and triggers recalculation if due.
        """
        timestamp = time.time()
        hour = int((timestamp / 3600) % 24) # Hour of the day (0-23)

        with self.lock:
            self.global_window.append((timestamp, count))
            if hour not in self.hourly_slots:
                self.hourly_slots[hour] = []
            self.hourly_slots[hour].append(count)

            # Remove entries older than 30 minutes
            self._remove_old_entries(timestamp)
        
        # Recalculate every 60 seconds
        if timestamp - self.last_recalc >= self.recalc_intervals:
            self._recalculate_baseline(timestamp)
            # self.last_recalc = timestamp


    def _recalculate_baseline(self, timestamp):
        """Recalculates the effective mean and stddev based on the current window.
        Prefers current hour's data if it has enough points.
        Falls back to full 30-minute window otherwise.
        """
        with self.lock:
            current_hour = int(timestamp // 3600) % 24
            hourly_counts = self.hourly_slots.get(current_hour, [])

            # Prefer hourly data if we have at least 5 minutes of it
            if len(hourly_counts) >= 300:
                counts = hourly_counts
            else: 
                counts = [c for _, c in self.global_window]

            if len(counts) < 2:
                return

            mean = sum(counts) / len(counts)
            variance = sum((x - mean) ** 2 for x in counts) / len(counts)
            stddev = math.sqrt(variance)

            # Apply floors — never let these hit zero
            self.effective_mean = max(mean, 1.0)
            self.effective_stddev = max(stddev, 0.5)
            self.last_recalc = timestamp

    
    def z_score(self, rate):
        """Calculates the z-score for a given request rate."""
        return (rate - self.effective_mean) / self.effective_stddev