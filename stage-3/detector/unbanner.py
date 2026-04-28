import time
import threading
import subprocess

class Unbanner:
    """
    Manages unbanning of IPs based on the configured schedule.
    Runs a background thread that periodically checks for IPs that are due for unbanning and removes the corresponding iptables rules.
    Logs and notifies on unban actions.
    """
    def __init__(self, banned_ips, lock, config, audit_logger, notifier):
        self.banned_ips = banned_ips
        self.lock = lock
        self.schedule = config["unban_schedule"]
        self.audit = audit_logger
        self.notifier = notifier

        threading.Thread(target=self._unban_loop, daemon=True).start()

    def _unban_loop(self):
        """
        Background loop that checks for IPs to unban every 30 seconds.
        """
        while True:
            time.sleep(30)  # Check every 30 seconds
            self._check_unbans()

    def _check_unbans(self):
        """
        Checks if any banned IPs are due for unbanning and removes the iptables rule.
        """
        now = time.time()
        with self.lock:
            banned_items = list(self.banned_ips.items())
            
        for ip, info in banned_items:
            if info["duration"] == "permanent":
                continue  # Skip permanent bans
            ban_elapsed_minutes = (now - info['banned_at']) / 60
            if  ban_elapsed_minutes >= info['duration']:
                self._unban(ip, info)

    def _unban(self, ip, info):
        """
        Unbans an IP by removing the iptables rule and logging the unban action.
        """
        subprocess.run([
            "iptables", "-D", "INPUT", "-s", ip, "-j", "DROP"
        ])
        next_level = info['level'] + 1
        next_duration = self.schedule[min(next_level, len(self.schedule) - 1)]
        with self.lock:
            del self.banned_ips[ip]
            print(f"Unblocked IP: {ip}")

        # Log and alert
        self.audit.log('UNBAN', ip, '', 0, 0, next_duration)
        self.notifier.send_unban(ip, info['duration'], next_duration)
