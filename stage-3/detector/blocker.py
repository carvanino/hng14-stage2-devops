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
        Skips if already actively banned.
        Preserves ban level from previous offences.
        """
        with self.lock:
            current = self.banned_ips.get(ip, {})

            # Skip if already actively banned
            if current.get('active', False):
                return

            # Level carries over from previous bans — escalation is preserved
            level = current.get('level', 0)
            duration = self.schedule[min(level, len(self.schedule) - 1)]

            subprocess.run([
                "iptables", "-A", "INPUT", "-s", ip, "-j", "DROP"
            ])

            self.banned_ips[ip] = {
                'banned_at': time.time(),
                'level': level,
                'duration': duration,
                'active': True
            }

            print(f"Blocked IP: {ip}")

            # Log and alert
            self.audit.log('BAN', ip, condition, rate, baseline, duration)
            self.notifier.send_ban(ip, condition, rate, baseline, duration)