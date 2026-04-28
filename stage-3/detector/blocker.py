import subprocess
import time
import threading

from unbanner import Unbanner



class Blocker:
    """
    Manages blocking of IPs using iptables.
    Maintains a set of currently blocked IPs and provides methods to block/unblock.
    """
    def __init__(self, config, audit_logger, notifier):
        self.schedule = config["unban_schedule"]
        self.audit = audit_logger
        self.notifier = notifier

        # key: ip, value: {banned_at, level, duration}
        self.banned_ips = {}
        self.lock = threading.Lock()

        # self.unbanner = Unbanner(self.banned_ips, self.lock, config, audit_logger, notifier)

    def block_ip(self, ip, condition, rate, baseline):
        """
        Bans an IP by adding an iptables DROP rule.
        Skips if already banned.
        """
        duration = 0
        with self.lock:
            if ip not in self.banned_ips:
                # What level (count) is this IP at ?
                level = self.banned_ips.get(ip, {}).get('level', 0)
                # get the set duration for IP current level 
                duration = self.schedule[min(level, len(self.schedule) - 1)]

                subprocess.run([
                    "sudo", "iptables", "-A", "INPUT", "-s", ip, "-j", "DROP"
                ])

                self.banned_ips[ip] = {
                    'banned_at': time.time(),
                    'level': level, 
                    'duration': duration,
                }

                print(f"Blocked IP: {ip}")

                # Log and alert
                self.audit.log('BAN', ip, condition, rate, baseline, duration)
                self.notifier.send_ban(ip, condition, rate, baseline, duration)