import requests
import datetime


class Notifier:
    """
    Handles sending notifications when an IP is blocked.
    """

    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def _send(self, message):
        """
        Sends a message to the configured webhook URL.
        """
        payload = {
            "text": message
        }
        try:
            requests.post(self.webhook_url, json=payload)
        except Exception as e:
            print(f"Failed to send notification: {e}")

    def _now(self):
        """Returns the current UTC time as a formatted string."""
        return datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    
    def send_ban(self, ip, condition, rate, baseline, duration):
        message = (
            f"🚨 *IP BANNED*\n"
            f"IP: `{ip}`\n"
            f"Condition: {condition}\n"
            f"Current rate: {rate:.2f} req/s\n"
            f"Baseline mean: {baseline:.2f} req/s\n"
            f"Ban duration: {duration} minutes\n"
            f"Timestamp: {self._now()}"
        )
        self._send(message)

    def send_unban(self, ip, previous_duration, next_duration):
        message = (
            f"✅ *IP UNBANNED*\n"
            f"IP: `{ip}`\n"
            f"Served: {previous_duration} minutes\n"
            f"Next ban if reoffends: {next_duration}\n"
            f"Timestamp: {self._now()}"
        )
        self._send(message)

    def send_global_alert(self, rate, baseline):
        message = (
            f"⚠️ *GLOBAL TRAFFIC ANOMALY*\n"
            f"Current rate: {rate:.2f} req/s\n"
            f"Baseline mean: {baseline:.2f} req/s\n"
            f"Timestamp: {self._now()}"
        )
        self._send(message)

    def send_baseline_recalc(self, mean, stddev):
        message = (
            f"📊 *BASELINE RECALCULATED*\n"
            f"New mean: {mean:.2f} req/s\n"
            f"New stddev: {stddev:.2f}\n"
            f"Timestamp: {self._now()}"
        )
        self._send(message)