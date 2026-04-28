import time
import json
from collections import deque


def tail_log(path):
    """
    Generator function to read a log file in real-time.
    """

    with open(path, "r") as file:
        # Move the cursor to the end of the file
        file.seek(0, 2)

        while True:
            line = file.readline()
            if not line:
                time.sleep(0.05)  # Sleep briefly to avoid busy waiting
                continue
            line = line.strip()
            if line: 
                try:
                    # Attempt to parse the line as JSON
                    data = json.loads(line)
                    yield data
                except json.JSONDecodeError:
                    # If the line is not valid JSON, skip it
                    continue



class SlidingWindow:
    """
    Tracks request timestamps for the last 60 seconds.
    One instance per IP, one instance for global traffic.
    """

    def __init__(self, window_seconds=60):
        self.window_seconds = window_seconds
        self.timestamps = deque()

    def _remove_old_entries(self, timestamp):
        """Removes timestamps that are older than the window."""
        cutoff = timestamp - self.window_seconds
        while self.timestamps and self.timestamps[0] < cutoff:
            self.timestamps.popleft()

    def add(self, timestamp):
        """Adds a new request timestamp and removes old entries."""
        self.timestamps.append(timestamp)
        self._remove_old_entries(timestamp)

    def count(self):
        """Returns the count of requests in the current window."""
        return len(self.timestamps)
    
    def rate(self):
        """Returns the average requests per second over the window."""
        return self.count() / self.window_seconds

    def count_last_n_seconds(self, n=1):
        """Returns the number of requests that arrived in the last n seconds."""
        cutoff = time.time() - n
        return sum(1 for ts in self.timestamps if ts >= cutoff)